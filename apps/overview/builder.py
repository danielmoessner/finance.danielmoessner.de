from typing import Any

from django.db import models

from apps.core.functional import list_map
from apps.overview.domain import VBucket, combine_paths, get_percentage, get_total
from apps.overview.models import Bucket
from apps.users.models import StandardUser


def calc_total(user: StandardUser) -> float:
    buckets = Bucket.objects.filter(user=user)
    dbuckets = list_map(list(buckets), lambda x: x.dbucket)
    total = get_total(dbuckets)
    return total


def build_vtotal(buckets: list[VBucket], total: float) -> dict[str, str]:
    context = {}
    wanted = sum([b.actual_wanted_percentage for b in buckets]) if buckets else 0
    context["wanted"] = "{:,.2f} %".format(wanted)
    actual = sum(list_map(buckets, lambda x: x.percentage), 0.0)
    context["percentage"] = "{:,.2f} %".format(actual)
    diff = (wanted - actual) * total / 100
    context["diff"] = "{:,.2f} €".format(diff)
    context["amount"] = "{:,.2f} €".format(total * actual / 100)
    return context


def build_context_from_buckets(
    total: float, buckets: models.QuerySet[Bucket], layers=1
) -> dict[str, Any]:
    dbuckets_all = list_map(list(buckets), lambda x: x.dbucket)
    dbuckets = combine_paths(dbuckets_all, layers)
    percentage = get_percentage(dbuckets)
    vbuckets = list_map(dbuckets, lambda x: x.to_vbucket(total, percentage))
    vtotal = build_vtotal(vbuckets, total)
    return {"buckets": vbuckets, "total": vtotal}
