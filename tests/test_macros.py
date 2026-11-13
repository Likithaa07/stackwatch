import configparser
import re
from pathlib import Path

CONF = Path("splunk_app/stackwatch/default/macros.conf")


def macro(name):
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(CONF)
    return cp[name]["definition"]


def test_thresholds_match_signed_off_requirements():
    got = dict(re.findall(r"(\w+)=(\d+)", macro("stackwatch_thresholds")))
    assert got == {
        "under_pct": "90",
        "under_min": "15",
        "over_pct": "40",
        "over_min": "60",
        "nodata_min": "10",
    }


def test_status_logic_uses_named_thresholds_not_hardcoded_numbers():
    d = macro("stackwatch_status")
    assert "`stackwatch_thresholds`" in d
    assert not re.search(r"[<>]=?\s*\d", d)
