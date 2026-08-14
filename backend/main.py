from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

FRONTEND_DIR = (
    PROJECT_ROOT
    / "frontend"
)


# =========================================================
# GITHUB CONFIG
# =========================================================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
).strip()

GITHUB_REPO = os.getenv(
    "GITHUB_REPO",
    "minhwuan1234/linkedin-auto-mass-messeages",
).strip()

GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
).strip()

GITHUB_JOB_PATH = os.getenv(
    "GITHUB_JOB_PATH",
    "data/current_job.json",
).strip()


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="LinkedIn Mass Messages"
)


# =========================================================
# REQUEST MODEL
# =========================================================

class StartMessageRequest(
    BaseModel
):
    urls: list[str]
    template: str


# =========================================================
# TIME
# =========================================================

def utc_now_iso() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


# =========================================================
# GITHUB HEADERS
# =========================================================

def github_headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Missing GITHUB_TOKEN environment variable."
        )

    return {
        "Authorization": (
            f"Bearer {GITHUB_TOKEN}"
        ),
        "Accept": (
            "application/vnd.github+json"
        ),
        "X-GitHub-Api-Version": (
            "2022-11-28"
        ),
    }


# =========================================================
# GITHUB URL
# =========================================================

def github_contents_url() -> str:
    return (
        "https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_JOB_PATH}"
    )


# =========================================================
# READ CURRENT JOB
# =========================================================

