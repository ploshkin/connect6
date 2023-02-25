from typing import Tuple

# TODO: pass turn_num to each error


class EqualCellsInTurnError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Cells in turn should be different")


class CellOutOfBoundsError(RuntimeError):
    def __init__(self, cell: Tuple[int, int], board_size: int) -> None:
        super().__init__(f"Cell {cell} out of bounds ({board_size=})")


class CellOccupiedError(RuntimeError):
    def __init__(self, cell: Tuple[int, int]) -> None:
        super.__init__(f"Cell {cell} is already occupied")


class WrongPlayerError(RuntimeError):
    def __init__(self, player: str, turn_num: int) -> None:
        super().__init__(f"Wrong player {player} for turn {turn_num}")


class NegativeCellCoordinateError(RuntimeError):
    def __init__(self, cell: Tuple[int, int]) -> None:
        super().__init__(f"Cell must have non-negative coordinates, got {cell}")


class WrongBufferShapeError(RuntimeError):
    def __init__(self, shape: Tuple[int, ...]) -> None:
        super().__init__(f"Buffer shape must be (*, 2), got {shape}")


class WrongTurnBuffers(RuntimeError):
    pass
