import logging
from typing import Optional

import numpy as np

from connect6.game import common, constants, errors
from connect6.game.player import BasePlayer
from connect6.game.state import GameState
from connect6.game.turn_data import BaseTurnData, TurnData

logger = logging.getLogger(__name__)


class GameEngine:
    def __init__(
        self,
        size: int = 19,
        num_players: int = 2,
        num_cells_per_turn: int = 2,
        num_cells_to_win: int = 6,
        *,
        _state: Optional[GameState] = None,
    ) -> None:
        if _state is not None:
            logger.info(f"Restoring {self.__class__.__name__} from state")
            self._state = _state
        else:
            self._validate_board_size(size)
            logger.info(f"Initializing {self.__class__.__name__}")
            self._state = GameState(
                size, num_players, num_cells_per_turn, num_cells_to_win
            )
        self._board = self.state.generate_board()
        logger.info(f"Successfully initialized {self}")

    @classmethod
    def restore(cls, state: GameState) -> "GameEngine":
        return cls(_state=state)

    @property
    def max_num_turns(self) -> int:
        """Maximum possible number of turns on the board of given size."""
        return (self._size**2 - 1) // self.state.num_cells_per_turn + 1

    @property
    def current_player(self) -> BasePlayer:
        return self.state.Player.current(self.state.num_turns)

    @property
    def state(self) -> GameState:
        return self._state

    def turn(self, data: BaseTurnData) -> None:
        self._validate_turn(data)
        self.state.turn(data)
        for cell in data.cells:
            self._board[cell.row, cell.col] = data.player.value

    def is_win(self, data: BaseTurnData) -> bool:
        return any(self._check_win_condition(cell, data.player) for cell in data.cells)

    def is_occupied(self, cell: common.Cell) -> bool:
        return bool(self._board[cell.row, cell.col])

    def __repr__(self) -> str:
        params = self.state.as_dict()
        params.pop("history")
        params_str = ", ".join(f"{key}={val}" for key, val in params.items())
        return f"{self.__class__.__name__}({params_str}), turn #{self.state.num_turns}"

    @property
    def _size(self) -> int:
        return self.state.size

    def _check_win_condition(self, cell: common.Cell, player: BasePlayer) -> bool:
        """Checks if at least N cells are connected using the given cell."""
        radius = self.state.num_cells_to_win - 1
        coords = np.array(cell.as_tuple(), np.int64)
        directions = np.array([(1, -1), (1, 0), (1, 1), (0, 1)], np.int64)
        for direction in directions:
            values = []
            for offset in range(-radius, radius + 1):
                row, col = coords + offset * direction
                if (0 <= row < self._size) and (0 <= col < self._size):
                    values.append(self._board[row, col])
            num_connected_cells = common.max_segment_length(values, player.value)
            if num_connected_cells >= self.state.num_cells_to_win:
                return True
        return False

    def _validate_board_size(self, size: int) -> None:
        if size % 2 == 0:
            raise RuntimeError(f"Board size must be odd number, got {size}")
        if not (constants.MIN_BOARD_SIZE <= size <= constants.MAX_BOARD_SIZE):
            bounds = [constants.MIN_BOARD_SIZE, constants.MAX_BOARD_SIZE]
            raise RuntimeError(f"Board size {size} not in {bounds}")

    def _validate_turn(self, data: BaseTurnData) -> None:
        if data.player is not self.current_player:
            raise errors.WrongPlayerError(data.player.name, self.state.num_turns)

        if not isinstance(data, TurnData[self.state.num_cells_per_turn]):  # type: ignore
            raise RuntimeError  # TODO

        for cell in data.cells:
            self._validate_coordinates(cell)

    def _validate_coordinates(self, cell: common.Cell) -> None:
        if cell.row >= self._size or cell.col >= self._size:
            raise errors.CellOutOfBoundsError(cell.as_tuple(), self._size)

        if self.is_occupied(cell):
            raise errors.CellOccupiedError(cell.as_tuple())
