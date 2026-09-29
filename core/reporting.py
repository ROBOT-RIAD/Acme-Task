import requests

from core.config import (
    MOCK_API_URL,
    REPORT_TIMEOUT,
)


def report_progress(processed_frames: int,total_frames: int,):
    if total_frames <= 0:
        progress = 0.0
    else:
        progress = processed_frames / total_frames

    progress = min(
        max(progress, 0.0),
        1.0,
    )

    payload = {
        "progress": round(progress, 4),
        "processed_frames": processed_frames,
        "total_frames": total_frames,
    }

    url = (
        f"{MOCK_API_URL}"
        "/api/v1/jobs/progress"
    )

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=REPORT_TIMEOUT,
        )

        response.raise_for_status()

        print(
            f"[reporting] progress "
            f"{processed_frames}/{total_frames} "
            f"({progress * 100:.1f}%)"
        )

    except requests.RequestException as exc:
        print(
            f"[reporting] progress "
            f"report failed: {exc}"
        )


def report_event(status: str,**data,):
    payload = {
        "status": status,
        **data,
    }

    url = (
        f"{MOCK_API_URL}"
        "/api/v1/jobs/events"
    )

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=REPORT_TIMEOUT,
        )

        response.raise_for_status()

        print(
            f"[reporting] event sent: "
            f"{payload}"
        )

    except requests.RequestException as exc:
        print(
            f"[reporting] event "
            f"report failed: {exc}"
        )