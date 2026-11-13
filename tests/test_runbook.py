import re
from pathlib import Path

RUNBOOK = Path("docs/runbook.md").read_text()


def test_every_alert_links_to_a_runbook_section_with_meaning_steps_and_escalation():
    links = set(
        re.findall(
            r"runbook\.md#([\w-]+)", Path("splunk_app/stackwatch/default/savedsearches.conf").read_text()
        )
    )
    assert links == {"undersized", "no-data", "stale-plans"}
    sections = re.split(r"^## ", RUNBOOK, flags=re.M)[1:]
    anchors = {s.splitlines()[0].strip().lower().replace(" ", "-"): s for s in sections}
    for link in links:
        body = anchors[link]
        assert "**Meaning:**" in body and "**First 3 steps**" in body and "**Escalation:**" in body
        assert re.search(r"^3\. ", body, flags=re.M)
