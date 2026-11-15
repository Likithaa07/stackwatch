import pytest
import requests

from scripts import report

ROWS = [
    {
        "customer_id": "ok1",
        "region": "us",
        "avg_util": "60",
        "p95_util": "80",
        "peak_util": "85",
        "under_pct": "90",
        "over_pct": "40",
    },
    {
        "customer_id": "hot",
        "region": "eu",
        "avg_util": "100",
        "p95_util": "150",
        "peak_util": "170",
        "under_pct": "90",
        "over_pct": "40",
    },
    {
        "customer_id": "idle",
        "region": "unknown",
        "avg_util": "10",
        "p95_util": "20",
        "peak_util": "25",
        "under_pct": "90",
        "over_pct": "40",
    },
]


def test_render_ranks_worst_first_with_an_action_each():
    md = report.render(ROWS, "2026-11-13")
    order = [
        line.split("|")[2].strip() for line in md.splitlines() if line.startswith("| ") and line[2].isdigit()
    ]
    assert order == ["hot", "idle", "ok1"]
    assert "Re-size UP" in md and "Downsize" in md and "No action" in md
    assert "**2 of 3 customers need action.**" in md


def test_fetch_reads_the_splunk_export_stream():
    class Resp:
        text = '{"preview":false,"result":{"customer_id":"a"}}\n{"preview":false,"lastrow":true}\n'

        def raise_for_status(self):
            pass

    class Session:
        def post(self, url, **kw):
            self.url, self.kw = url, kw
            return Resp()

    s = Session()
    assert report.fetch(s, "https://h:8089", "admin", "pw") == [{"customer_id": "a"}]
    assert s.url == "https://h:8089/servicesNS/admin/stackwatch/search/jobs/export"
    assert "`stackwatch_thresholds`" in s.kw["data"]["search"]


@pytest.mark.parametrize(
    "env, fetched, message",
    [
        ({}, ROWS, "missing settings"),
        ({"SPLUNK_PASSWORD": "x"}, [], "no usage data"),
        ({"SPLUNK_PASSWORD": "x"}, requests.ConnectionError("down"), "report failed: down"),
    ],
)
def test_main_fails_clearly(monkeypatch, env, fetched, message):
    monkeypatch.delenv("SPLUNK_PASSWORD", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    def fake_fetch(*a, **k):
        if isinstance(fetched, Exception):
            raise fetched
        return fetched

    monkeypatch.setattr(report, "fetch", fake_fetch)
    with pytest.raises(SystemExit, match=message):
        report.main()


def test_main_writes_one_report_with_one_command(monkeypatch, tmp_path):
    monkeypatch.setenv("SPLUNK_PASSWORD", "x")
    monkeypatch.setenv("HEC_INSECURE", "true")
    monkeypatch.setattr(report, "OUT_DIR", tmp_path)
    monkeypatch.setattr(report, "fetch", lambda *a, **k: ROWS)
    report.main()
    assert [p.name.startswith("weekly-") for p in tmp_path.iterdir()] == [True]
