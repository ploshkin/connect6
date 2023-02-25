import dataclasses
from numbers import Number
from typing import List, Tuple

from connect6.game import errors


@dataclasses.dataclass(unsafe_hash=True)
class Cell:
    row: int
    col: int

    def __post_init__(self) -> None:
        if self.row < 0 or self.col < 0:
            raise errors.NegativeCellCoordinateError(self.as_tuple())

    def as_tuple(self) -> Tuple[int, int]:
        return dataclasses.astuple(self)


def max_segment_length(array: List[Number], value: Number) -> int:
    max_length = 0
    length = 0
    for item in array:
        if item == value:
            length += 1
            max_length = max(max_length, length)
        else:
            length = 0
    return max_length
