from datetime import datetime
from decimal import Decimal


def get_latest_years(n: int) -> list[str]:
    this_year = datetime.now().year
    ret: list[str] = []
    i = 0
    while n > i:
        ret.append(str(this_year - i))
        i += 1
    return ret


def format_currency_amount_to_de(value: float | Decimal) -> str:
    s = f"{value:.2f}"
    integral, decimal = s.split(".")
    rev = integral[::-1]
    grouped_rev = ".".join(rev[i : i + 3] for i in range(0, len(rev), 3))
    grouped_integral = grouped_rev[::-1]
    return f"{grouped_integral},{decimal}"
