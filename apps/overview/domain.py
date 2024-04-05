import os

from pydantic import BaseModel

from apps.core.functional import dict_map, group_by, list_map, list_sum


class DBucket(BaseModel):
    pk: int | None
    path: str
    value: float
    wanted_percentage: float

    def __add__(self, other) -> "DBucket":
        if not isinstance(other, DBucket):
            return NotImplemented
        common_name = os.path.commonprefix([self.path, other.path])
        common_name = common_name.strip().rstrip("/").strip()
        if common_name == "":
            raise ValueError("buckets must have a common prefix")
        wanted_percentage = self.wanted_percentage + other.wanted_percentage
        value = self.value + other.value
        return DBucket(
            pk=None, path=common_name, value=value, wanted_percentage=wanted_percentage
        )

    def __radd__(self, other) -> "DBucket":
        return self.__add__(other)

    def to_vbucket(self, total: float, percentage: float) -> "VBucket":
        return VBucket(
            path=self.path,
            value=self.value,
            actual_wanted_percentage=self.wanted_percentage,
            total_value=total,
            total_percentage=percentage,
            pk=self.pk,
        )


def combine_paths(buckets: list[DBucket], layers: int) -> list[DBucket]:
    grouped = group_by(buckets, lambda x: "/".join(x.path.split("/")[:layers]))
    added = dict_map(grouped, lambda x: list_sum(x))
    return list(added.values())


def get_total(buckets: list[DBucket]) -> float:
    values = list_map(buckets, lambda x: x.value)
    return sum(values, 0.0)


def get_percentage(buckets: list[DBucket]) -> float:
    values = list_map(buckets, lambda x: x.wanted_percentage)
    return sum(values, 0.0)


class VBucket(BaseModel):
    pk: int | None
    path: str
    value: float
    actual_wanted_percentage: float
    total_value: float
    total_percentage: float

    @property
    def name(self) -> str:
        return self.path

    @property
    def percentage(self) -> float:
        return self.value / self.total_value * 100 if self.total_value else 0

    @property
    def is_ok(self) -> bool:
        return abs(self.actual_wanted_percentage - self.percentage) < 1

    def get_amount(self) -> str:
        amount = self.value
        return "{:,.2f} €".format(amount)

    def get_percentage(self) -> str:
        percentage = self.percentage
        return "{:,.2f} %".format(percentage)

    def get_wanted_percentage(self) -> str:
        ret = "{:,.2f} %".format(self.actual_wanted_percentage)
        return ret

    def get_diff(self) -> str:
        if self.is_ok:
            return "OK"
        wanted = self.actual_wanted_percentage * self.total_value / 100
        amount = self.value
        diff = wanted - amount
        return "{:,.2f} €".format(diff)


def build_vtotal(buckets: list[VBucket], total: float) -> dict[str, str]:
    context = {}
    context["amount"] = "{:,.2f} €".format(total)
    wanted = sum([b.actual_wanted_percentage for b in buckets]) if buckets else 0
    context["wanted"] = "{:,.2f} %".format(wanted)
    actual = sum(list_map(buckets, lambda x: x.percentage), 0.0)
    context["percentage"] = "{:,.2f} %".format(actual)
    return context
