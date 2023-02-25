import dataclasses
from typing import Dict, List

from connect6.game import common
from connect6.game import errors
from connect6.game import player


__all__ = [
    "BaseTurnData",
    "TurnData",
]


@dataclasses.dataclass
class BaseTurnData:
    player: player.BasePlayer
    cells: List[common.Cell]

    def __post_init__(self) -> None:
        self._check_num_cells(len(self.cells))
        self._check_cells_are_different(self.cells)

    def _check_cells_are_different(self, cells: List[common.Cell]) -> None:
        if len(set(cells)) != len(cells):
            raise errors.EqualCellsInTurnError()

    @classmethod
    def _check_num_cells(cls, num_cells) -> None:
        if not hasattr(cls, "num_cells"):
            raise RuntimeError(
                f"Cannot create instance of a base class {cls.__name__!r}"
            )
        if num_cells != cls.num_cells:
            raise RuntimeError(
                f"Turn should consist of {cls.num_cells} cells, got {num_cells}"
            )


class _Registry(Dict[int, BaseTurnData]):
    def __getitem__(self, num_cells: int) -> BaseTurnData:
        if num_cells < 1:
            raise RuntimeError(f"Turn should consist of ≥ 1 cells, got {num_cells}")
        if num_cells not in self:
            self[num_cells] = type(  # type: ignore
                f"TurnData{num_cells}", (BaseTurnData,), dict(num_cells=num_cells)
            )
        return super().__getitem__(num_cells)


TurnData = _Registry()
