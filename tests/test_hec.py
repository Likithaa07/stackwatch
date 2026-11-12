import json

import requests

from simulator.hec import HECClient, build_payload


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class FakeSession:
    """Plays back a list of responses (or exceptions) and records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.calls = []

    def post(self, url, data, timeout, verify):
        self.calls.append(data)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def client(responses):
    session = FakeSession(responses)
    sleeps = []
    c = HECClient("https://hec", "tok", session=session, sleep=sleeps.append)
    return c, session, sleeps


def test_payload_is_one_json_object_per_event():
    payload = build_payload([{"a": 1}, {"a": 2}], "stackwatch", "stackwatch:usage", 1.0)
    objs = [json.loads(p) for p in payload.replace("}{", "}\n{").splitlines()]
    assert [o["event"]["a"] for o in objs] == [1, 2]
    assert all(o["index"] == "stackwatch" and o["sourcetype"] == "stackwatch:usage" for o in objs)


def test_token_header():
    _, session, _ = client([])
    assert session.headers["Authorization"] == "Splunk tok"


def test_success_first_try():
    c, session, sleeps = client([FakeResponse(200)])
    assert c.send([{"x": 1}]) is True
    assert len(session.calls) == 1 and sleeps == []


def test_retries_on_5xx_and_network_errors_with_backoff():
    c, session, sleeps = client([FakeResponse(503), requests.ConnectionError("down"), FakeResponse(200)])
    assert c.send([{"x": 1}]) is True
    assert len(session.calls) == 3
    assert sleeps == [0.5, 1.0]


def test_does_not_retry_bad_token():
    c, session, sleeps = client([FakeResponse(403, "Invalid token")])
    assert c.send([{"x": 1}]) is False
    assert len(session.calls) == 1 and sleeps == []


def test_gives_up_after_all_tries():
    c, session, sleeps = client([FakeResponse(500)] * 4)
    assert c.send([{"x": 1}]) is False
    assert len(session.calls) == 4
    assert sleeps == [0.5, 1.0, 2.0]


def test_empty_batch_sends_nothing():
    c, session, _ = client([])
    assert c.send([]) is True
    assert session.calls == []
