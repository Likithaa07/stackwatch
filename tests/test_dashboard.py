import xml.etree.ElementTree as ET
from pathlib import Path

UI = Path("splunk_app/stackwatch/default/data/ui")


def test_dashboard_has_required_inputs_drilldown_and_shared_macros():
    root = ET.parse(UI / "views/stackwatch_overview.xml").getroot()
    assert {"time", "region", "customer"} <= {i.get("token") for i in root.iter("input")}
    assert root.find(".//table/drilldown") is not None
    queries = " ".join(q.text for q in root.iter("query"))
    for macro in ("stackwatch_status", "stackwatch_thresholds", "stackwatch_current_rules"):
        assert f"`{macro}`" in queries


def test_app_opens_on_the_dashboard():
    nav = ET.parse(UI / "nav/default.xml").getroot()
    assert nav.find("view[@default='true']").get("name") == "stackwatch_overview"


def test_region_filters_keep_plans_with_missing_region():
    root = ET.parse(UI / "views/stackwatch_overview.xml").getroot()
    region_queries = [
        q.text for q in root.iter("query") if "inputlookup" in q.text or "OUTPUT region" in q.text
    ]
    assert region_queries and all("fillnull value=unknown region" in q for q in region_queries)
