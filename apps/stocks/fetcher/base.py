import abc


class Fetcher(abc.ABC):
    @abc.abstractmethod
    def fetch_single(self, *args, **kwargs) -> tuple[bool, str | float]:
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_multiple(
        self, *args, **kwargs
    ) -> dict[str, tuple[bool, str | float]]:
        raise NotImplementedError()
