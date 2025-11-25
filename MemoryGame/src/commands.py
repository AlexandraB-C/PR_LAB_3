from typing import Callable, Awaitable
from board import Board


async def look(board: Board, player_id: str) -> str:
    return await board.look(player_id)


async def flip(board: Board, player_id: str, row: int, col: int) -> str:
    return await board.flip(player_id, row, col)


async def map_cards(board: Board, player_id: str, f: Callable[[str], Awaitable[str]]) -> str:
    return await board.map(player_id, f)


async def watch(board: Board, player_id: str) -> str:
    return await board.watch(player_id)
