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
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


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

GITHUB_CONTACTS_PATH = os.getenv(
    "GITHUB_CONTACTS_PATH",
    "data/contacts.json",
).strip()


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="LinkedIn Mass Messages"
)


# =========================================================
# REQUEST
# =========================================================

class StartMessageRequest(BaseModel):
    urls: list[str]
    template: str


# =========================================================
# UTILS
# =========================================================

def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def github_headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Missing GITHUB_TOKEN environment variable."
        )

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_contents_url(
    path: str,
) -> str:
    return (
        "https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/{path}"
    )


# =========================================================
# GENERIC GITHUB JSON READ
# =========================================================

def read_json_file(
    path: str,
) -> tuple[Any | None, str]:
    response = requests.get(
        github_contents_url(path),
        headers=github_headers(),
        params={
            "ref": GITHUB_BRANCH,
        },
        timeout=20,
    )

    if response.status_code == 404:
        return None, ""

    if response.status_code != 200:
        raise RuntimeError(
            f"Could not read {path}. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

    payload = response.json()

    sha = str(
        payload.get("sha", "")
        or ""
    )

    encoded_content = str(
        payload.get("content", "")
        or ""
    )

    encoded_content = (
        encoded_content
        .replace("\n", "")
        .strip()
    )

    if not encoded_content:
        return None, sha

    try:
        decoded = (
            base64.b64decode(
                encoded_content
            )
            .decode("utf-8")
            .strip()
        )

    except Exception as exc:
        raise RuntimeError(
            f"Could not decode {path}."
        ) from exc

    if not decoded:
        return None, sha

    try:
        data = json.loads(
            decoded
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{path} contains invalid JSON."
        ) from exc

    return data, sha


# =========================================================
# GENERIC GITHUB JSON WRITE
# =========================================================

def write_json_file(
    path: str,
    data: Any,
    *,
    commit_message: str,
) -> None:
    _, existing_sha = (
        read_json_file(path)
    )

    raw_json = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    encoded_content = (
        base64.b64encode(
            raw_json.encode("utf-8")
        )
        .decode("ascii")
    )

    payload: dict[str, Any] = {
        "message": commit_message,
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }

    if existing_sha:
        payload["sha"] = (
            existing_sha
        )

    response = requests.put(
        github_contents_url(path),
        headers=github_headers(),
        json=payload,
        timeout=20,
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise RuntimeError(
            f"Could not write {path}. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )


# =========================================================
# JOB
# =========================================================

def read_job() -> dict[str, Any] | None:
    data, sha = read_json_file(
        GITHUB_JOB_PATH
    )

    if data is None:
        return None

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Current job must be a JSON object."
        )

    data["_github_sha"] = sha

    return data


def write_job(
    job: dict[str, Any],
    *,
    commit_message: str,
) -> None:
    clean_job = {
        key: value
        for key, value in job.items()
        if not key.startswith("_github_")
    }

    write_json_file(
        GITHUB_JOB_PATH,
        clean_job,
        commit_message=commit_message,
    )


# =========================================================
# CONTACTS
# =========================================================

def read_contacts() -> list[dict[str, Any]]:
    data, _ = read_json_file(
        GITHUB_CONTACTS_PATH
    )

    if data is None:
        return []

    if not isinstance(
        data,
        list,
    ):
        raise RuntimeError(
            "contacts.json must contain a JSON array."
        )

    return data


def queue_contacts(
    urls: list[str],
    job_id: str,
) -> None:
    contacts = read_contacts()

    now = utc_now_iso()

    by_url = {
        str(item.get("url", "")): item
        for item in contacts
        if item.get("url")
    }

    for url in urls:
        existing = by_url.get(url)

        if existing:
            existing["status"] = "queued"
            existing["last_job_id"] = job_id
            existing["error"] = ""
            existing["updated_at"] = now

        else:
            contact = {
                "url": url,
                "full_name": "",
                "first_name": "",
                "status": "queued",
                "message": "",
                "last_job_id": job_id,
                "sent_at": None,
                "error": "",
                "created_at": now,
                "updated_at": now,
            }

            contacts.append(
                contact
            )

            by_url[url] = contact

    write_json_file(
        GITHUB_CONTACTS_PATH,
        contacts,
        commit_message=(
            f"Queue contacts for job {job_id}"
        ),
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

        seen.add(url)
        clean_urls.append(url)

    return clean_urls


# =========================================================
# IDLE
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
# START JOB
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
        request.template or ""
    ).strip()

    if not clean_urls:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one LinkedIn URL is required."
            ),
        )

    if not template:
        raise HTTPException(
            status_code=400,
            detail=(
                "Message template cannot be empty."
            ),
        )

    if "{first_name}" not in template:
        raise HTTPException(
            status_code=400,
            detail=(
                "Message template must contain "
                "{first_name}."
            ),
        )

    try:
        current_job = read_job()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if current_job:
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
                    "A messaging job is already active."
                ),
            )

    job_id = str(
        uuid4()
    )

    now = utc_now_iso()

    job = {
        "job_id": job_id,
        "status": "pending",

        "urls": clean_urls,
        "template": template,

        "total": len(clean_urls),

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

    try:
        queue_contacts(
            clean_urls,
            job_id,
        )

        write_job(
            job,
            commit_message=(
                f"Create message job {job_id}"
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "job_id": job_id,
        "status": "pending",
        "total": len(clean_urls),
    }


# =========================================================
# JOB STATUS
# =========================================================

@app.get(
    "/api/messages/status"
)
def message_status() -> dict[str, Any]:
    try:
        job = read_job()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if job is None:
        return idle_state()

    job.pop(
        "_github_sha",
        None,
    )

    return job


# =========================================================
# CONTACT LIST
# =========================================================

@app.get(
    "/api/contacts"
)
def contact_list() -> dict[str, Any]:
    try:
        contacts = (
            read_contacts()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    contacts = sorted(
        contacts,
        key=lambda item: (
            item.get(
                "updated_at",
                "",
            )
            or ""
        ),
        reverse=True,
    )

    return {
        "total": len(contacts),
        "contacts": contacts,
    }


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
        "github_contacts_path": (
            GITHUB_CONTACTS_PATH
        ),
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


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)
