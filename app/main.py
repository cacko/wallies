from fastapi import FastAPI
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from app.config import app_config
import uvicorn
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.scheduler import Scheduler

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def create_app():
    app = FastAPI()

    origins = [
        "http://localhost:4200",
        "https://wallies.cacko.net"
    ]

    assets_path = Path(app_config.api.assets)
    if not assets_path.exists():
        assets_path.mkdir(parents=True, exist_ok=True)

    app.mount(
        "/api/assets",
        StaticFiles(directory=assets_path.as_posix()),
        name="assets"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["x-user-token"],
    )

    app.include_router(api.router)
    return app


def serve():
    server_config = uvicorn.Config(
        app=create_app,
        host=app_config.api.host,
        port=app_config.api.port,
        workers=app_config.api.workers,
        reload=True,
        factory=True
    )
    Scheduler.start()
    server = uvicorn.Server(server_config)
    server.run()
