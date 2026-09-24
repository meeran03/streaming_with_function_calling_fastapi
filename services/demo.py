"""Deterministic Responses-shaped events for running the entire local flow."""

import asyncio
from types import SimpleNamespace


class Item(SimpleNamespace):
    def model_dump(self, **kwargs):
        return vars(self)


class Stream:
    def __init__(self, events):
        self.events = events
        self.closed = False

    async def __aiter__(self):
        for event in self.events:
            await asyncio.sleep(0)
            yield event

    async def close(self):
        self.closed = True


class DemoResponses:
    async def create(self, **kwargs):
        items = kwargs["input"]
        if items[-1].get("type") != "function_call_output":
            item = Item(
                type="function_call",
                id="fc_demo",
                call_id="call_demo",
                name="get_weather_information",
                arguments='{"latitude":38.9,"longitude":-77.0}',
            )
            output, text = [item], []
        else:
            message = "Demo weather: 21°C and clear. This is a fictional fixture, not a live forecast."
            output = [
                Item(
                    type="message",
                    role="assistant",
                    content=[
                        {"type": "output_text", "text": message, "annotations": []}
                    ],
                )
            ]
            text = [
                SimpleNamespace(type="response.output_text.delta", delta=part)
                for part in [
                    "Demo weather: ",
                    "21°C and clear. ",
                    "This is a fictional fixture, not a live forecast.",
                ]
            ]
        return Stream(
            text
            + [
                SimpleNamespace(
                    type="response.completed",
                    response=SimpleNamespace(output=output, status="completed"),
                )
            ]
        )


class DemoClient:
    def __init__(self):
        self.responses = DemoResponses()
