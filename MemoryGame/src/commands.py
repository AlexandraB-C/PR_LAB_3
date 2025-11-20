from board import Board


async def look(board: Board, player_id: str) -> str:
    return board.get_board_state(player_id)


async def flip(board: Board, player_id: str, row: int, col: int) -> str:
    return await board.flip_card(player_id, row, col)
