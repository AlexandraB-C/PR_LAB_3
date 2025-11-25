import pytest
import asyncio
from src.board import Board


class TestBoardParsing:
    """Tests for board file parsing."""
    
    @pytest.mark.asyncio
    async def test_parse_from_file_simple(self):
        """Test parsing a simple board file."""
        board = await Board.parse_from_file('boards/ab.txt')
        assert board._rows == 5
        assert board._cols == 5
        board.check_rep()
    
    @pytest.mark.asyncio
    async def test_initial_board_state(self):
        """Test that all cards start face down."""
        board = await Board.parse_from_file('boards/ab.txt')
        state = board.get_board_state('player1')
        lines = state.strip().split('\n')
        assert lines[0] == '5x5'
        # All cards should be "down"
        for line in lines[1:]:
            assert line == 'down'


class TestRule1B:
    """Tests for Rule 1-B: Face down card turns face up and player controls it."""
    
    @pytest.mark.asyncio
    async def test_rule_1b_face_down_turns_face_up(self):
        """Rule 1-B: Flipping a face-down card turns it face up and player controls it."""
        board = await Board.parse_from_file('boards/ab.txt')
        # Verify card starts face down
        assert (0, 0) not in board._faces_up
        
        await board.flip_card('player1', 0, 0)
        
        # Card should now be face up and controlled
        assert (0, 0) in board._faces_up
        assert board._controllers[(0, 0)] == 'player1'
        assert (0, 0) in board._controls.get('player1', [])
        
        # Board state should show "my A"
        state = board.get_board_state('player1')
        lines = state.strip().split('\n')
        assert lines[1] == 'my A'  # First card in ab.txt is A
        
        board.check_rep()


class TestRule2D:
    """Tests for Rule 2-D: Matching cards - player keeps control of both."""
    
    @pytest.mark.asyncio
    async def test_rule_2d_matching_cards(self):
        """Rule 2-D: When two cards match, player keeps control of both."""
        board = await Board.parse_from_file('boards/ab.txt')
        # Flip first card (A at 0,0)
        await board.flip_card('player1', 0, 0)
        # Flip matching card (A at 0,4) - both are A
        await board.flip_card('player1', 0, 4)
        
        # Player should control both cards
        assert board._controllers[(0, 0)] == 'player1'
        assert board._controllers[(0, 4)] == 'player1'
        assert (0, 0) in board._controls.get('player1', [])
        assert (0, 4) in board._controls.get('player1', [])
        assert len(board._controls.get('player1', [])) == 2
        
        # Both cards should be face up
        assert (0, 0) in board._faces_up
        assert (0, 4) in board._faces_up
        
        board.check_rep()


class TestRule3A:
    """Tests for Rule 3-A: Remove matched cards on next flip."""
    
    @pytest.mark.asyncio
    async def test_rule_3a_remove_matched_cards(self):
        """Rule 3-A: Matched cards are removed when player flips a new first card."""
        board = await Board.parse_from_file('boards/ab.txt')
        # Match two cards (both A)
        await board.flip_card('player1', 0, 0)
        await board.flip_card('player1', 0, 4)  # Matching A card
        
        # Verify they're controlled
        assert len(board._controls.get('player1', [])) == 2
        
        # Flip a new first card (triggers cleanup)
        await board.flip_card('player1', 1, 0)
        
        # Matched cards should be removed
        assert board._grid[0][0] is None
        assert board._grid[0][4] is None
        assert (0, 0) not in board._faces_up
        assert (0, 4) not in board._faces_up
        assert (0, 0) not in board._controllers
        assert (0, 4) not in board._controllers
        assert (0, 0) not in board._controls.get('player1', [])
        assert (0, 4) not in board._controls.get('player1', [])
        
        board.check_rep()
