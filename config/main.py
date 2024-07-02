"""
    This file contains all project configs read from env file.
"""

import os

class Base(object):
    """
    Base configuration class. Contains all the default configurations.
    """

    DEBUG: bool = True

class Config(Base):
    """
    Main configuration class. Contains all the configurations for the project.
    """

    DEBUG: bool = True
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID: str = os.getenv("ASSISTANT_ID")
    OPENAI_MODEL: str = "gpt-4o"
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY")


config = Config()
