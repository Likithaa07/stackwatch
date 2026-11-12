"""Planned capacity per customer, based on SizeRight's v1 rules."""

# GB/day one indexer handles, copied from SizeRight rules/v1.yaml.
# If SizeRight changes these without bumping the rules version, StackWatch
# drifts silently: that is Drill 4, and why plan rows keep rules_version.
GB_PER_INDEXER = {"light": 300, "moderate": 200, "heavy": 150}
GB_PER_INDEXER_ES = 100


def gb_per_indexer(search_profile: str, premium_apps: list[str]) -> int:
    """GB/day a single indexer can take for this customer."""
    if "enterprise_security" in premium_apps:
        return GB_PER_INDEXER_ES
    return GB_PER_INDEXER[search_profile]


def planned_capacity_gb(indexers: int, search_profile: str, premium_apps: list[str]) -> int:
    """Total GB/day the planned indexers can take."""
    return indexers * gb_per_indexer(search_profile, premium_apps)
