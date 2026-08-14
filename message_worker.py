from __future__ import annotations

import base64
import json
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

from app.mass_message import run_mass_message


# =========================================================
# ENV
# =========================================================

load_dotenv()


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

WORKER_POLL_SECONDS = int(
    os.getenv(
        "MESSAGE_WORKER_POLL_SECONDS",
        "3",
    )
)


# =========================================================
# WORKER ID
# =========================================================

WORKER_ID = (
    f"{socket.gethostname()}-"
    f"{os.getpid()}"
)


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
# GITHUB
# =========================================================

def github_headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Missing GITHUB_TOKEN in local .env"
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


def github_contents_url() -> str:
    return (
        "https://api.github.com/repos/"
        f"{GITHUB_REPO}/contents/"
        f"{GITHUB_JOB_PATH}"
    )


# =========================================================
# READ JOB
# =========================================================

def read_job() -> dict[str, Any] | None:
    response = requests.get(
        github_contents_url(),
        headers=github_headers(),
        params={
            "ref": GITHUB_BRANCH,
        },
        timeout=20,
    )

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        raise RuntimeError(
            "Could not read GitHub job. "
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

    if not encoded_content:
        return None

    decoded = (
        base64.b64decode(
            encoded_content
        )
        .decode(
            "utf-8"
        )
        .strip()
    )

    if not decoded:
        return None

    try:
        job = json.loads(
            decoded
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "current_job.json contains invalid JSON."
        ) from exc

    if not isinstance(
        job,
        dict,
    ):
        raise RuntimeError(
            "current_job.json must contain a JSON object."
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
# WRITE JOB
# =========================================================

def write_job(
    job: dict[str, Any],
    *,
    commit_message: str,
    expected_sha: str | None = None,
) -> dict[str, Any]:
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

    payload: dict[str, Any] = {
        "message": commit_message,
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }

    if expected_sha:
        payload["sha"] = (
            expected_sha
        )

    response = requests.put(
        github_contents_url(),
        headers=github_headers(),
        json=payload,
        timeout=20,
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise RuntimeError(
            "Could not update GitHub job. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

    response_payload = (
        response.json()
    )

    content_data = (
        response_payload.get(
            "content"
        )
        or {}
    )

    new_sha = str(
        content_data.get(
            "sha",
            "",
        )
        or ""
    )

    result = clean_job.copy()

    result["_github_sha"] = (
        new_sha
    )

    return result


# =========================================================
# CLAIM JOB
# =========================================================

def claim_pending_job(
    job: dict[str, Any],
) -> dict[str, Any] | None:
    status = str(
        job.get(
            "status",
            "",
        )
        or ""
    ).lower()

    if status != "pending":
        return None

    job_id = str(
        job.get(
            "job_id",
            "",
        )
        or ""
    )

    if not job_id:
        raise RuntimeError(
            "Pending job has no job_id."
        )

    current_sha = str(
        job.get(
            "_github_sha",
            "",
        )
        or ""
    )

    now = utc_now_iso()

    claimed_job = job.copy()

    claimed_job["status"] = (
        "processing"
    )

    claimed_job["worker_id"] = (
        WORKER_ID
    )

    claimed_job["started_at"] = (
        now
    )

    claimed_job["updated_at"] = (
        now
    )

    claimed_job["error"] = ""

    print("")
    print("==============================")
    print("CLAIMING JOB")
    print("==============================")
    print(
        f"Job ID   : {job_id}"
    )
    print(
        f"Worker ID: {WORKER_ID}"
    )
    print("")

    try:
        return write_job(
            claimed_job,
            commit_message=(
                f"Claim message job {job_id}"
            ),
            expected_sha=current_sha,
        )

    except RuntimeError as exc:
        # GitHub SHA conflict means another worker
        # probably claimed or updated the job first.
        if (
            "Status: 409" in str(exc)
            or "Status: 422" in str(exc)
        ):
            print(
                "Job changed before claim. "
                "Skipping this poll."
            )

            return None

        raise


# =========================================================
# UPDATE PROGRESS
# =========================================================

def make_progress_callback(
    active_job: dict[str, Any],
):
    state = {
        "job": active_job,
    }

    def progress_callback(
        event: dict,
    ) -> None:
        job = state["job"]

        status = str(
            event.get(
                "status",
                "",
            )
            or ""
        )

        step = str(
            event.get(
                "step",
                "",
            )
            or ""
        )

        index = int(
            event.get(
                "index",
                0,
            )
            or 0
        )

        job["current"] = {
            "index": index,
            "total": event.get(
                "total",
                job.get(
                    "total",
                    0,
                ),
            ),
            "url": event.get(
                "url",
                "",
            ),
            "full_name": event.get(
                "full_name",
                "",
            ),
            "first_name": event.get(
                "first_name",
                "",
            ),
            "status": status,
            "step": step,
            "error": event.get(
                "error",
                "",
            ),
        }

        # ---------------------------------------------
        # PROFILE FINISHED
        # ---------------------------------------------

        if status in {
            "sent",
            "failed",
        }:
            results = list(
                job.get(
                    "results",
                    [],
                )
                or []
            )

            event_copy = {
                key: value
                for key, value in event.items()
                if not key.startswith(
                    "_"
                )
            }

            # Avoid duplicate result for the same index.
            results = [
                item
                for item in results
                if item.get(
                    "index"
                ) != index
            ]

            results.append(
                event_copy
            )

            job["results"] = results

            processed = len(
                results
            )

            sent = sum(
                1
                for item in results
                if item.get(
                    "status"
                ) == "sent"
            )

            failed = sum(
                1
                for item in results
                if item.get(
                    "status"
                ) == "failed"
            )

            job["processed"] = (
                processed
            )

            job["sent"] = sent
            job["failed"] = failed

        job["updated_at"] = (
            utc_now_iso()
        )

        current_sha = str(
            job.get(
                "_github_sha",
                "",
            )
            or ""
        )

        try:
            updated_job = write_job(
                job,
                commit_message=(
                    "Update message job progress"
                ),
                expected_sha=current_sha,
            )

            state["job"] = (
                updated_job
            )

        except Exception as exc:
            print(
                "Progress update failed:"
            )
            print(
                str(exc)
            )

    return (
        progress_callback,
        state,
    )


# =========================================================
# PROCESS CLAIMED JOB
# =========================================================

def process_claimed_job(
    claimed_job: dict[str, Any],
) -> None:
    job_id = str(
        claimed_job.get(
            "job_id",
            "",
        )
    )

    urls = list(
        claimed_job.get(
            "urls",
            [],
        )
        or []
    )

    template = str(
        claimed_job.get(
            "template",
            "",
        )
        or ""
    )

    print("")
    print("==============================")
    print("MESSAGE JOB STARTED")
    print("==============================")
    print(
        f"Job ID : {job_id}"
    )
    print(
        f"Profiles: {len(urls)}"
    )
    print("")

    progress_callback, state = (
        make_progress_callback(
            claimed_job
        )
    )

    try:
        results = run_mass_message(
            urls=urls,
            template=template,
            progress_callback=(
                progress_callback
            ),
        )

        job = state["job"]

        job["status"] = (
            "completed"
        )

        job["current"] = None

        job["results"] = (
            results
        )

        job["processed"] = len(
            results
        )

        job["sent"] = sum(
            1
            for item in results
            if item.get(
                "status"
            ) == "sent"
        )

        job["failed"] = sum(
            1
            for item in results
            if item.get(
                "status"
            ) == "failed"
        )

        job["completed_at"] = (
            utc_now_iso()
        )

        job["updated_at"] = (
            utc_now_iso()
        )

        current_sha = str(
            job.get(
                "_github_sha",
                "",
            )
            or ""
        )

        write_job(
            job,
            commit_message=(
                f"Complete message job {job_id}"
            ),
            expected_sha=current_sha,
        )

        print("")
        print("==============================")
        print("MESSAGE JOB COMPLETED")
        print("==============================")
        print(
            f"Sent  : {job['sent']}"
        )
        print(
            f"Failed: {job['failed']}"
        )
        print("")

    except Exception as exc:
        job = state["job"]

        job["status"] = "failed"

        job["error"] = str(
            exc
        )

        job["completed_at"] = (
            utc_now_iso()
        )

        job["updated_at"] = (
            utc_now_iso()
        )

        current_sha = str(
            job.get(
                "_github_sha",
                "",
            )
            or ""
        )

        try:
            write_job(
                job,
                commit_message=(
                    f"Fail message job {job_id}"
                ),
                expected_sha=current_sha,
            )

        except Exception as write_exc:
            print(
                "Could not write failed "
                "job status:"
            )
            print(
                str(write_exc)
            )

        print("")
        print("==============================")
        print("MESSAGE JOB FAILED")
        print("==============================")
        print(
            str(exc)
        )
        print("")


# =========================================================
# SINGLE POLL
# =========================================================

def poll_once() -> None:
    job = read_job()

    if job is None:
        return

    status = str(
        job.get(
            "status",
            "",
        )
        or ""
    ).lower()

    if status != "pending":
        return

    claimed_job = (
        claim_pending_job(
            job
        )
    )

    if claimed_job is None:
        return

    process_claimed_job(
        claimed_job
    )


# =========================================================
# MAIN LOOP
# =========================================================

def main() -> None:
    print("")
    print("==============================")
    print("LINKEDIN MESSAGE WORKER")
    print("==============================")
    print(
        f"Worker ID: {WORKER_ID}"
    )
    print(
        f"Repo     : {GITHUB_REPO}"
    )
    print(
        f"Job path : {GITHUB_JOB_PATH}"
    )
    print(
        f"Poll     : {WORKER_POLL_SECONDS}s"
    )
    print("")
    print(
        "Waiting for message jobs..."
    )
    print("")

    while True:
        try:
            poll_once()

        except KeyboardInterrupt:
            print("")
            print(
                "Worker stopped."
            )
            return

        except Exception as exc:
            print("")
            print(
                "Worker poll error:"
            )
            print(
                str(exc)
            )
            print("")

        time.sleep(
            WORKER_POLL_SECONDS
        )


if __name__ == "__main__":
    main()
