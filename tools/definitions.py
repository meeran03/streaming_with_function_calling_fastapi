"""
    This file contains json-schemas for the tools

"""

GET_WEATHER_INFORMATION = {
    "type": "function",
    "function": {
        "name": "get_weather_information",
        "description": "Gets the weather information for a given latitude and longitude",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "The latitude of the location",
                },
                "longitude": {
                    "type": "number",
                    "description": "The longitude of the location",
                },
            },
            "required": ["latitude", "longitude"],
        },
    },
}
