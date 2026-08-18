from __future__ import annotations

import logging

from fastapi import FastAPI

from hi_resolve.db import init_db
from hi_resolve.middleware import setup_middleware
from hi_resolve.urls import include_urls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("hi_resolve")

app = FastAPI(title="Hi Resolve")
setup_middleware(app)
include_urls(app)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("app started")
