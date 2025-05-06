from typing import TypeVar

T = TypeVar("T")


def flatten(list: list[list[T]]) -> list[T]:
    return [item for sublist in list for item in sublist]
