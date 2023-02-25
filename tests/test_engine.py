import itertools
import math
import tempfile
from pathlib import Path

import numpy as np
import pytest

from connect6.game import GameEngine, Player, TurnData, common, errors
from connect6.game.state import GameState
from connect6.game.storage import CellStorage


@pytest.mark.parametrize("row", [0, 1, 1000])
@pytest.mark.parametrize("col", [0, 1, 1000])
def test_cell_interface(row, col):
    cell = common.Cell(row, col)
    assert cell.as_tuple() == (row, col)

    if row > 0:
        with pytest.raises(errors.NegativeCellCoordinateError):
            common.Cell(-row, col)

    if col > 0:
        with pytest.raises(errors.NegativeCellCoordinateError):
            common.Cell(row, -col)

    if row > 0 or col > 0:
        with pytest.raises(errors.NegativeCellCoordinateError):
            common.Cell(-row, -col)


@pytest.mark.parametrize("length", [10, 100, 1000])
def test_cell_storage_interface(length):
    history = CellStorage()
    assert len(history) == 0

    for idx in range(length):
        history.add(common.Cell(idx * 2, idx * 2 + 1))

    assert len(history) == length
    assert (history.data == np.arange(length * 2).reshape((-1, 2))).all()

    rows, cols = history.rows_cols()
    indices = np.arange(len(history) * 2)
    assert (rows == indices[::2]).all()
    assert (cols == indices[1::2]).all()


@pytest.mark.parametrize("length", [10, 100, 1000])
def test_cell_storage_valid_restore(length):
    valid_data = np.arange(length * 2).reshape((-1, 2))
    history = CellStorage(valid_data)
    assert (history.data == valid_data).all()


@pytest.mark.parametrize("shape", [(10,), (10, 2, 2), (15, 3)])
def test_cell_storage_invalid_shape(shape):
    length = math.prod(shape)
    data = np.arange(length).reshape(shape)
    with pytest.raises(errors.WrongBufferShapeError):
        CellStorage(data)


@pytest.mark.parametrize("length", [10, 100, 1000])
def test_cell_storage_negative_values(length):
    data = np.arange(length * 2).reshape((length, 2))
    with pytest.raises(ValueError):
        CellStorage(-data)
    data[-1] = (0, -1)
    with pytest.raises(ValueError):
        CellStorage(-data)


@pytest.mark.parametrize("num_players", [2, 3])
def test_valid_player(num_players):
    assert len(Player[num_players]) == num_players
    for index, player in enumerate(Player[num_players], start=1):
        assert player.value == index

    assert Player[num_players].first().value == 1

    # After the 1st turn was made current player should have index = 2
    assert Player[num_players].current(1).value == 2

    players = itertools.cycle(range(1, num_players + 1))
    for turn, player in zip(range(100), players):
        assert Player[num_players].current(turn).value == player


@pytest.mark.parametrize("num_players", [-1, 0, 1, 100])
def test_invalid_num_players(num_players):
    with pytest.raises(RuntimeError):
        Player[num_players]


@pytest.mark.parametrize("num_cells_per_turn", [1, 2, 3, 10])
def test_valid_turn_data(num_cells_per_turn):
    player = Player[2].first()
    cells = [common.Cell(i * 2, i * 2 + 1) for i in range(num_cells_per_turn)]

    data = TurnData[num_cells_per_turn](player, cells)
    assert data.player is player
    assert len(data.cells) == num_cells_per_turn
    for data_cell, cell in zip(data.cells, cells):
        assert data_cell == cell


@pytest.mark.parametrize("num_cells_per_turn", [0, -1])
def test_turn_data_wrong_num_cells_per_turn(num_cells_per_turn):
    with pytest.raises(RuntimeError):
        TurnData[num_cells_per_turn]


@pytest.mark.parametrize(
    "actual, expected",
    [(1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2), (5, 10)],
)
def test_turn_data_invalid_num_cells_per_turn(actual, expected):
    player = Player[2].first()
    cells = [common.Cell(i * 2, i * 2 + 1) for i in range(actual)]
    with pytest.raises(RuntimeError):
        TurnData[expected](player, cells)


