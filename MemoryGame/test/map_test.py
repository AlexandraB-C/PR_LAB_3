"""Copyright (c) 2021-25 MIT 6.102/6.031 course staff, all rights reserved.
"""

import pytest
import asyncio
from src.board import Board


async def identity(x):
    return x


async def double_card(card):
    return card * 2


class TestMapCards:
    @pytest.mark.asyncio
    async def test_map_simple_replacement(self):
        board = await Board.parse_from_file('boards/ab.txt')
        await board.map_cards('player1', identity)
        assert board._cards[0][0] == 'A'  # unchanged

    @pytest.mark.asyncio
    async def test_map_preserves_pairwise_consistency(self):
        board = await Board.parse_from_file('boards/ab.txt')
        await board.map_cards('player1', identity)
        assert board._cards[0][0] == 'A'
        assert board._cards[0][4] == 'A'  # both A cards become the same

    @pytest.mark.asyncio
    async def test_map_does_not_affect_states(self):
        board = await Board.parse_from_file('boards/ab.txt')
        await board.flip_card('player1', 0, 0)
        await board.map_cards('player1', identity)
        assert board._face_up[0][0]
        assert board._controllers[0][0] == 'player1'
