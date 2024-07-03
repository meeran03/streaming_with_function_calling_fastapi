"""
    This file contains the core functionality of the chat service.
"""

import os
import asyncio
import json

from openai import AsyncOpenAI as OpenAI
from openai.types.beta import Assistant, Thread
from openai.types.beta.assistant_stream_event import (
    ThreadRunRequiresAction,
    ThreadMessageDelta,
    ThreadRunFailed,
    ThreadRunCancelling,
    ThreadRunCancelled,
    ThreadRunExpired,
    ThreadRunStepFailed,
    ThreadRunStepCancelled,
)

from config.main import config
from config.prompts import SYS_PROMPT
from utils.singleton import Singleton
from services.assistant_setup import AssistantSetup
from tools.definitions import GET_WEATHER_INFORMATION
from tools.get_weather import get_weather_information

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY

class ChatService(metaclass=Singleton):
    """
    This class is used to handle the OpenAI GPT based assistant.
    """

    assistant: Assistant = None
    assistant_setup: AssistantSetup = None
    sys_prompt: str = SYS_PROMPT
    chat_to_thread_map = {}
    tools = []
    tool_instances = {}

    def __init__(self) -> None:
        self.client = OpenAI()
        self.name = 'Activity Suggester'
        self.assistant_id = config.ASSISTANT_ID
        self.init_tools()
        self.initialize()

    def initialize(self):
        """
        This function initializes the required services and objects.
        """
        self.assistant_setup = AssistantSetup(
            self.client,
            self.assistant_id,
            self.sys_prompt,
            self.name,
            self.tools,
        )

    async def create_assistant(self):
        """
        This function creates assistant if not exists
        """
        if not self.assistant:
            self.assistant = (  # pylint: disable=attribute-defined-outside-init
                await self.assistant_setup.create_or_update_assistant()
            )

    async def generate(self, chat_id, content):
        """
        It generates the response for the user query.
        """
        await self.create_assistant()
        thread = await self.create_or_get_thread(chat_id)
        await self.client.beta.threads.messages.create(
            thread.id,
            role="user",
            content=content,
        )
        stream = await self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=self.assistant.id, stream=True
        )
        async for event in stream:
            async for token in self.process_event(event, thread):
                yield token

        print("Tool run completed")

    async def create_or_get_thread(self, chat_id) -> Thread:
        """
        This function either creates a new thread for the chat_id or gets the existing thread.
        """
        thread = None
        if self.chat_to_thread_map.get(chat_id):
            try:
                thread = await self.client.beta.threads.retrieve(self.chat_to_thread_map[chat_id])
            except Exception as e:  # pylint: disable=bare-except, broad-except
                print("Error in getting thread", e)
                thread = None
        if not thread:
            thread = await self.client.beta.threads.create(
                metadata={
                    "chat_id": str(chat_id),
                },
            )
            self.chat_to_thread_map[chat_id] = thread.id
        return thread

    def create_tool_output(self, tool_call, tool_result):
        """
        This function creates the tool output.
        """
        output = {
            "tool_call_id": tool_call.id,
            "output": tool_result,
        }
        return output

    async def process_event(self, event, thread: Thread, **kwargs):
        """
        Process an event in the thread.

        Args:
            event: The event to be processed.
            thread: The thread object.
            **kwargs: Additional keyword arguments.

        Yields:
            The processed tokens.

        Raises:
            Exception: If the run fails.
        """
        if isinstance(event, ThreadMessageDelta):
            data = event.data.delta.content
            for d in data:
                yield d

        elif isinstance(event, ThreadRunRequiresAction):
            run_obj = event.data
            tool_outputs = await self.process_tool_calls(
                run_obj.required_action.submit_tool_outputs.tool_calls
            )
            tool_output_events = (
                await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run_obj.id,
                    tool_outputs=tool_outputs,
                    stream=True,
                )
            )
            async for tool_event in tool_output_events:
                async for token in self.process_event(
                    tool_event, thread=thread, **kwargs
                ):
                    yield token

        elif any(
            isinstance(event, cls)
            for cls in [
                ThreadRunFailed,
                ThreadRunCancelling,
                ThreadRunCancelled,
                ThreadRunExpired,
                ThreadRunStepFailed,
                ThreadRunStepCancelled,
            ]
        ):
            raise Exception("Run failed") # pylint: disable=broad-exception-raised

    def init_tools(self):
        """
        This function initializes the tools.
        """
        self.tools = [GET_WEATHER_INFORMATION]
        self.tool_instances = {
            "get_weather_information": get_weather_information,
        }

    async def process_tool_call(self, tool_call, tool_outputs: list, extra_args=None):
        """
        This function processes a single tool call.
        And also handles the exceptions.
        """
        result = None
        try:
            arguments = json.loads(tool_call.function.arguments)
            function_name = tool_call.function.name
            if extra_args:
                for key, value in extra_args.items():
                    arguments[key] = value
            if function_name not in self.tool_instances:
                result = "Tool not found"
            else:
                result = await self.tool_instances[function_name](**arguments)
        except Exception as e:  # pylint: disable=broad-except
            result = str(e)
            print(e)
        created_tool_output = self.create_tool_output(tool_call, result)
        tool_outputs.append(created_tool_output)

    async def process_tool_calls(self, tool_calls, extra_args = None):
        """
        This function processes all the tool calls.
        """
        tool_outputs = []
        coroutines = []
        total_calls = len(tool_calls)
        for i in range(total_calls):
            tool_call = tool_calls[i]
            coroutines.append(self.process_tool_call(tool_call, tool_outputs, extra_args))
        if coroutines:
            await asyncio.gather(*coroutines)
        return tool_outputs
