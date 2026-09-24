from fastapi import FastAPI
from api.router import api_router

app = FastAPI(title="Responses Streaming + Tool Calling", version="2.0.0")
app.include_router(api_router)
