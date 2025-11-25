import asyncio
import random
from .board import Board


async def simulation_main():
    """
    Simulate a multi-player Memory Scramble game.

    Requirements: 4 players, timeouts between 0.1ms and 2ms, 100 moves each.
    """
    board: Board = await Board.parse_from_file('boards/ab.txt')
    size = board.get_rows()
    players = 4  # Required: 4 players
    moves_per_player = 100  # Required: 100 moves each
    min_delay_ms = 0.1  # Required: minimum 0.1ms
    max_delay_ms = 2.0  # Required: maximum 2ms

    print(f'Starting simulation with {players} players, {moves_per_player} moves each')
    print(f'Board size: {size}x{size}')
    print(f'Delay range: {min_delay_ms}ms - {max_delay_ms}ms')

    player_tasks = []
    for ii in range(players):
        random.seed(ii * 42)
        player_tasks.append(player(ii, board, size, moves_per_player, min_delay_ms, max_delay_ms))

    try:
        movesets = await asyncio.gather(*player_tasks)
        print('\n' + '='*60)
        print('SIMULATION COMPLETED SUCCESSFULLY - NO CRASHES!')
        print('='*60)

        # Print movesets for each player
        print('\nMovesets for each player:')
        print('-'*60)
        for player_num, moveset in enumerate(movesets):
            print(f'\nPlayer {player_num} moveset ({len(moveset)} moves):')
            for move_idx, move in enumerate(moveset):
                (row1, col1), (row2, col2) = move
                print(f'  Move {move_idx + 1}: ({row1},{col1}) -> ({row2},{col2})')

        print('\n' + '='*60)
        board.check_rep()
    except Exception as err:
        print(f'Simulation failed with error: {err}')
        raise


async def player(player_number: int, board: Board, size: int, moves: int, min_delay_ms: float, max_delay_ms: float):
    """
    Simulate a player making moves.
    """
    player_id = f'player_{player_number}'
    moveset = []

    for move_num in range(moves):
        row1 = random_int(size)
        col1 = random_int(size)
        row2 = random_int(size)
        col2 = random_int(size)

        try:
            delay = min_delay_ms + random.random() * (max_delay_ms - min_delay_ms)
            await timeout(delay)

            await board.flip_card(player_id, row1, col1)

            delay = min_delay_ms + random.random() * (max_delay_ms - min_delay_ms)
            await timeout(delay)

            await board.flip_card(player_id, row2, col2)

        except (ValueError, IndexError):
            pass
        except Exception as err:
            print(f'Player {player_number} move {move_num} failed: {err}')
            raise

        moveset.append(((row1, col1), (row2, col2)))

    return moveset


def random_int(max_val: int) -> int:
    return random.randrange(0, max_val)


async def timeout(milliseconds: float):
    await asyncio.sleep(milliseconds / 1000.0)


if __name__ == '__main__':
    asyncio.run(simulation_main())
