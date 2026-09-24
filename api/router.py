from fastapi import APIRouter, Request, Path
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from services.chat import ChatService
from utils.stream import stream_generator

api_router = APIRouter()
chat_service = ChatService()
templates = Jinja2Templates(directory="templates")


class GetChatResponseRequest(BaseModel):
    user_query: str = Field(min_length=1, max_length=2000)


@api_router.get("/ping")
def ping():
    return {"status": "ok"}


@api_router.post("/chat/{chat_id}")
async def get_chat_response(
    data: GetChatResponseRequest,
    chat_id: str = Path(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
):
    return StreamingResponse(
        stream_generator(chat_service.generate(chat_id, data.user_query)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api_router.get("/")
def chat_frontend(request: Request):
    from config.main import config

    return templates.TemplateResponse(
        request=request, name="index.html", context={"demo_mode": config.DEMO_MODE}
    )
