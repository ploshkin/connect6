import enum
from typing import Dict, Optional


__all__ = [
    "BasePlayer",
    "Player",
]


class BasePlayer(enum.IntEnum):
    @classmethod
    def current(cls, num_turns: int) -> Optional['BasePlayer']:
        if len(cls) == 0:
            return None
        return cls(num_turns % len(cls) + 1)

    @classmethod
    def first(cls) -> 'BasePlayer':
        return cls.current(0)


_COLORS = [  # TODO: JSON / YAML as module importer
    "BLACK",
    "WHITE",
    "RED",
]


class _Registry(Dict[int, BasePlayer]):
    def __getitem__(self, num_players: int) -> BasePlayer:
        if num_players not in self:
            if num_players < 2 or num_players > len(_COLORS):
                message = f"Supported 2 to {len(_COLORS)} players, got {num_players}"
                raise RuntimeError(message)
            players = _COLORS[: num_players]
            self[num_players] = BasePlayer(f"Player{num_players}", players)
        return super().__getitem__(num_players)


Player = _Registry()
