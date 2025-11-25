# Memory Card Game

### Author: Bujor-Cobili Alexandra

## Game Rules

1. **Flipping Cards**: You flip cards, but if someone else is using a card, you wait
2. **Finding Pairs**: If cards match, you keep them; if not, you lose control
3. **Cleanup**: Matching cards disappear, non-matching cards flip back over

## Project Files

![alt text](img/structure.png)

## Implementation

### Running Tests

```bash
cd MemoryGame
python src/run_tests.py
```

Run ALL tests and shows a summary like:

![alt text](img/runall.png)

All passed WOW!!!!!!!

### One by One

#### 1. Basic Game Rules Test
```bash
python -m pytest test/board_test.py -v
```
This checks that basic card flipping, matching, and cleanup works correctly.

![alt text](img/board_test.png)

All the individual game rules like "when you flip a face-down card, it should turn face-up and you control it."

#### 2. Multi-Player Test
```bash
python -m pytest test/concurrent_test.py -v
```
This tests what happens when many players try to flip cards at the same time.

![alt text](img/conc.png)

Players wait properly for cards that are busy, and no crashes during concurrent play.

#### 3. Card Changing Test
```bash
python -m pytest test/map_test.py -v
```
This tests the "map" feature that changes card values during gameplay.

![alt text](img/map.png)

Cards change values atomically, and matching pairs stay matched even when changing.

#### 4. Watch/Notification Test
```bash
python -m pytest test/watch_test.py -v
```
This tests the watching feature that tells you when cards change.

![alt text](img/w.png)

You get notified when cards flip over, disappear, or change pictures, but not when someone just claims control.

#### 5. Simulation
```bash
cd MemoryGame
python -m src.simulation
```

This runs a simulation of 4 players each making 100 random moves.

**Expected Output:**
```
Starting simulation with 4 players, 100 moves each
Board size: 5x5
Delay range: 0.1ms - 2.0ms

============================================================
SIMULATION COMPLETED SUCCESSFULLY - NO CRASHES!
============================================================

Movesets for each player:
------------------------------------------------------------
Player 0 moveset (100 moves):
  Move 1: (2,1) -> (4,3)
  Move 2: (0,4) -> (1,2)
  [... 98 more moves ...]
```

It ran, its cool, we cool.


## Game in Browser

From the MemoryGame directory:

```bash
python -m src.server 8080 boards/ab.txt
```

This starts a web server on port 8080 with the A/B card board.

![alt text](img/1.png)

We select two cards from the right player, then the same A which player right choose, player left took it and another B.

![alt text](img/2.png)

Player A choose a randomn card, and because palyer A was first to go he\she has priority thus a the most A and B dissapeard.

![alt text](img/3.png)

Showcase of notification.

![alt text](img/4.png)

Further in the game + notification, if the same player selects the same card (like click twice and stuff)


