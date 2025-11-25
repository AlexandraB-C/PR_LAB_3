"""Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
"""

import pytest
import asyncio
from src.board import Board


class TestConcurrentPlayers:
    @pytest.mark.asyncio
    async def test_waiting_for_controlled_card(self):
        board = await Board.parse_from_file('boards/ab.txt')
        await board.flip_card('player1', 0, 0)

        async def player2_flip():
            await board.flip_card('player2', 0, 0)
            return True

        task = asyncio.create_task(player2_flip())
        await asyncio.sleep(0.01)
        assert not task.done()

        await board.flip_card('player1', 0, 1)
        await board.flip_card('player1', 1, 0)
        await task
        assert board._controllers[0][0] == 'player2'

    @pytest.mark.asyncio
    async def test_multiple_players_wait_for_same_card(self):
        board = await Board.parse_from_file('boards/ab.txt')
        await board.flip_card('player1', 0, 0)

        async def player2_flip():
            await board.flip_card('player2', 0, 0)

        async def player3_flip():
            await board.flip_card('player3', 0, 0)

        task2 = asyncio.create_task(player2_flip())
        task3 = asyncio.create_task(player3_flip())
        await asyncio.sleep(0.01)

        await board.flip_card('player1', 0, 1)
        await asyncio.sleep(0.05)

        await board.flip_card('player1', 1, 0)
        await asyncio.sleep(0.1)

        if task2.done():
            assert board._controllers[0][0] == 'player2'
        else:
            await task2
            assert board._controllers[0][0] == 'player2'

    @pytest.mark.asyncio
    async def test_concurrent_players_flip_different_cards(self):
        board = await Board.parse_from_file('boards/ab.txt')

        async def player1():
            await board.flip_card('player1', 0, 0)

        async def player2():
            await board.flip_card('player2', 0, 4)

        await asyncio.gather(player1(), player2())
        assert board._controllers[0][0] == 'player1'
        assert board._controllers[0][4] == 'player2'
