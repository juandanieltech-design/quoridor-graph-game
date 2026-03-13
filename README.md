# Quoridor Graph Game

Implementation of the board game **Quoridor** using graph theory concepts and search algorithms.  
This project models the game board as a graph and uses **Breadth-First Search (BFS)** to validate game rules and ensure that players always have a valid path to their goal.

The system supports multiple game modes including human players and CPU agents.

---

# Project Overview

Quoridor is a strategic board game played on a **9×9 grid** where players attempt to reach the opposite side of the board before their opponents.

On each turn a player may:

- Move their pawn to an adjacent cell
- Place a wall to block opponents

However, walls **cannot completely block a player's path to their goal**.  
To enforce this rule, the system validates each wall placement using **graph connectivity checks with BFS**.

The board is represented as a **graph** where:

- Nodes represent board cells
- Edges represent legal movements between adjacent cells
- Walls remove edges from the graph

---

# Algorithms and Concepts Used

This project integrates several core computer science concepts:

- Graph modeling
- Breadth-First Search (BFS)
- State representation
- Game rule validation
- Modular software architecture

BFS is used to:

- Validate wall placements
- Ensure that each player still has a valid path to their goal
- Evaluate movement possibilities across the board

---

# System Architecture

The system is organized using a modular structure:

```
core.py → Game logic and board representation  
player.py → Player strategies (human or CPU)  
interface.py → Graphical interface and event handling  
main.py → Application entry point and game orchestration  
```

This design separates:

- Game rules
- Player strategies
- User interface
- Game execution

making the system easier to maintain, extend and test.

---

# Game Modes

The implementation supports several configurations combining human and CPU players.

| Mode | Description |
|-----|-------------|
| HC | Human vs CPU |
| HH | Human vs Human |
| CC | CPU vs CPU |
| HCC | Human vs two CPU players |
| HCCC | Human vs three CPU players |
| CCC | Three CPU players |
| CCCC | Four CPU players |

The game dynamically builds the required player configuration depending on the selected mode.

---

# Features

- Graph-based board representation
- BFS path validation for rule enforcement
- Wall placement validation
- Multiple game modes
- Basic CPU agents
- Graphical interface

---

# How to Run

Clone the repository:

```
git clone https://github.com/juandanieltech-design/quoridor-graph-game.git
```

Navigate to the project directory:

```
cd quoridor-graph-game
```

Run the program:

```
python main.py
```

Then select the desired game mode from the interface.

---

# Possible Improvements

Future improvements could include:

- Minimax-based AI agents
- Monte Carlo Tree Search (MCTS)
- Heuristic path evaluation
- Stronger CPU strategies
- Online multiplayer support

---

# Technologies Used

- Python
- Graph algorithms
- Breadth-First Search (BFS)
- Tkinter (GUI)

---

# Author

Juan Daniel Vargas  
Engineering Student – Pontificia Universidad Javeriana  
Bogotá, Colombia
