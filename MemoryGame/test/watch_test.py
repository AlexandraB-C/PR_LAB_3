"""Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
"""

import pytest
import asyncio
from src.board import Board


class TestWatchFunction:
    @pytest.mark.asyncio
    async def test_watch_detects_card_turned_face_up(self):
        board = await Board.parse_from_file('boards/ab.txt')

        async def do():
            task = asyncio.create_task(board.watch_for_change())
            await asyncio.sleep(0.01)
            await board.flip_card('player1', 0, 0)
            await task

        await asyncio.wait_for(do(), timeout=1.0)

    @pytest.mark.asyncio
    async def test_watch_detects_card_removed(self):
        board = await Board.parse_from_file('boards/ab.txt')

        async def do():
            task = asyncio.create_task(board.watch_for_change())
            await asyncio.sleep(0.01)
            await board.flip_card('player1', 0, 0)
            await board.flip_card('player1', 0, 4)
            await board.flip_card('player1', 1, 0)
            await task

        await asyncio.wait_for(do(), timeout=1.0)

    @pytest.mark.asyncio
    async def test_watch_does_not_detect_failed_operations(self):
        board = await Board.parse_from_file('boards/ab.txt')
        # remove a card to create empty space
        board._cards[0][0] = None

        async def do():
            task = asyncio.create_task(board.watch_for_change())
            await asyncio.sleep(0.01)
            # failed operation: flip empty space
            try:
                await board.flip_card('player1', 0, 0)
            except ValueError:
                pass  # expected failure
            await asyncio.wait_for(task, timeout=0.5)

        with pytest.raises(asyncio.TimeoutError):
            await do()
