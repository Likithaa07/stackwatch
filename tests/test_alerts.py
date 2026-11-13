import configparser
import re
from pathlib import Path

DEFAULT = Path("splunk_app/stackwatch/default")


def conf(name):
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read(DEFAULT / name)
    return cp


def test_three_alerts_with_signed_off_severities():
    got = {s: a["alert.severity"] for s, a in conf("savedsearches.conf").items() if s != "DEFAULT"}
    assert got == {
        "StackWatch - UNDERSIZED": "5",
        "StackWatch - NO DATA": "3",
        "StackWatch - stale plans": "3",
    }


def test_alerts_run_every_5_min_and_are_throttled_per_customer_per_hour():
    alerts = conf("savedsearches.conf")
    for name in ("StackWatch - UNDERSIZED", "StackWatch - NO DATA", "StackWatch - stale plans"):
        a = alerts[name]
        assert (a["cron_schedule"], a["alert.suppress"], a["alert.suppress.period"]) == (
            "*/5 * * * *",
            "1",
            "1h",
        )
    for name in ("StackWatch - UNDERSIZED", "StackWatch - NO DATA"):
        assert alerts[name]["alert.suppress.fields"] == "customer_id"
    assert "runbook.md#undersized" in alerts["StackWatch - UNDERSIZED"]["search"]


def test_worst_case_detection_is_within_20_minutes():
    under_min = int(
        re.search(r"under_min=(\d+)", conf("macros.conf")["stackwatch_thresholds"]["definition"])[1]
    )
    schedule_min = int(conf("savedsearches.conf")["StackWatch - UNDERSIZED"]["cron_schedule"].split()[0][2:])
    assert under_min + schedule_min <= 20


def test_trigger_uses_conf_keys_so_alerts_only_fire_on_results():
    # alert_type/alert_comparator/alert_threshold are REST names; in .conf they are ignored -> "always fire"
    for name, a in conf("savedsearches.conf").items():
        if name == "DEFAULT":
            continue
        assert (a["counttype"], a["relation"], a["quantity"]) == ("number of events", "greater than", "0")
        assert not {"alert_type", "alert_comparator", "alert_threshold"} & set(a)
