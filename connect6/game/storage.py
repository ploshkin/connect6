from typing import Optional, Tuple

import numpy as np

from connect6.game import common
from connect6.game import errors


class CellStorage:
    INITIAL_LENGTH = 100
    EXTEND_FACTOR = 2

    def __init__(self, buffer: Optional[np.ndarray] = None) -> None:
        if buffer is not None:
            self.data = buffer
            self._length = len(buffer)
        else:
            self._buffer = np.empty((self.INITIAL_LENGTH, 2), np.int32)
            self._length = 0

    def __len__(self) -> int:
        return self._length

    @property
    def data(self) -> np.ndarray:
        return self._buffer[: len(self)]

    @data.setter
    def data(self, buffer: np.ndarray) -> None:
        buffer = buffer.astype(np.int32)
        if buffer.shape[1:] != (2,):
            raise errors.WrongBufferShapeError(buffer.shape)
        if (buffer < 0).any():
            raise ValueError("Stored coordinates should be non-negative")
        self._buffer = buffer

    def add(self, cell: common.Cell) -> None:
        if len(self._buffer) == len(self):
            self._extend_buffer()
        self._buffer[len(self)] = cell.as_tuple()
        self._length += 1

    def rows_cols(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.data[..., 0].flatten(), self.data[..., 1].flatten()

    def _extend_buffer(self) -> None:
        buffer = np.empty((self.EXTEND_FACTOR * len(self), 2), self._buffer.dtype)
        buffer[: len(self)] = self._buffer[: len(self)]
        self._buffer = buffer
