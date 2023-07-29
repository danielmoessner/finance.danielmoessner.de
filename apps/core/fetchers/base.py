import abc
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)

class Fetcher(abc.ABC):
    @abc.abstractmethod
    def fetch_single(self, data: T) -> tuple[bool, str | float]:
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_multiple(
        self, data: dict[str, T]
    ) -> dict[str, tuple[bool, str | float]]:
        raise NotImplementedError()
