import json


async def stream_generator(events):
    async for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