def read_job_from_github() -> dict[str, Any] | None:
    response = requests.get(
        github_contents_url(),
        headers=github_headers(),
        params={
            "ref": GITHUB_BRANCH,
        },
        timeout=20,
    )

    # -----------------------------------------------------
    # File does not exist = no current job
    # -----------------------------------------------------

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise RuntimeError(
            "Could not read job from GitHub. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

    payload = response.json()

    encoded_content = str(
        payload.get(
            "content",
            "",
        )
        or ""
    )

    encoded_content = (
        encoded_content
        .replace(
            "\n",
            "",
        )
        .strip()
    )

    # -----------------------------------------------------
    # GitHub file exists but content field is empty
    # -----------------------------------------------------

    if not encoded_content:
        return None

    try:
        decoded = (
            base64.b64decode(
                encoded_content
            )
            .decode(
                "utf-8"
            )
        )

    except Exception as exc:
        raise RuntimeError(
            "Could not decode GitHub job file."
        ) from exc

    decoded = decoded.strip()

    # -----------------------------------------------------
    # File itself contains blank text such as "\n"
    # -----------------------------------------------------

    if not decoded:
        return None

    # -----------------------------------------------------
    # Parse JSON safely
    # -----------------------------------------------------

    try:
        job = json.loads(
            decoded
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "GitHub job file contains invalid JSON. "
            f"Path: {GITHUB_JOB_PATH}"
        ) from exc

    if not isinstance(
        job,
        dict,
    ):
        raise RuntimeError(
            "GitHub job file must contain "
            "a JSON object."
        )

    job["_github_sha"] = str(
        payload.get(
            "sha",
            "",
        )
        or ""
    )

    return job


# =========================================================
# WRITE CURRENT JOB
# =========================================================

def write_job_to_github(
    job: dict[str, Any],
    *,
    commit_message: str,
) -> None:
    existing_job = (
        read_job_from_github()
    )

    existing_sha = ""

    if existing_job is not None:
        existing_sha = str(
            existing_job.get(
                "_github_sha",
                "",
            )
            or ""
        ).strip()

    # -----------------------------------------------------
    # Important:
    #
    # If file exists but is blank, read_job_from_github()
    # returns None, but GitHub still requires SHA to update.
    #
    # So query the raw file metadata again when necessary.
    # -----------------------------------------------------

    if not existing_sha:
        metadata_response = requests.get(
            github_contents_url(),
            headers=github_headers(),
            params={
                "ref": GITHUB_BRANCH,
            },
            timeout=20,
        )

        if metadata_response.status_code == 200:
            metadata = (
                metadata_response.json()
            )

            existing_sha = str(
                metadata.get(
                    "sha",
                    "",
                )
                or ""
            ).strip()

        elif metadata_response.status_code != 404:
            raise RuntimeError(
                "Could not inspect existing GitHub "
                "job file. "
                f"Status: "
                f"{metadata_response.status_code}. "
                f"Response: "
                f"{metadata_response.text}"
            )

    clean_job = {
        key: value
        for key, value in job.items()
        if not key.startswith(
            "_github_"
        )
    }

    raw_json = json.dumps(
        clean_job,
        ensure_ascii=False,
        indent=2,
    )

    encoded_content = (
        base64.b64encode(
            raw_json.encode(
                "utf-8"
            )
        )
        .decode(
            "ascii"
        )
    )

    request_payload: dict[str, Any] = {
        "message": commit_message,
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }

    # Existing GitHub file → SHA required.
    if existing_sha:
        request_payload["sha"] = (
            existing_sha
        )

    response = requests.put(
        github_contents_url(),
        headers=github_headers(),
        json=request_payload,
        timeout=20,
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise RuntimeError(
            "Could not write job to GitHub. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )


# =========================================================
# NORMALIZE URLS
# =========================================================

def normalize_urls(
    urls: list[str],
) -> list[str]:
    clean_urls: list[str] = []
    seen: set[str] = set()

    for raw_url in urls:
        url = str(
            raw_url or ""
        ).strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(
            url
        )

        clean_urls.append(
            url
        )

    return clean_urls


# =========================================================
# IDLE STATE
# =========================================================

def idle_state() -> dict[str, Any]:
    return {
        "status": "idle",
        "job_id": None,
        "total": 0,
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "current": None,
        "results": [],
        "error": "",
    }


# =========================================================
# CREATE NEW MESSAGE JOB
# =========================================================

@app.post(
    "/api/messages/start"
)
def start_messages(
    request: StartMessageRequest,
) -> dict[str, Any]:
    clean_urls = normalize_urls(
        request.urls
    )

    template = str(
        request.template
        or ""
    ).strip()

    # -----------------------------------------------------
    # Validate URLs
    # -----------------------------------------------------

    if not clean_urls:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one LinkedIn URL "
                "is required."
            ),
        )

    # -----------------------------------------------------
    # Validate template
    # -----------------------------------------------------

    if not template:
        raise HTTPException(
            status_code=400,
            detail=(
                "Message template "
                "cannot be empty."
            ),
        )

    if "{first_name}" not in template:
        raise HTTPException(
            status_code=400,
            detail=(
                "Message template must "
                "contain {first_name}."
            ),
        )

    # -----------------------------------------------------
    # Check current job
    # -----------------------------------------------------

    try:
        current_job = (
            read_job_from_github()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(
                exc
            ),
        ) from exc

    if current_job is not None:
        current_status = str(
            current_job.get(
                "status",
                "",
            )
            or ""
        ).lower()

        if current_status in {
            "pending",
            "processing",
            "running",
        }:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A messaging job "
                    "is already active."
                ),
            )

    # -----------------------------------------------------
    # Build new job
    # -----------------------------------------------------

    job_id = str(
        uuid4()
    )

    now = utc_now_iso()

    job: dict[str, Any] = {
        "job_id": job_id,

        "status": "pending",

        "urls": clean_urls,

        "template": template,

        "total": len(
            clean_urls
        ),

        "processed": 0,
        "sent": 0,
        "failed": 0,

        "current": None,

        "results": [],

        "error": "",

        "created_at": now,

        "started_at": None,

        "completed_at": None,

        "worker_id": None,

        "updated_at": now,
    }

    # -----------------------------------------------------
    # Write job to GitHub
    # -----------------------------------------------------

    try:
        write_job_to_github(
            job,
            commit_message=(
                f"Create message job {job_id}"
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(
                exc
            ),
        ) from exc

    return {
        "ok": True,
        "job_id": job_id,
        "status": "pending",
        "total": len(
            clean_urls
        ),
    }


# =========================================================
# CURRENT JOB STATUS
# =========================================================

@app.get(
    "/api/messages/status"
)
def message_status() -> dict[str, Any]:
    try:
        job = (
            read_job_from_github()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(
                exc
            ),
        ) from exc

    if job is None:
        return idle_state()

    job.pop(
        "_github_sha",
        None,
    )

    return job


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/api/health"
)
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": (
            "linkedin-auto-mass-messeages"
        ),
        "github_repo": GITHUB_REPO,
        "github_branch": GITHUB_BRANCH,
        "github_job_path": GITHUB_JOB_PATH,
    }


# =========================================================
# FRONTEND
# =========================================================

@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR
        / "index.html"
    )


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)
