# Lab 3: Multiplayer Game - Memory Scramble

**Author:** Bujor-Cobili Alexandra

---

## 1. Project Structure

### Directory Contents

```
MemoryGame/
├── src/
│   ├── board.py          # Board ADT with AF, RI, flip logic
│   ├── commands.py       # Glue code for look and flip commands
│   ├── server.py         # Quart HTTP API server with routes
│   └── nah/              # Old TypeScript files
├── boards/
│   ├── ab.txt            # Sample 5x5 board with letters
│   ├── perfect.txt       # 3x3 rainbow/unicorn board
│   └── zoom.txt          # Another sample board
├── public/
│   └── index.html        # Web UI for playing the game
├── requirements.txt      # Python dependencies (Quart, Hypercorn, etc.)
├── .gitignore            # Git ignore for Python and old TS
└── README.md
```

**Commands to run setup:**
```bash
pip install -r requirements.txt
python src/server.py 3000 boards/ab.txt  # starts server on localhost:3000
```

---

## 2. Problem 1: Game Board ADT

### 2.1 Synchronous Implementation

The Board ADT is implemented in Python as a mutable class with synchronous methods. I used lists and dictionaries for the internal rep: grid as list of lists for card positions (None for removed), controls as dict player to list of (row,col) pos, faces_up as set of visible pos, controllers as dict (r,c) to controlling player.

Rep invariants were added as comments in the class, with check_rep() enforcing dim constraints, card validity, no duplicate controls, face up positions having controllers. Safety from rep exposure: private fields, only mutators change rep, no direct client access.

parseFromFile static method reads board files with aiofiles, splits lines, creates grid with cards. All 11 game rules (1A-D, 2A-E, 3A-B) implemented in synchronous flip_card: cleanup on new move, check if empty or controlled, turn face up, assign control, match check.

Issues: cleanup holds removed cards first, then on next move removes them. Match keeps both cards under control until next move. Mismatch keeps cards face up without control until next move turns them down.

Remarks: Simple sequential play works for single player, observable consistent card states.

**Commands to test Problem 1:**
```bash
python src/server.py 3000 boards/perfect.txt
# open localhost:3000, play! button, click squares to see synchronous flip rules
```

**Remarks:** Synchronous version matches original sequential rules, no waits since no concurrent players.

---

## 2. Problem 2: Connect to the Web Server

### 2.2 HTTP API Implementation

The Quart server runs on Hypercorn with routes for look/get player board state, flip/get flip card result. commands.py provides simple glue: async def look, flip calling board methods directly, no logic.

Board state output uses line-separated format: 3x3\ncard1\ncard2\n... as none/down/up MY CARD/my MY CARD.

Issues: Server uses asyncio.Lock in flip for thread safety, GET routes non-blocking.

Remarks: Only look and flip implemented here, map and watch for problems 4-5.

**Commands to test Problem 2:**
```bash
python src/server.py 3000 boards/perfect.txt
# open multiple tabs for sequential play, each flips as 'single' player
```

---

## 3. Problem 3: Concurrent Players

### 3.1 Asynchronous Implementation

Board flip_card revised to async with asyncio for concurrency. Added _waiting_events dict (pos to list of Events) for Rule 1-D waiting. When card controlled by other, create Event, add to pos waiters, await event outside lock (non-blocking).

On cleanup (relinquish control), set all waiting Events for freed pos, clear list. Retry self.flip_card after wait.

Uses asyncio.Lock for critical sections.

Issues: Potential retry loop if multiple waits, but rare. No deadlocks as await outside lock, lock re-acquired after wait. Events shared across flip calls via self dict.

Remarks: Multiple players can now wait for controlled cards, thread-safe board state, no race conditions.

### 3.2 Concurrent Testing

Testing concurrent play: in multiple browser tabs (Chrome), each with unique player ID, try to flip same card. First gets control, others await silently until it frees (remove or turn down on next move).

Remarks: Polling mode in UI shows delayed updates, but concurrent access works. No crash under simultaneous requests, board stays consistent.

**Commands to test Problem 3:**
```bash
python src/server.py 3000 boards/perfect.txt
# open 3 browser tabs to localhost:3000, enter player1, player2, player3
# player1 clicks card1 (gets up my CARD), player2/player3 click same card1 → wait silently
# player1 clicks card2 (if match remove both, frees card1; waiting players proceed)
```

**Screenshot placeholder 1:** Browser tabs showing waiting behavior
```
![Screenshot of 3 browser tabs, one with "my card1", others pending on same card](img/concurrent_tabs.png)
```

**Screenshot placeholder 2:** Terminal server logs showing concurrent flips
```
![Server logs with async flips, Events set on free](img/server_concurrent_logs.png)
```

**What ifs and examples:**
- If player controlling dies/killed, waiting players hang: solve with timeouts on Events (set after 30s).
- If multiple waiting for same card, all get set on free, first proceeds others retry fail.
- Board state updates correctly even with waits, no inconsistency observed.

---
