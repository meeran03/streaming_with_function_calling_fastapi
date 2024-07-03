# OpenAI Assistant Streaming with Function Calling in FastAPI

This project showcases how you can use asynchronous streaming with OpenAI assistant and at the same time utilize function calling
in FastAPI.

You can read about it in detail in the following blog post: [OpenAI Assistant Streaming with Function Calling in FastAPI](https://medium.com/@meeran2003/async-streaming-openai-assistant-api-with-function-calling-in-fastapi-0dfe5935f238)

![OpenAI Assistant Streaming with Function Calling in FastAPI](./demo.png?raw=true "Demo")

## Description

This project demonstrates how you can use FastAPI to create a real-time chat interface that communicates with OpenAI's GPT models for automated responses. The application also supports function calling, allowing you to execute commands and retrieve information in real-time.

## Features

- Asynchronous streaming for real-time chat communication.
- Function calling for executing commands and retrieving information.
- Integration with OpenAI's GPT models for automated responses.
- Weather information retrieval using the OpenWeather API.
- Text to Speech and Speech to Text using web APIs.
- Chat interface for real-time communication.

## Getting Started

### Dependencies

- Python 3.8 or higher
- FastAPI
- OpenAI API
- aiohttp, httpx for asynchronous HTTP requests

Refer to `requirements.txt` for a complete list of dependencies.

### Installing

1. Clone the repository to your local machine.
2. Create a virtual environment:

```sh
python -m venv env
```

3. Activate the virtual environment:

- On Windows:

```sh
env\Scripts\activate
```

- On Unix or MacOS:

```sh
source env/bin/activate
```

4. Install the required packages:

```sh
pip install -r requirements.txt
```

### Configuration

- Copy `.env.development` to `.env` and adjust the configuration variables as needed.
- Ensure you have valid API keys for OpenAI and OpenWeather APIs set in your `.env` file.

### Running the Application

1. Start the application:

```sh
uvicorn main:app --reload
```

2. Visit `http://127.0.0.1:8000` in your web browser to access the chat interface.

## Usage

- Use the chat interface to communicate in real-time.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to suggest improvements or add new features.
