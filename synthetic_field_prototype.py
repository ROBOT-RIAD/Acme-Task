"""
SYNTHETIC RESEARCH PROTOTYPE — FIELD BOUNDARY & CROP DERIVATION (v0.1)
----------------------------------------------------------------------
This is an unoptimized prototype script for detecting pitch boundaries and
computing camera crop layouts across video feeds.

DO NOT USE IN PRODUCTION.
"""
import os
import requests
import time


import cv2
import numpy as np
from shapely.geometry import Polygon

from synthetic_generator import generate_synthetic_video

CONFIG = {
    "video_path": "synthetic_pitch_feed.mp4",
    "target_fps": 30,
    "confidence_threshold": 0.5,
    "field_detector": {
        "type": "sam_mask_v1",
        "sport": "football",
        "min_area": 1000,
    },
    "crop_search": {
        "aspect_ratio": "16:9",
        "padding_px": 20,
    },
    "debug_mode": True,
}



MOCK_API_URL = os.getenv(
    "MOCK_API_URL",
    "http://localhost:5000",
)

REPORT_TIMEOUT = 5



def report_progress(processed_frames: int,total_frames: int):

    if total_frames <= 0:
        progress = 0.0
    else:
        progress = processed_frames / total_frames
    progress = min(max(progress, 0.0), 1.0)
    payload = {
        "progress": round(progress, 4),
        "processed_frames": processed_frames,
        "total_frames": total_frames,
    }
    url = f"{MOCK_API_URL}/api/v1/jobs/progress"
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
            f"[reporting] progress report failed: {exc}"
        )




def report_event(status: str,**data,):
    payload = {
        "status": status,
        **data,
    }
    url = f"{MOCK_API_URL}/api/v1/jobs/events"
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=REPORT_TIMEOUT,
        )

        response.raise_for_status()

        print(
            f"[reporting] event sent: {payload}"
        )

    except requests.RequestException as exc:
        print(
            f"[reporting] event report failed: {exc}"
        )







class FieldBoundaryAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.sport = config.get("field_detector", {}).get("sport", "soccer")
        self.threshold = config.get("confidence_threshold", 0.5)

    def process_video(self, video_path: str):
        print(f"Starting processing for video: {video_path}")
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("Error: Could not open video stream.")
            return

        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        frame_count = 0
        detected_polygons = []

        report_progress(
            processed_frames=0,
            total_frames=total_frames,
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            mask = self._extract_mask(frame)
            poly = self._derive_polygon_from_mask(mask)

            if poly and poly.is_valid:
                outer_boundary = Polygon([(0, 0), (1280, 0), (1280, 720), (0, 720)])
                intersection_area = poly.intersection(outer_boundary).area
                detected_polygons.append((frame_count, poly, intersection_area))

            # Simulate heavy per-frame processing latency
            time.sleep(0.005)

        cap.release()
        print(f"Processed {frame_count} frames. Found {len(detected_polygons)} boundaries.")
        return detected_polygons


    def _extract_mask(self, frame: np.ndarray) -> np.ndarray:
        # Dummy mask generation based on green color thresholding
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        return cv2.inRange(hsv, lower_green, upper_green)


    def _derive_polygon_from_mask(self, mask: np.ndarray):
        try:
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > self.config.get("field_detector", {}).get("min_area", 500):
                    pts = largest.reshape(-1, 2)
                    if len(pts) >= 3:
                        return Polygon(pts)
        except Exception:
            pass
        return None


def get_video_frame_count(video_path: str,) -> int:
    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: "
            f"{video_path}"
        )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    cap.release()

    return total_frames



def run_pipeline():
    """
    Execute the complete synthetic processing pipeline.
    """

    start_time = time.time()
    report_event("started",message="Pipeline started",)

    try:
        print(
            "Generating synthetic video..."
        )
        generate_synthetic_video(outputPath=CONFIG["video_path"])

        total_frames = (
                    get_video_frame_count(
                        CONFIG["video_path"]
                    )
                )
        
        analyzer = FieldBoundaryAnalyzer(CONFIG)

        results = analyzer.process_video(CONFIG["video_path"])
        report_progress(
                    processed_frames=total_frames,
                    total_frames=total_frames,
                )
        result_count = (len(results)if results else 0)

        duration = (time.time() - start_time)

        report_event(
            "completed",
            message="Pipeline completed successfully",
            processed_frames=1800,
            boundaries_detected=result_count,
            duration_seconds=round(
                duration,
                3,
            ),
        )

        print(
            f"Pipeline finished with "
            f"{result_count} results."
        )

    except Exception as exc:
        duration = (
            time.time() - start_time
        )
        print(
            f"Pipeline failed: {exc}"
        )
        report_event(
            "failed",
            message="Pipeline failed",
            error=str(exc),
            duration_seconds=round(
                duration,
                3,
            ),
        )
        raise



if __name__ == "__main__":
    run_pipeline()
