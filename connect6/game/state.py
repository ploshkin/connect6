from collections import defaultdict
from os import PathLike
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from connect6.game.player import Player
from connect6.game.storage import CellStorage
from connect6.game.turn_data import BaseTurnData


class GameState:
    def __init__(
            self,
            size: int,
            num_players: int,
            num_cells_per_turn: int,
            num_cells_to_win: int, 
            history: Optional[Dict[str, CellStorage]] = None,
    ) -> None:
        self._size = size
        self._num_cells_per_turn = num_cells_per_turn
        self._num_cells_to_win = num_cells_to_win

        history = defaultdict(CellStorage) if history is None else history
        self._history = {player: history[player.name] for player in Player[num_players]}

        self._validate_history()

    @property
    def size(self) -> int:
        return self._size

    @property
    def num_turns(self) -> int:
        num_occupied_cells = sum(map(len, self._history.values()))
        return num_occupied_cells // self.num_cells_per_turn + 1  # first turn

    @property
    def num_players(self) -> int:
        return len(self._history)

    @property
    def num_cells_per_turn(self) -> int:
        return self._num_cells_per_turn

    @property
    def num_cells_to_win(self) -> int:
        return self._num_cells_to_win

    def turn(self, data: BaseTurnData) -> None:
        for cell in data.cells:
            self._history[data.player].add(cell)

    def as_dict(self) -> Dict[str, Any]:
        history = {
            player.name: history.data
            for player, history in self._history.items()
        }
        return {
            "size": self.size,
            "num_players": self.num_players,
            "num_cells_per_turn": self.num_cells_per_turn,
            "num_cells_to_win": self.num_cells_to_win,
            "history": history,
        }

    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'GameState':
        state_dict["history"] = {
            name: CellStorage(buffer)
            for name, buffer in state_dict["history"].items()
        }
        return cls(**state_dict)

    def dump(self, path: PathLike) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        state_dict = self.as_dict()
        history = state_dict.pop("history")
        np.savez(path, **state_dict, **history)

    @classmethod
    def load(cls, path: PathLike) -> 'GameState':
        flat_dict = dict(np.load(path))
        state_dict = {
            "size": int(flat_dict.pop("size")),
            "num_players": int(flat_dict.pop("num_players")),
            "num_cells_per_turn": int(flat_dict.pop("num_cells_per_turn")),
            "num_cells_to_win": int(flat_dict.pop("num_cells_to_win"))
        }
        state_dict["history"] = flat_dict
        return cls.from_dict(state_dict)

    def generate_board(self) -> np.ndarray:
        board = np.zeros((self.size, self.size), np.int32)
        occupancy_count = np.zeros((self.size, self.size), np.int32)
        for player, history in self._history.items():
            rows, cols = history.rows_cols()
            board[rows, cols] = player.value
            occupancy_count[rows, cols] += 1

        # first turn
        board[self.size // 2, self.size // 2] = Player[self.num_players].first().value
        occupancy_count[self.size // 2, self.size // 2] += 1
        if (occupancy_count > 1).any():
            raise RuntimeError("Historical turns have intersection")

        return board

    def _validate_history(self) -> None:
        for _, history in self._history.items():
            if len(history) % self.num_cells_per_turn != 0:
                raise RuntimeError(
                    f"History length should be divisible by {self.num_cells_per_turn}"
                )
        num_turns = [
            len(self._history[player]) // self.num_cells_per_turn
            for player in Player[self.num_players]
        ]
        num_turns[0] += 1  # first turn

        index = 0
        for i, num in enumerate(num_turns):
            if num != num_turns[index]:
                if index == 0 and num == num_turns[index] - 1:
                    index = i
                else:
                    raise RuntimeError(f"Wrong number of turns: {num_turns}")
