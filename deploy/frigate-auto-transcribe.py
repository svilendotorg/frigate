#!/usr/bin/env python3
"""Auto-transcribe Frigate speech events by polling the API."""
import logging
import os
import time

import requests

FRIGATE_API = os.environ.get("FRIGATE_API_URL", "http://127.0.0.1:5000")
POLL_INTERVAL = 30  # seconds between polls
TRANSCRIBE_TIMEOUT = 120  # seconds to wait for transcription to complete

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("auto-transcribe")


def wait_for_api():
    """Block until Frigate API is ready."""
    while True:
        try:
            r = requests.get(f"{FRIGATE_API}/api/stats", timeout=5)
            if r.ok:
                log.info("Frigate API ready")
                return
        except Exception:
            pass
        log.info("Waiting for Frigate API...")
        time.sleep(5)


def get_untranscribed_events(after: float) -> list[dict]:
    """Fetch speech events without descriptions since given timestamp."""
    try:
        r = requests.get(
            f"{FRIGATE_API}/api/events",
            params={"label": "speech", "limit": 100, "after": after},
            timeout=10,
        )
        r.raise_for_status()
        events = r.json()
        return [e for e in events if not e.get("data", {}).get("description")]
    except Exception as e:
        log.error(f"Failed to fetch events: {e}")
        return []


def transcribe_event(event_id: str) -> bool:
    """Trigger transcription and wait for result. Returns True on success."""
    try:
        r = requests.put(
            f"{FRIGATE_API}/api/audio/transcribe",
            json={"event_id": event_id},
            timeout=10,
        )
        if not r.ok:
            log.warning(f"{event_id}: trigger failed {r.status_code} {r.text}")
            return False
        if r.json().get("message") == "in_progress":
            log.debug(f"{event_id}: transcription already running, will retry next poll")
            return False
    except Exception as e:
        log.error(f"{event_id}: trigger error: {e}")
        return False

    # Poll until description appears or timeout
    deadline = time.time() + TRANSCRIBE_TIMEOUT
    while time.time() < deadline:
        time.sleep(3)
        try:
            r = requests.get(f"{FRIGATE_API}/api/events/{event_id}", timeout=10)
            desc = r.json().get("data", {}).get("description")
            if desc:
                log.info(f"{event_id}: {desc[:80]}")
                return True
        except Exception:
            pass

    log.warning(f"{event_id}: timed out waiting for transcription")
    return False


def main():
    log.info(f"Starting — polling {FRIGATE_API} every {POLL_INTERVAL}s")
    wait_for_api()
    # Start from 24h ago to catch any missed recent events
    poll_after = time.time() - 86400

    while True:
        events = get_untranscribed_events(poll_after)
        if events:
            log.info(f"Found {len(events)} untranscribed speech events")
            for event in events:
                transcribe_event(event["id"])
                time.sleep(1)  # brief pause between API calls
        # Next poll: look back 10 minutes to catch any that appeared late
        poll_after = time.time() - 600
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
