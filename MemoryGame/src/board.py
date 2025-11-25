import asyncio
import aiofiles
import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


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
        self._previous_moves: Dict[str, Optional[Tuple[List[Tuple[int, int]], bool]]] = {}  # cleanup tracking
        self._waiting_players: Dict[Tuple[int, int], List[asyncio.Event]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._map_locks: Dict[str, asyncio.Lock] = {}
        self._change_watchers: List[asyncio.Event] = []
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
        # retry loop for waiting
        while True:
            event_to_wait = None
            async with self._lock:
                # cleanup previous moves
                if player_id in self._previous_moves and self._previous_moves[player_id] is not None:
                    prev_cards, prev_matched = self._previous_moves[player_id]
                    if prev_matched:
                        # remove matched cards
                        for p in prev_cards:
                            if 0 <= p[0] < self._rows and 0 <= p[1] < self._cols and self._grid[p[0]][p[1]] is not None:
                                self._grid[p[0]][p[1]] = None
                                self._faces_up.discard(p)
                                self._controllers.pop(p, None)
                                self._notify_waiting_players(p)
                                self._notify_change_watchers()
                        # remove from player controls
                        if player_id in self._controls and all(p in prev_cards for p in self._controls[player_id]):
                            self._controls[player_id] = []
                    else:
                        # turn down uncontrolled cards
                        for p in prev_cards:
                            if (0 <= p[0] < self._rows and 0 <= p[1] < self._cols and
                                self._grid[p[0]][p[1]] is not None and p in self._faces_up and
                                self._controllers.get(p) is None):
                                self._faces_up.remove(p)
                                self._notify_waiting_players(p)
                                self._notify_change_watchers()
                    self._previous_moves[player_id] = None
                    # clean up player controls if empty
                    if player_id in self._controls and not self._controls[player_id]:
                        del self._controls[player_id]

                # check if card still exists after cleanup
                if self._grid[row][col] is None:
                    if self._controls.get(player_id, []):
                        # player had controls, relinquish them for cleanup on next flip
                        first_pos = self._controls[player_id][0]
                        self._relinquish_control(player_id, first_pos[0], first_pos[1])
                        self._previous_moves[player_id] = ([first_pos], False)
                        self._notify_waiting_players(first_pos)
                        raise ValueError("no card at position")
                    else:
                        raise ValueError("no card at position")

                player_controls = self._controls.get(player_id, [])
                pos = (row, col)
                is_face_up = pos in self._faces_up
                controller = self._controllers.get(pos)

                if len(player_controls) == 0:  # first card flip
                    if controller is not None and controller != player_id:
                        # wait for card to be available
                        wait_event = asyncio.Event()
                        self._waiting_players[pos].append(wait_event)
                        event_to_wait = wait_event
                    else:
                        # can flip now
                        if not is_face_up:
                            self._faces_up.add(pos)
                            self._notify_change_watchers()
                        self._controllers[pos] = player_id
                        if player_id not in self._controls:
                            self._controls[player_id] = []
                        self._controls[player_id].append(pos)
                        self._notify_waiting_players(pos)
                        self._previous_moves[player_id] = None
                        self.check_rep()
                        return self.get_board_state(player_id)

                elif len(player_controls) == 1:  # second card flip
                    if self._grid[row][col] is None:
                        # relinquish first card
                        first_pos = player_controls[0]
                        self._relinquish_control(player_id, first_pos[0], first_pos[1])
                        self._previous_moves[player_id] = ([first_pos], False)
                        self._notify_waiting_players(first_pos)
                        raise ValueError("no card at position")
                    if is_face_up and controller is not None:
                        # relinquish first card
                        first_pos = player_controls[0]
                        self._relinquish_control(player_id, first_pos[0], first_pos[1])
                        self._previous_moves[player_id] = ([first_pos], False)
                        self._notify_waiting_players(first_pos)
                        raise ValueError("controlled card")
                    # flip second card
                    if not is_face_up:
                        self._faces_up.add(pos)
                        self._notify_change_watchers()
                    self._controllers[pos] = player_id
                    self._controls[player_id].append(pos)
                    # check match
                    first_pos = player_controls[0]
                    first_card = self._grid[first_pos[0]][first_pos[1]]
                    second_card = self._grid[row][col]
                    if first_card == second_card:
                        self._previous_moves[player_id] = ([first_pos, pos], True)
                    else:
                        self._previous_moves[player_id] = ([first_pos, pos], False)
                    self._notify_waiting_players(pos)
                    self.check_rep()
                    return self.get_board_state(player_id)
                else:
                    raise ValueError("invalid player controls")

            # wait outside lock if needed
            if event_to_wait is not None:
                await event_to_wait.wait()
            else:
                break

    def _notify_waiting_players(self, pos: Tuple[int, int]) -> None:
        if pos in self._waiting_players:
            events = self._waiting_players[pos]
            for event in events:
                event.set()
            self._waiting_players[pos].clear()
            if not events:
                del self._waiting_players[pos]

    def _notify_change_watchers(self) -> None:
        events = self._change_watchers[:]
        self._change_watchers.clear()
        for event in events:
            event.set()

    async def watch_for_change(self) -> None:
        event = asyncio.Event()
        async with self._lock:
            self._change_watchers.append(event)
        await event.wait()

    def _relinquish_control(self, player_id: str, row: int, col: int) -> None:
        pos = (row, col)
        if self._controllers.get(pos) == player_id:
            self._controllers[pos] = None
            if player_id in self._controls and pos in self._controls[player_id]:
                self._controls[player_id].remove(pos)
                if not self._controls[player_id]:
                    del self._controls[player_id]

    async def look(self, player_id: str) -> str:
        return self.get_board_state(player_id)

    async def flip(self, player_id: str, row: int, col: int) -> str:
        return await self.flip_card(player_id, row, col)

    async def watch(self, player_id: str) -> str:
        await self.watch_for_change()
        return self.get_board_state(player_id)

    async def map_cards(self, player_id: str, f) -> None:
        # collect unique cards
        card_positions = {}
        async with self._lock:
            for r in range(self._rows):
                for c in range(self._cols):
                    if self._grid[r][c] is not None:
                        card = self._grid[r][c]
                        if card not in card_positions:
                            card_positions[card] = []
                        card_positions[card].append((r, c))

        # process each unique card
        for card, positions in card_positions.items():
            if card not in self._map_locks:
                async with self._lock:
                    if card not in self._map_locks:
                        self._map_locks[card] = asyncio.Lock()
            async with self._map_locks[card]:
                new_card = await f(card)
                changes_made = False
                async with self._lock:
                    for r, c in positions:
                        if (0 <= r < self._rows and 0 <= c < self._cols and
                            self._grid[r][c] == card):
                            self._grid[r][c] = new_card
                            changes_made = True
                    if changes_made and new_card != card:
                        self._notify_change_watchers()
                    if new_card not in self._map_locks:
                        self._map_locks[new_card] = asyncio.Lock()
        async with self._lock:
            self.check_rep()

    def get_rows(self) -> int:
        return self._rows

    def get_columns(self) -> int:
        return self._cols

    async def map(self, player_id: str, f) -> str:
        await self.map_cards(player_id, f)
        return self.get_board_state(player_id)
