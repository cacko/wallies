from fastapi import FastAPI
from .routers import api
from fastapi.middleware.cors import CORSMiddleware
from app.config import app_config
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.scheduler import Scheduler
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve as hypercorn_serve

ASSETS_PATH = Path(__file__).parent.parent / "assets"


def create_app():
    app = FastAPI(
        title="wallies@cacko.net",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url="/api/redoc"
    )

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
        allow_headers=("x-user-token", "x-pagination-page",
                       "x-pagination-total"),
        expose_headers=["x-pagination-page",
                        "x-pagination-total",
                        'x-pagination-next']
    )

    app.include_router(api.router)
    return app


def serve():
    Scheduler.start()
    server_config = Config.from_mapping(
        bind=f"{app_config.api.host}:{app_config.api.port}",
        worker_class="trio"
    )
    asyncio.run(hypercorn_serve(create_app(), server_config))
