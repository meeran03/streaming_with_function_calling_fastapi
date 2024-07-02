"""
Stream related utilities.
"""

async def stream_generator(data):
    """
    Generator function to simulate streaming data.
    """
    async for message in data:
        json_data = message
        if hasattr(message, 'model_dump_json'):
            json_data = message.model_dump_json()
        if isinstance(json_data, str) and json_data.startswith('data:'):
            yield json_data
        else:
            yield f"data: {json_data}\n\n"
