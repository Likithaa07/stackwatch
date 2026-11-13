import random
import threading

import pytest

from simulator import __main__ as runner

CUSTOMERS = [
    {
        "id": "a",
        "region": "us-east-1",
        "ingest_gb_per_day": 100,
        "concurrent_users": 10,
        "actual": {"start": 1.0, "growth_per_day": 0.0},
    },
    {
        "id": "b",
        "region": "eu-west-1",
        "ingest_gb_per_day": 200,
        "concurrent_users": 20,
        "actual": {"start": 0.5, "growth_per_day": 0.0},
    },
]


def test_config_defaults_and_overrides():
    cfg = runner.load_config({"HEC_URL": "u", "HEC_TOKEN": "t"})
    assert (cfg.interval, cfg.speed, cfg.insecure) == (60.0, 240.0, False)
    env = {"HEC_URL": "u", "HEC_TOKEN": "t", "SIM_INTERVAL": "5", "SIM_SPEED": "1", "HEC_INSECURE": "true"}
    cfg = runner.load_config(env)
    assert (cfg.interval, cfg.speed, cfg.insecure) == (5.0, 1.0, True)


@pytest.mark.parametrize(
    "env, message",
    [({}, "HEC_URL, HEC_TOKEN"), ({"HEC_URL": "u", "HEC_TOKEN": "t", "SIM_SPEED": "0"}, "positive")],
)
def test_config_fails_fast_with_clear_message(env, message):
    with pytest.raises(ValueError, match=message):
        runner.load_config(env)


def test_sim_clock_compresses_time():
    day, hour = runner.sim_clock(elapsed_real_s=360, speed=240, start_hour=8)
    assert day == pytest.approx(1.0)
    assert hour == pytest.approx(8.0)
    _, hour = runner.sim_clock(elapsed_real_s=60, speed=240, start_hour=8)
    assert hour == pytest.approx(12.0)


def test_load_capacities(tmp_path):
    f = tmp_path / "plans.csv"
    f.write_text("customer_id,planned_capacity_gb\na,500\nb,900\n")
    assert runner.load_capacities(f) == {"a": 500.0, "b": 900.0}


def test_tick_skips_customers_without_a_plan():
    events = runner.tick(CUSTOMERS, {"a": 100.0}, day=0, hour=12, rng=random.Random(1))
    assert [e["customer_id"] for e in events] == ["a"]


class RecordingClient:
    def __init__(self, stop, stop_after):
        self.batches, self.stop, self.stop_after = [], stop, stop_after

    def send(self, events):
        self.batches.append(events)
        if len(self.batches) == self.stop_after:
            self.stop.set()
        return True


def test_run_sends_batches_until_stopped():
    cfg = runner.Config("u", "t", False, interval=0.001, speed=240)
    stop = threading.Event()
    client = RecordingClient(stop, stop_after=3)
    assert runner.run(cfg, CUSTOMERS, {"a": 100.0, "b": 200.0}, client, stop) == 3
    assert all(len(b) == 2 for b in client.batches)


def test_main_exits_with_clear_message_when_misconfigured(monkeypatch):
    monkeypatch.delenv("HEC_URL", raising=False)
    monkeypatch.delenv("HEC_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="missing settings"):
        runner.main()


@pytest.mark.parametrize("insecure, expected_calls", [(True, 1), (False, 0)])
def test_warn_if_insecure_warns_once_only_when_tls_off(monkeypatch, caplog, insecure, expected_calls):
    calls = []
    monkeypatch.setattr(runner.urllib3, "disable_warnings", calls.append)
    runner.warn_if_insecure(insecure)
    assert len(calls) == expected_calls
    assert ("TLS verification OFF" in caplog.text) is insecure
