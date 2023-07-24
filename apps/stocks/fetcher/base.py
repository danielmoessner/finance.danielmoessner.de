import abc

from apps.stocks.models import PriceFetcher, Stock


class Fetcher(abc.ABC):
    @abc.abstractmethod
    def fetch_single(self, stock: PriceFetcher) -> tuple[bool, str | float]:
        raise NotImplementedError()
    
    @abc.abstractmethod
    def fetch_multiple(self, stocks: list[PriceFetcher]) -> dict[Stock, tuple[bool, str | float]]:
        raise NotImplementedError()
