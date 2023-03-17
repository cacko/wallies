from fastapi import FastAPI
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from app.config import app_config
import uvicorn


def create_app():
    app = FastAPI()

    origins = [
        "http://localhost:4200",
        "https://wallies.cacko.net"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api.router)
    return app


def serve():
    server_config = uvicorn.Config(
        app=create_app,
        host=app_config.api.host,
        port=app_config.api.port,
        workers=app_config.api.workers,
        factory=True
    )
    server = uvicorn.Server(server_config)
    server.run()
