"""A local fixture; this sample deliberately does not contact a weather service."""

import math


async def get_weather_information(latitude: float, longitude: float) -> dict:
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in (latitude, longitude)
    ):
        raise ValueError("coordinates must be finite numbers")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("coordinates are out of range")
    return {
        "source": "fictional demo fixture, not live weather",
        "temperature_c": 21,
        "conditions": "clear",
        "latitude": latitude,
        "longitude": longitude,
    }
