import asyncio
import aiofiles
from typing import List, Dict, Set, Tuple, Optional


class Board:
    # rep invariant: grid != [] and card != "" if not None, faces_up have controllers, etc.
    # abstraction function: AF(cols, rows, grid, faces_up, controllers, controls) = memory scramble board with same cards, face state, ownership
    # safety from rep exposure: only constructors and mutators change rep, no direct access
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


    def __str__(self) -> str:
        return self.get_board_state("")

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
        assert 0 <= row < self._rows and 0 <= col < self._cols

        pos = (row, col)
        async with self._lock:
            player_controls = self._controls.get(player_id, [])

            # cleanup previous play if exists
            if len(player_controls) >= 2:
                # had matching pair, remove them
                for p in player_controls:
                    self._grid[p[0]][p[1]] = None
                    del self._controllers[p]
                self._faces_up -= set(player_controls)
                self._controls[player_id] = []
                player_controls = []
            if len(player_controls) == 1:
                # had mismatched, turn down if uncontrolled
                p = player_controls[0]
                if p in self._faces_up and self._controllers.get(p) != player_id:
                    self._faces_up.remove(p)
                    del self._controllers[p]
                self._controls[player_id] = []
                player_controls = []

            # now check the flip
            if self._grid[row][col] is None:
                raise ValueError("cannot flip: no card")  # 1A

            is_face_up = pos in self._faces_up
            controller = self._controllers.get(pos)

            if len(player_controls) == 0:  # first card
                if is_face_up and controller is not None and controller != player_id:
                    raise ValueError("cannot flip: controlled by other player")  # 1D
                # rules 1B and 1C: turn face up and control
                if not is_face_up:
                    self._faces_up.add(pos)
                self._controllers[pos] = player_id
                self._controls[player_id] = [pos]
            elif len(player_controls) == 1:  # second card
                if self._grid[row][col] is None:
                    raise ValueError("cannot flip: no card")  # 2A
                if is_face_up and controller is not None:
                    raise ValueError("cannot flip: controlled card")  # 2B
                # rules 2C: turn up if down
                if not is_face_up:
                    self._faces_up.add(pos)
                self._controllers[pos] = player_id
                # check if match
                first_pos = player_controls[0]
                first_card = self._grid[first_pos[0]][first_pos[1]]
                card = self._grid[row][col]
                if first_card == card:
                    player_controls.append(pos)  # keep control
                    self._controls[player_id] = player_controls
                else:
                    self._controls[player_id] = [first_pos, pos]  # keep for cleanup
            else:
                raise ValueError("unexpected controls count")

            self.check_rep()
            return self.get_board_state(player_id)
