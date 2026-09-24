GET_WEATHER_INFORMATION = {
    "type": "function",
    "name": "get_weather_information",
    "description": "Return a fictional weather fixture for demonstrating tool calling. Never present it as live weather.",
    "parameters": {
        "type": "object",
        "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"}},
        "required": ["latitude", "longitude"],
        "additionalProperties": False,
    },
    "strict": True,
}
