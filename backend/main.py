from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.mass_message import run_mass_message


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

FRONTEND_DIR = (
    PROJECT_ROOT
    / "frontend"
)


app = FastAPI(
    title="LinkedIn Mass Messages"
)


job_state: dict[str, Any] = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "sent": 0,
    "failed": 0,
    "current": None,
    "results": [],
}


class StartMessageRequest(
    BaseModel
):
    urls: list[str]
    template: str


def update_progress(
    event: dict,
) -> None:
    global job_state

    job_state["current"] = event

    status = event.get(
        "status"
    )

    if status == "sent":
        job_state["processed"] += 1
        job_state["sent"] += 1

        job_state["results"].append(
            event
        )

    elif status == "failed":
        job_state["processed"] += 1
        job_state["failed"] += 1

        job_state["results"].append(
            event
        )


def run_job(
    urls: list[str],
    template: str,
) -> None:
    global job_state

    try:
        run_mass_message(
            urls=urls,
            template=template,
            progress_callback=update_progress,
        )

        job_state["status"] = "completed"
        job_state["current"] = None

    except Exception as exc:
        job_state["status"] = "failed"
        job_state["error"] = str(
            exc
        )


@app.post(
    "/api/messages/start"
)
def start_messages(
    request: StartMessageRequest,
) -> dict:
    global job_state

    if job_state["status"] == "running":
        return {
            "ok": False,
            "error": (
                "A messaging job is already running."
            ),
        }

    clean_urls = [
        url.strip()
        for url in request.urls
        if url.strip()
    ]

    job_state = {
        "status": "running",
        "total": len(clean_urls),
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "current": None,
        "results": [],
        "error": "",
    }

    thread = threading.Thread(
        target=run_job,
        args=(
            clean_urls,
            request.template,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "ok": True,
        "total": len(clean_urls),
    }


@app.get(
    "/api/messages/status"
)
def message_status() -> dict:
    return job_state


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR
        / "index.html"
    )


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)
