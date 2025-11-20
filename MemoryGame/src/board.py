import asyncio
import aiofiles
from typing import List, Dict, Set, Tuple, Optional


class Board:
    def __init__(self, grid: List[List[str]]) -> None:
        self._rows = len(grid)
        self._cols = len(grid[0]) if grid else 0
        self._grid = grid  # list of lists of card str, or None for empty
        self._controls: Dict[str, List[Tuple[int, int]]] = {}  # player -> list of (r,c)
        self._faces_up: Set[Tuple[int, int]] = set()  # set of face up positions
        self._controllers: Dict[Tuple[int, int], Optional[str]] = {}  # (r,c) -> player controlling or None
        self._lock = asyncio.Lock()
        self.check_rep()

    @staticmethod
    async def parse_from_file(filename: str) -> 'Board':
        async with aiofiles.open(filename, 'r') as f:
            lines = [line.rstrip('\n\r') for line in await f.readlines() if line.strip()]

        dims = lines[0].split('x')
        rows, cols = int(dims[0]), int(dims[1])
        cards = [line for line in lines[1:] if line]

        if len(cards) != rows * cols:
            raise ValueError("mismatch in card count")

        grid = [[None for _ in range(cols)] for _ in range(rows)]  # None for empty
        idx = 0
        for r in range(rows):
            for c in range(cols):
                grid[r][c] = cards[idx]
                idx += 1

        return Board(grid)

    def check_rep(self) -> None:
        # grid dimensions
        assert len(self._grid) == self._rows
        for row in self._grid:
            assert len(row) == self._cols
        # cards are valid
        for r in range(self._rows):
            for c in range(self._cols):
                card = self._grid[r][c]
                assert card is None or isinstance(card, str) and card
        # controls consistency
        controlled = set()
        for player, positions in self._controls.items():
            for pos in positions:
                assert pos not in controlled, "card controlled by multiple players"
                controlled.add(pos)
                assert self._controllers.get(pos) == player
        # faces up and controllers
        for pos in self._faces_up:
            assert pos in self._controllers
            assert self._grid[pos[0]][pos[1]] is not None
        # all controllers are non-none if faces up
        for pos, player in self._controllers.items():
            if pos in self._faces_up:
                assert player is not None

    def get_board_state(self, player_id: str) -> str:
        result = [f"{self._rows}x{self._cols}"]
        for r in range(self._rows):
            for c in range(self._cols):
                pos = (r, c)
                if self._grid[r][c] is None:
                    result.append("none")
                elif pos not in self._faces_up:
                    result.append("down")
                else:
                    card = self._grid[r][c]
                    controller = self._controllers[pos]
                    if controller == player_id:
                        result.append(f"my {card}")
                    else:
                        result.append(f"up {card}")
        return '\n'.join(result)

    async def flip_card(self, player_id: str, row: int, col: int) -> str:
        assert 0 <= row < self._rows and 0 <= col < self._cols, "invalid position"

        pos = (row, col)
        async with self._lock:
            if self._grid[row][col] is None:
                raise ValueError("no card there")

            # get current controls for player
            current_controls = self._controls.get(player_id, [])

            # rule 1a: empty space fails
            if self._grid[row][col] is None:
                raise ValueError("cannot flip: no card")

            card = self._grid[row][col]

            # is face up?
            is_face_up = pos in self._faces_up
            controller = self._controllers.get(pos)

            # waiting never happens in sync
            if not is_face_up:
                # rule 1b: down -> up, control
                self._faces_up.add(pos)
                self._controllers[pos] = player_id
                current_controls.append(pos)
                self._controls[player_id] = current_controls
            elif controller == player_id:
                # rule 1c: up, controlled by self -> remains
                pass
            elif controller is not None:
                # rule 1d: controlled by other -> wait, but sync can't wait, so fail
                raise ValueError("cannot flip: controlled by other player")

            self.check_rep()
            return self.get_board_state(player_id)
