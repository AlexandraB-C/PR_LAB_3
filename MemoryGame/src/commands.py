"""Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
Redistribution of original or derived work requires permission of course staff.
"""

from typing import Callable, Awaitable
from .board import Board


"""
String-based commands provided by the Memory Scramble game.

PS4 instructions: these are required functions.
You MUST NOT change the names, type signatures, or specs of these functions.
"""


async def look(board: Board, player_id: str) -> str:
    """
    looks at the current state of the board.

    args:
        board: a memory scramble board
        player_id: ID of player looking at the board
    returns:
        the state of the board from the perspective of player_id
    """
    return await board.look(player_id)


async def flip(board: Board, player_id: str, row: int, column: int) -> str:
    """
    tries to flip over a card on the board.
    if another player controls the card, waits until flip becomes possible or fails.

    args:
        board: a memory scramble board
        player_id: ID of player making the flip
        row: row number of card to flip
        column: column number of card to flip
    returns:
        the state of the board after the flip from the perspective of player_id
    raises:
        error if the flip operation fails
    """
    return await board.flip(player_id, row, column)


async def map_cards(board: Board, player_id: str, f: Callable[[str], Awaitable[str]]) -> str:
    """
    Modifies board by replacing every card with f(card), without affecting other state of the game.
    
    This operation must be able to interleave with other operations, so while a map() is in progress,
    other operations like look() and flip() should not throw an unexpected error or wait for the map() to finish.
    But the board must remain observably pairwise consistent for players: if two cards on the board match 
    each other at the start of a call to map(), then while that map() is in progress, it must not
    cause any player to observe a board state in which that pair of cards do not match.

    Two interleaving map() operations should not throw an unexpected error, or force each other to wait,
    or violate pairwise consistency, but the exact way they must interleave is not specified.

    f must be a mathematical function from cards to cards: 
    given some legal card `c`, f(c) should be a legal replacement card which is consistently 
    the same every time f(c) is called for that same `c`.
    
    Args:
        board: game board
        player_id: ID of player applying the map; 
                   must be a nonempty string of alphanumeric or underscore characters
        f: mathematical function from cards to cards
    Returns:
        the state of the board after the replacement from the perspective of player_id,
        in the format described in the ps4 handout
    """
    return await board.map(player_id, f)


async def watch(board: Board, player_id: str) -> str:
    """
    Watches the board for a change, waiting until any cards turn face up or face down, 
    are removed from the board, or change from one string to a different string.

    Args:
        board: a Memory Scramble board
        player_id: ID of player watching the board; 
                   must be a nonempty string of alphanumeric or underscore characters
    Returns:
        the updated state of the board from the perspective of player_id, in the 
        format described in the ps4 handout
    """
    return await board.watch(player_id)
