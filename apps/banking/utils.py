from datetime import datetime


def get_latest_years(n: int) -> list[str]:
    this_year = datetime.now().year
    ret: list[str] = []
    i = 0
    while n > i:
        ret.append(str(this_year - i))
        i += 1
    return ret
