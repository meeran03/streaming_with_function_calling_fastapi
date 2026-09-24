# Streaming tool calls with FastAPI

A small, inspectable example of the **OpenAI Responses API → validated tool execution → streamed browser response** loop. Includes a deterministic local mode, so you can run the complete flow without an account, API key, or paid request.

Originally published in 2024; refreshed in September 2026. The [original article](https://medium.com/@meeran2003/async-streaming-openai-assistant-api-with-function-calling-in-fastapi-0dfe5935f238) describes the earlier Assistants API implementation. The current code uses Responses.

## Run in five minutes

Requires Python **3.13+**. From the repository root:

```bash
git clone https://github.com/meeran03/streaming_with_function_calling_fastapi.git
cd streaming_with_function_calling_fastapi
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**, send a message, and watch the tool event and incremental text. `DEMO_MODE=1` is the default. The local provider intentionally follows a fixed weather-tool scenario; it is not a language model. The weather tool returns a **fictional fixture**, including in live model mode.

## What to inspect

```text
Browser POST /chat/{chat_id}
  → bounded, per-conversation session
  → Responses stream
  → completed function-call arguments validated
  → local tool result returned to model
  → JSON server-sent events: delta / tool / done / error
```

- [Tool loop](services/chat.py): four-round limit, 45-second response deadline, at most eight tool calls per round, and duplicate-call conflict detection.
- [Session handling](services/chat.py): at most 64 in-memory conversations, one active response per conversation, eight complete turns of history, and one-hour idle expiry.
- [SSE encoding](utils/stream.py) and [browser reader](templates/index.html): JSON framing, incremental UTF-8 decoding, cancellation, and explicit incomplete-response errors.
- [Tool validation](tools/get_weather.py): finite coordinates and latitude/longitude bounds. No arbitrary function dispatch.
- [Tests](tests/test_chat.py): successful tool round trips, premature stream termination, cancellation, deadlines, concurrency, bounds, and the HTTP interface.

Only completed turns enter conversation history. On a failed stream, text already shown in the browser is explicitly marked incomplete. This is a useful boundary when integrating a model with a streaming UI.

## Optional live model mode

Set these values in your untracked `.env`:

```dotenv
DEMO_MODE=0
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o
```

Restart the server. You can choose another compatible Responses model available to your account. Live requests use your provider account and may incur charges. `store=False` disables Responses application-state storage; it is not a claim of zero provider retention. See [OpenAI's function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

The automated suite uses a deterministic provider. It does **not** prove live model quality or provider availability.

## Validate

```bash
python -m unittest discover -s tests -v
```

## Boundaries

This is a local teaching example, not a hosted multi-tenant service. Conversation IDs are not authentication. State and duplicate-call tracking are process-local and disappear on restart. Before exposing it, add authentication, tenant isolation, request limits, durable storage, provider observability, and a policy for sensitive tool output. The fixture has no external side effect; production side-effecting tools need durable idempotency and reconciliation.

Built by [Muhammad Meeran](https://meeran.dev). For session lifecycle failure scenarios, see [Voice Session Lab](https://github.com/meeran03/voice-session-lab).
