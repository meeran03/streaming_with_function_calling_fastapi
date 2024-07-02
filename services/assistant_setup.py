"""
    This class handles updates/creation of the 
    OpenAI Assistant for the chatbot
"""
from openai import AsyncOpenAI as OpenAI
from config.main import config

class AssistantSetup:
    """
    This class handles updates/creation of the
    OpenAI Assistant for the chatbot
    """
    def __init__(self, client: OpenAI, assistant_id, sys_prompt, name, tools):
        self.client = client
        self.assistant_id = assistant_id
        self.tools = tools
        self.sys_prompt = sys_prompt
        self.name = name
        self.model = config.OPENAI_MODEL

    async def create_or_update_assistant(self):
        """
        This function creates or updates the assistant
        """
        assistant_id = self.assistant_id
        if assistant_id:
            assistant = await self.update_existing_assistant(assistant_id)
        else:
            assistant = await self.create_new_assistant()
        return assistant

    async def update_existing_assistant(self, assistant_id):
        """
        This function updates the existing assistant
        with the new properties
        """
        try:
            assistant = await self.client.beta.assistants.retrieve(assistant_id)
            await self.update_assistant_properties(assistant)
        except Exception as e: # pylint: disable=broad-except
            print(f"Error updating assistant: {e}")
            assistant = await self.create_new_assistant()
        return assistant

    async def create_new_assistant(self):
        """
        This function creates a new assistant
        """
        try:
            model = self.model
            assistant = await self.client.beta.assistants.create(
                name=self.name,
                instructions=self.sys_prompt,
                model=model,
                tools=self.tools,
                temperature=self.get_temperature(),
            )
            print("Assistant created successfully!", assistant.id)
        except Exception as e: # pylint: disable=broad-except
            print(f"Error creating assistant: {e}")
            assistant = None
        return assistant

    def get_temperature(self):
        """
        This function returns the temperature depending on the assistant
        """
        return 0.5

    async def update_assistant_properties(self, assistant):
        """
        This function updates the assistant properties
        """
        try:
            assistant = await self.client.beta.assistants.update(
                assistant.id,
                instructions=self.sys_prompt,
                tools=self.tools,
                temperature=self.get_temperature(),
            )
        except Exception as e: # pylint: disable=broad-except
            print(f"Error updating assistant: {e}")
        return assistant