@pytest.mark.parametrize("num_cells_per_turn", [1, 2, 3, 10])
def test_turn_data_equal_cells(num_cells_per_turn):
    player = Player[2].first()
    if num_cells_per_turn == 1:
        TurnData[num_cells_per_turn](player, [common.Cell(0, 0)])
    else:
        cells = [common.Cell(i * 2, i * 2 + 1) for i in range(num_cells_per_turn - 1)]
        cells.append(cells[0])
        with pytest.raises(errors.EqualCellsInTurnError):
            TurnData[num_cells_per_turn](player, cells)


def test_max_segment_length():
    array = [0 for _ in range(10)]
    assert common.max_segment_length(array, 0) == 10
    assert common.max_segment_length(array, 1) == 0
    assert common.max_segment_length(array, -1) == 0

    array = list(range(100))
    for value in array:
        assert common.max_segment_length(array, value) == 1

    array = [k // 2 for k in range(100)]
    for value in range(50):
        assert common.max_segment_length(array, value) == 2

    array = [3, 3, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 2, 0, 4, 4, 4]
    assert common.max_segment_length(array, 0) == 4
    assert common.max_segment_length(array, 1) == 3
    assert common.max_segment_length(array, 2) == 1
    assert common.max_segment_length(array, 3) == 2
    assert common.max_segment_length(array, 4) == 3
    assert common.max_segment_length(array, 5) == 0


@pytest.mark.parametrize("size", [15, 19])
@pytest.mark.parametrize("num_players", [2, 3])
@pytest.mark.parametrize("num_cells_per_turn", [1, 2, 3, 10])
@pytest.mark.parametrize("num_cells_to_win", [5, 6])
def test_state_interface(size, num_players, num_cells_per_turn, num_cells_to_win):
    state = GameState(size, num_players, num_cells_per_turn, num_cells_to_win)
    assert state.num_players == num_players
    assert state.num_cells_per_turn == num_cells_per_turn
    assert state.num_cells_to_win == num_cells_to_win
    assert state.num_turns == 1

    board = state.generate_board()
    assert board.shape[:2] == (size, size)
    assert board[size // 2, size // 2] == Player[num_players].first().value
    board[size // 2, size // 2] = 0
    assert (board == 0).all()

    player1 = Player[num_players].current(1)
    cells1 = [common.Cell(i, i + 1) for i in range(num_cells_per_turn)]
    data1 = TurnData[num_cells_per_turn](player1, cells1)
    state.turn(data1)
    assert state.num_turns == 2

    board = state.generate_board()
    assert (board != 0).sum() == num_cells_per_turn + 1
    assert (board == player1.value).sum() == num_cells_per_turn

    player2 = Player[num_players].current(2)
    cells2 = [common.Cell(i + 1, i) for i in range(num_cells_per_turn)]
    data2 = TurnData[num_cells_per_turn](player2, cells2)
    state.turn(data2)
    assert state.num_turns == 3

    board = state.generate_board()
    assert (board != 0).sum() == num_cells_per_turn * 2 + 1
    assert (board == player1.value).sum() == num_cells_per_turn
    if player2 is Player[num_players].first():
        assert (board == player2.value).sum() == num_cells_per_turn + 1
    else:
        assert (board == player2.value).sum() == num_cells_per_turn

    state_from_dict = GameState.from_dict(state.as_dict())
    assert state_from_dict.num_players == state.num_players
    assert state_from_dict.num_cells_per_turn == state.num_cells_per_turn
    assert state_from_dict.num_cells_to_win == state.num_cells_to_win
    assert state_from_dict.num_turns == state.num_turns

    board_from_dict = state_from_dict.generate_board()
    assert (board_from_dict == board).all()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.npz"
        state.dump(path)
        restored_state = GameState.load(path)

    assert restored_state.num_players == state.num_players
    assert restored_state.num_cells_per_turn == state.num_cells_per_turn
    assert restored_state.num_cells_to_win == state.num_cells_to_win
    assert restored_state.num_turns == state.num_turns

    restored_board = restored_state.generate_board()
    assert (restored_board == board).all()


def test_state_generate_board_fail():
    state_dict = {
        "size": 15,
        "num_players": 2,
        "num_cells_per_turn": 2,
        "num_cells_to_win": 6,
    }
    first_turn = (state_dict["size"] // 2, state_dict["size"] // 2)
    intersected_histories = [
        {
            Player[2](1).name: np.array([(0, 0), (1, 1)], dtype=np.int32),
            Player[2](2).name: np.array([(5, 5), (0, 0)], dtype=np.int32),
        },
        {
            Player[2](1).name: np.array([(0, 0), (1, 1)], dtype=np.int32),
            Player[2](2).name: np.array([(5, 5), first_turn], dtype=np.int32),
        },
    ]
    for history in intersected_histories:
        state_dict.update(history=history)
        state = GameState.from_dict(state_dict)
        with pytest.raises(RuntimeError):
            state.generate_board()


@pytest.mark.parametrize(
    "num_players, num_cells_per_turn, lengths",
    [
        (2, 2, [1, 2]),
        (2, 2, [100, 101]),
        (2, 2, [10, 6]),
        (3, 2, [2, 0, 2]),
        (3, 2, [4, 2, 0]),
        (3, 3, [4, 3, 3]),
    ],
)
def test_state_bad_history_lengths(num_players, num_cells_per_turn, lengths):
    state_dict = {
        "size": 15,
        "num_players": num_players,
        "num_cells_per_turn": num_cells_per_turn,
        "num_cells_to_win": 6,
        "history": {
            player.name: np.zeros((length, 2), np.int32)
            for player, length in zip(Player[num_players], lengths)
        },
    }
    with pytest.raises(RuntimeError):
        GameState.from_dict(state_dict)


@pytest.mark.parametrize("restore_turn", range(1, 28))
def test_valid_gomoku_game(restore_turn):
    gomoku = GameEngine(
        size=15,
        num_players=2,
        num_cells_per_turn=1,
        num_cells_to_win=5,
    )
    assert gomoku.max_num_turns == 15**2
    assert gomoku.current_player is Player[2].current(1)
    assert gomoku.is_occupied(common.Cell(7, 7))
    assert not gomoku.is_occupied(common.Cell(0, 0))

    # fmt: off
    turns = [
        (6, 7), (6, 8), (8, 6), (7, 8), (8, 8), (8, 7), (7, 6), (9, 6), (6, 9), (7, 9),
        (5, 8), (8, 5), (5, 6), (7, 10), (7, 11), (5, 7), (4, 6), (6, 6), (4, 7),
        (7, 5), (4, 8), (8, 4), (9, 3), (10, 5), (11, 4), (9, 5), (6, 5), (11, 5),
    ]
    # fmt: on
    turn_generator = enumerate(turns, start=1)

    winner = None
    while gomoku.state.num_turns < gomoku.max_num_turns:
        if gomoku.state.num_turns == restore_turn:
            state = gomoku.state
            del gomoku
            gomoku = GameEngine.restore(state)
            assert gomoku.state.num_turns == restore_turn

        num_turns, (row, col) = next(turn_generator)
        current = Player[2].current(num_turns)
        data = TurnData[1](current, [common.Cell(row, col)])
        gomoku.turn(data)
        if gomoku.is_win(data):
            winner = data.player
            break

    assert winner is Player[2].first()
    assert gomoku.state.num_turns == len(turns) + 1


@pytest.mark.parametrize("restore_turn", range(1, 9))
def test_valid_connect6_game(restore_turn):
    connect6 = GameEngine(
        size=19,
        num_players=2,
        num_cells_per_turn=2,
        num_cells_to_win=6,
    )
    assert connect6.is_occupied(common.Cell(9, 9))

    # fmt: off
    turns = [
        [(9, 8), (8, 9)], [(8, 10), (7, 10)],
        [(9, 10), (10, 9)], [(7, 9), (7, 8)],
        [(7, 7), (8, 7)], [(7, 11), (7, 12)],
        [(7, 13), (7, 6)], [(6, 12), (11, 10)],
        [(5, 4), (6, 5)],
    ]
    # fmt: on
    turn_generator = enumerate(turns, start=1)

    winner = None
    while connect6.state.num_turns < connect6.max_num_turns:
        if connect6.state.num_turns == restore_turn:
            state = connect6.state
            del connect6
            connect6 = GameEngine.restore(state)
            assert connect6.state.num_turns == restore_turn

        num_turns, (first, second) = next(turn_generator)
        current = Player[2].current(num_turns)
        data = TurnData[2](current, [common.Cell(*first), common.Cell(*second)])
        connect6.turn(data)
        if connect6.is_win(data):
            winner = data.player
            break

    assert winner is Player[2](2)
    assert connect6.state.num_turns == len(turns) + 1
