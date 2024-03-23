from typing import Any

from django.db import models

from apps.core.functional import list_map
from apps.overview.domain import VBucket, combine_paths, get_percentage, get_total
from apps.overview.models import Bucket


def build_vtotal(buckets: list[VBucket], total: float) -> dict[str, str]:
    context = {}
    context["amount"] = "{:,.2f} €".format(total)
    wanted = sum([b.actual_wanted_percentage for b in buckets]) if buckets else 0
    context["wanted"] = "{:,.2f} %".format(wanted)
    if wanted != 100:
        context["wanted"] += " (100.00 %)"
    actual = sum(list_map(buckets, lambda x: x.percentage), 0.0)
    context["percentage"] = "{:,.2f} %".format(actual)
    return context


def build_context_from_buckets(
    buckets: models.QuerySet[Bucket], layers=1
) -> dict[str, Any]:
    dbuckets_all = list_map(list(buckets), lambda x: x.dbucket)
    dbuckets = combine_paths(dbuckets_all, layers)
    total = get_total(dbuckets)
    percentage = get_percentage(dbuckets)
    vbuckets = list_map(dbuckets, lambda x: x.to_vbucket(total, percentage))
    vtotal = build_vtotal(vbuckets, total)
    return {"buckets": vbuckets, "total": vtotal}
