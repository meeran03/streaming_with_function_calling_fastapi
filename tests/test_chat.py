import asyncio
import json
import unittest
from types import SimpleNamespace as NS
from services.chat import ChatService
from services.demo import DemoClient, Stream, Item
from tools.get_weather import get_weather_information
from utils.stream import stream_generator


async def collect(generator):
    return [item async for item in generator]


class ChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_tool_loop_and_history(self):
        service = ChatService(client=DemoClient())
        events = await collect(service.generate("one", "hello"))
        self.assertEqual(events[-1], {"event": "done"})
        self.assertTrue(any(e["event"] == "tool" for e in events))
        self.assertIn("fictional", "".join(e.get("text", "") for e in events))
        turn = service.sessions["one"].turns[0]
        self.assertTrue(any(e.get("type") == "function_call_output" for e in turn))
        self.assertNotIn("two", service.sessions)

    async def test_missing_completed_event_does_not_commit(self):
        stream = Stream([NS(type="response.output_text.delta", delta="partial")])

        class Responses:
            async def create(self, **kwargs):
                return stream

        service = ChatService(client=NS(responses=Responses()))
        events = await collect(service.generate("id", "hi"))
        self.assertEqual(events[-1]["event"], "error")
        self.assertFalse(service.sessions["id"].turns)
        self.assertTrue(stream.closed)

    async def test_tool_round_limit(self):
        class Responses:
            async def create(self, **kwargs):
                return Stream(
                    [
                        NS(
                            type="response.completed",
                            response=NS(
                                status="completed",
                                output=[
                                    Item(
                                        type="function_call",
                                        call_id="id",
                                        name="unknown",
                                        arguments="{}",
                                    )
                                ],
                            ),
                        )
                    ]
                )

        service = ChatService(client=NS(responses=Responses()), max_rounds=2)
        events = await collect(service.generate("id", "hi"))
        self.assertEqual(events[-1]["event"], "error")
        self.assertFalse(service.sessions["id"].turns)

    async def test_timeout_and_cancellation_release_session(self):
        entered = asyncio.Event()

        class Responses:
            async def create(self, **kwargs):
                entered.set()
                await asyncio.sleep(60)

        s = ChatService(client=NS(responses=Responses()), timeout=0.01)
        result = await collect(s.generate("id", "hi"))
        self.assertIn("deadline", result[-1]["message"])
        s.timeout = 60
        entered.clear()
        task = asyncio.create_task(collect(s.generate("id", "again")))
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(s.sessions["id"].lock.locked())
        self.assertFalse(s.sessions["id"].turns)

    async def test_same_session_overlap_is_rejected(self):
        entered = asyncio.Event()

        class Responses:
            async def create(self, **kwargs):
                entered.set()
                await asyncio.sleep(60)

        s = ChatService(client=NS(responses=Responses()))
        task = asyncio.create_task(collect(s.generate("same", "first")))
        await entered.wait()
        result = await collect(s.generate("same", "second"))
        self.assertIn("in progress", result[0]["message"])
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_tool_validation_and_duplicate_identity(self):
        s = ChatService(client=DemoClient())
        cache = {}
        call = Item(
            call_id="id",
            name="get_weather_information",
            arguments='{"latitude":38.9,"longitude":-77}',
        )
        first = await s.execute(call, cache)
        self.assertEqual(first, await s.execute(call, cache))
        call.arguments = "{}"
        with self.assertRaises(RuntimeError):
            await s.execute(call, cache)
        self.assertIn("error", json.loads(await s.execute(call, {})))
        for lat, lon in [(float("nan"), 1), (True, 1), (91, 0), (0, 181)]:
            with self.assertRaises(ValueError):
                await get_weather_information(lat, lon)

    async def test_session_capacity_and_history_bound(self):
        s = ChatService(client=DemoClient(), max_sessions=1)
        for _ in range(10):
            await collect(s.generate("one", "hi"))
        self.assertEqual(len(s.sessions["one"].turns), 8)
        self.assertEqual((await collect(s.generate("two", "hi")))[-1]["event"], "error")

    async def test_sse_newlines_and_unicode_are_encoded(self):
        async def events():
            yield {"event": "delta", "text": "hello\n🌍"}

        frames = await collect(stream_generator(events()))
        self.assertEqual(
            json.loads(frames[0][6:]), {"event": "delta", "text": "hello\n🌍"}
        )


class ApiTests(unittest.TestCase):
    def test_local_flow_and_request_validation(self):
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            r = client.post("/chat/demo", json={"user_query": "Hi"})
            self.assertEqual(r.status_code, 200)
            self.assertIn("text/event-stream", r.headers["content-type"])
            self.assertIn('"event": "done"', r.text)
            self.assertEqual(
                client.post("/chat/demo", json={"user_query": ""}).status_code, 422
            )
            self.assertEqual(client.get("/").status_code, 200)
