"""Send events to Splunk's HTTP Event Collector (HEC), in batches, with retries."""

import json
import logging
import time

import requests

log = logging.getLogger("hec")


def build_payload(events: list[dict], index: str, sourcetype: str, now: float) -> str:
    """HEC accepts many events in one request: one JSON object per event, back to back."""
    return "".join(
        json.dumps({"time": now, "index": index, "sourcetype": sourcetype, "event": e}) for e in events
    )


class HECClient:
    def __init__(
        self,
        url: str,
        token: str,
        index: str = "stackwatch",
        sourcetype: str = "stackwatch:usage",
        verify_tls: bool = True,
        tries: int = 4,
        session: requests.Session | None = None,
        sleep=time.sleep,
    ):
        self.url = url
        self.index = index
        self.sourcetype = sourcetype
        self.verify_tls = verify_tls
        self.tries = tries
        self.sleep = sleep
        self.session = session or requests.Session()
        self.session.headers["Authorization"] = f"Splunk {token}"

    def send(self, events: list[dict]) -> bool:
        """Send a batch. Retries with exponential backoff; returns False instead of crashing."""
        if not events:
            return True
        payload = build_payload(events, self.index, self.sourcetype, time.time())
        for attempt in range(1, self.tries + 1):
            try:
                r = self.session.post(self.url, data=payload, timeout=5, verify=self.verify_tls)
                if r.status_code == 200:
                    return True
                # 4xx (bad token, wrong index) will not fix itself: stop retrying.
                if 400 <= r.status_code < 500:
                    log.error("HEC rejected batch: %s %s", r.status_code, r.text[:200])
                    return False
                log.warning("HEC returned %s (attempt %d)", r.status_code, attempt)
            except requests.RequestException as e:
                log.warning("HEC unreachable: %s (attempt %d)", e, attempt)
            if attempt < self.tries:
                self.sleep(0.5 * 2 ** (attempt - 1))
        log.error("dropping %d events after %d attempts", len(events), self.tries)
        return False
