import abc
from typing import Generic, Mapping, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Fetcher(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def fetch_single(self, data: T) -> tuple[bool, str | float]:
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_multiple(self, data: dict[str, T]) -> Mapping[str, tuple[bool, str | float]]:
        raise NotImplementedError()
