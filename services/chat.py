"""Responses API tool loop with bounded sessions and explicit stream outcomes."""

from __future__ import annotations
import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from openai import AsyncOpenAI
from config.main import config
from tools.definitions import GET_WEATHER_INFORMATION
from tools.get_weather import get_weather_information
from services.demo import DemoClient

INSTRUCTIONS = "Help with activity suggestions. Weather results in this demo are fictional fixtures: say so clearly. Use the weather tool when useful, and never claim it is a live forecast."


@dataclass
class Conversation:
    turns: deque = field(default_factory=lambda: deque(maxlen=8))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    touched: float = field(default_factory=time.monotonic)


class ChatService:
    def __init__(
        self, client=None, model=None, max_sessions=64, timeout=45, max_rounds=4
    ):
        if max_sessions < 1 or timeout <= 0 or max_rounds < 1:
            raise ValueError("limits must be positive")
        self.client = client
        self.model = model or config.OPENAI_MODEL
        self.max_sessions, self.timeout, self.max_rounds = (
            max_sessions,
            timeout,
            max_rounds,
        )
        self.sessions: dict[str, Conversation] = {}

    def get_client(self):
        if self.client is None:
            self.client = (
                DemoClient()
                if config.DEMO_MODE
                else AsyncOpenAI(
                    api_key=config.OPENAI_API_KEY, timeout=30, max_retries=0
                )
            )
        return self.client

    def conversation(self, chat_id):
        now = time.monotonic()
        for key, session in list(self.sessions.items()):
            if not session.lock.locked() and now - session.touched > 3600:
                del self.sessions[key]
        if chat_id not in self.sessions:
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("session capacity reached")
            self.sessions[chat_id] = Conversation()
        return self.sessions[chat_id]

    async def execute(self, call, cache):
        signature = (call.name, call.arguments)
        if call.call_id in cache:
            previous, output = cache[call.call_id]
            if previous != signature:
                raise RuntimeError("conflicting duplicate tool call")
            return output
        try:
            if call.name != "get_weather_information":
                raise ValueError("unknown tool")
            args = json.loads(call.arguments)
            if not isinstance(args, dict) or set(args) != {"latitude", "longitude"}:
                raise ValueError("invalid arguments")
            output = json.dumps(
                await asyncio.wait_for(get_weather_information(**args), timeout=5)
            )
        except (ValueError, TypeError):
            output = json.dumps(
                {
                    "error": "Invalid tool or coordinates. Supply latitude and longitude as finite numbers."
                }
            )
        cache[call.call_id] = (signature, output)
        return output

    async def generate(self, chat_id, content):
        try:
            conversation = self.conversation(chat_id)
            if conversation.lock.locked():
                yield {
                    "event": "error",
                    "message": "This conversation already has a response in progress.",
                }
                return
            async with conversation.lock:
                conversation.touched = time.monotonic()
                previous = [item for turn in conversation.turns for item in turn]
                turn: list[dict[str, Any]] = [{"role": "user", "content": content}]
                cache = {}
                async with asyncio.timeout(self.timeout):
                    for _ in range(self.max_rounds):
                        completed = None
                        stream = await self.get_client().responses.create(
                            model=self.model,
                            instructions=INSTRUCTIONS,
                            input=previous + turn,
                            tools=[GET_WEATHER_INFORMATION],
                            stream=True,
                            store=False,
                            include=["reasoning.encrypted_content"],
                            max_output_tokens=1000,
                        )
                        try:
                            async for event in stream:
                                if event.type == "response.output_text.delta":
                                    yield {"event": "delta", "text": event.delta}
                                elif event.type == "response.completed":
                                    completed = event.response
                                elif event.type in {
                                    "response.failed",
                                    "response.incomplete",
                                    "error",
                                }:
                                    raise RuntimeError(
                                        "upstream response did not complete"
                                    )
                        finally:
                            await stream.close()
                        if completed is None or completed.status != "completed":
                            raise RuntimeError(
                                "stream ended without a completed response"
                            )
                        turn.extend(
                            item.model_dump(mode="json", exclude_none=True)
                            for item in completed.output
                        )
                        calls = [
                            item
                            for item in completed.output
                            if item.type == "function_call"
                        ]
                        if not calls:
                            conversation.turns.append(turn)
                            conversation.touched = time.monotonic()
                            yield {"event": "done"}
                            return
                        if len(calls) > 8:
                            raise RuntimeError("too many tool calls")
                        for call in calls:
                            output = await self.execute(call, cache)
                            turn.append(
                                {
                                    "type": "function_call_output",
                                    "call_id": call.call_id,
                                    "output": output,
                                }
                            )
                            yield {"event": "tool", "name": call.name}
                    raise RuntimeError("tool round limit exceeded")
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            yield {
                "event": "error",
                "message": "Response deadline exceeded. Any text already displayed is incomplete.",
            }
        except Exception:
            yield {
                "event": "error",
                "message": "Response failed. Any text already displayed is incomplete. Check configuration or retry.",
            }
