# quoridor/core.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List, Optional

Coord = Tuple[int, int]  # (fila, columna)

BOARD_N = 9
START_P1: Coord = (BOARD_N - 1, BOARD_N // 2)  # (8,4)
START_P2: Coord = (0, BOARD_N // 2)            # (0,4)
GOAL_P1 = 0
GOAL_P2 = BOARD_N - 1
WALLS_PER_PLAYER = 10


@dataclass(frozen=True)
class Wall:
    r: int
    c: int
    orientation: str  # 'H' o 'V'

    def in_bounds(self) -> bool:
        # ancla válido en rejilla 8x8 de muros
        return 0 <= self.r <= BOARD_N - 2 and 0 <= self.c <= BOARD_N - 2 and self.orientation in ("H", "V")

    def edges_blocked(self) -> List[Tuple[Coord, Coord]]:
        """Pares de celdas (aristas) que bloquea este muro en el grafo."""
        if self.orientation == "H":
            # Bloquea dos bordes verticales: (r,c)-(r+1,c) y (r,c+1)-(r+1,c+1)
            return [((self.r, self.c), (self.r + 1, self.c)),
                    ((self.r, self.c + 1), (self.r + 1, self.c + 1))]
        # 'V': bloquea dos bordes horizontales: (r,c)-(r,c+1) y (r+1,c)-(r+1,c+1)
        return [((self.r, self.c), (self.r, self.c + 1)),
                ((self.r + 1, self.c), (self.r + 1, self.c + 1))]


class Board:
    """Grafo mutable de celdas y adyacencias; colocar muros elimina aristas."""
    def __init__(self) -> None:
        self.adj: Dict[Coord, Set[Coord]] = {(r, c): set() for r in range(BOARD_N) for c in range(BOARD_N)}
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_N and 0 <= nc < BOARD_N:
                        self.adj[(r, c)].add((nr, nc))
        # almacenes de muros
        self.walls: Set[Wall] = set()
        self.h_slots: Set[Tuple[int, int]] = set()  # anclas H colocadas
        self.v_slots: Set[Tuple[int, int]] = set()  # anclas V colocadas

    def clone(self) -> "Board":
        b = Board.__new__(Board)
        b.adj = {u: set(vs) for u, vs in self.adj.items()}
        b.walls = set(self.walls)
        b.h_slots = set(self.h_slots)
        b.v_slots = set(self.v_slots)
        return b

    def has_edge(self, a: Coord, b: Coord) -> bool:
        return b in self.adj[a]

    def remove_edge(self, a: Coord, b: Coord) -> None:
        self.adj[a].discard(b)
        self.adj[b].discard(a)

    # --- NUEVO: movimientos inmediatos desde una casilla (sin saltos) ---
    def legal_moves_from(self, pos: Coord, other: Coord) -> Set[Coord]:
        """Vecinos ortogonales disponibles, excluyendo la casilla del oponente."""
        return {v for v in self.adj[pos] if v != other}

    # ---------- Reglas de muros ----------
    def _crossing_or_overlap(self, w: Wall) -> bool:
        """Evita solape exacto y cruce perpendicular por el centro."""
        if w.orientation == "H":
            if (w.r, w.c) in self.h_slots:
                return True  # mismo slot (solape)
            if (w.r, w.c) in self.v_slots:
                return True  # cruce perpendicular por el centro
        else:
            if (w.r, w.c) in self.v_slots:
                return True
            if (w.r, w.c) in self.h_slots:
                return True
        return False

    def can_place_wall(self, w: Wall, p1: Coord, p2: Coord) -> Tuple[bool, str]:
        if not w.in_bounds():
            return False, "Muro fuera de rango (ancla en 0..7 x 0..7)."
        if w in self.walls:
            return False, "Ya existe un muro idéntico."
        if self._crossing_or_overlap(w):
            return False, "No se permite solapar o cruzar muros en el centro del slot."

        # cada segmento que quiere bloquear debe existir aún
        for a, b in w.edges_blocked():
            if not self.has_edge(a, b):
                return False, "El muro colisiona con otro (segmento ya bloqueado)."

        # --- Simular y verificar invariantes ---
        test = self.clone()
        for a, b in w.edges_blocked():
            test.remove_edge(a, b)

        # (A) NUEVO: ambos conservan al menos un movimiento inmediato
        if not test.legal_moves_from(p1, p2):
            return False, "Ilegal: J1 quedaría sin movimientos inmediatos."
        if not test.legal_moves_from(p2, p1):
            return False, "Ilegal: J2 quedaría sin movimientos inmediatos."

        # (B) Como ya estaba: sigue existiendo un camino a meta (I3)
        if not (test._reachable_to_goal(p1, GOAL_P1) and test._reachable_to_goal(p2, GOAL_P2)):
            return False, "Bloquearía completamente el camino de algún jugador."

        return True, "OK"

    def place_wall(self, w: Wall, p1: Coord, p2: Coord) -> Tuple[bool, str]:
        ok, msg = self.can_place_wall(w, p1, p2)
        if not ok:
            return ok, msg
        for a, b in w.edges_blocked():
            self.remove_edge(a, b)
        self.walls.add(w)
        if w.orientation == "H":
            self.h_slots.add((w.r, w.c))
        else:
            self.v_slots.add((w.r, w.c))
        return True, "Muro colocado."

    # ---------- BFS ----------
    def _reachable_to_goal(self, start: Coord, goal_row: int) -> bool:
        from collections import deque
        dq = deque([start])
        seen = {start}
        while dq:
            r, c = dq.popleft()
            if r == goal_row:
                return True
            for v in self.adj[(r, c)]:
                if v not in seen:
                    seen.add(v)
                    dq.append(v)
        return False

    def shortest_dist_to_goal(self, start: Coord, goal_row: int) -> Optional[int]:
        from collections import deque
        INF = 10 ** 9
        dist = {(r, c): INF for r in range(BOARD_N) for c in range(BOARD_N)}
        dist[start] = 0
        dq = deque([start])
        while dq:
            u = dq.popleft()
            if u[0] == goal_row:
                return dist[u]
            for v in self.adj[u]:
                if dist[v] == INF:
                    dist[v] = dist[u] + 1
                    dq.append(v)
        return None


class Game:
    """Estado del juego + reglas de turno; sin UI."""
    def __init__(self) -> None:
        self.board = Board()
        self.p1: Coord = START_P1
        self.p2: Coord = START_P2
        self.turn: int = 1
        self.walls_left = {1: WALLS_PER_PLAYER, 2: WALLS_PER_PLAYER}

    # --- utilidades ---
    def goal_row(self, player: int) -> int:
        return GOAL_P1 if player == 1 else GOAL_P2

    def pos(self, player: int) -> Coord:
        return self.p1 if player == 1 else self.p2

    def set_pos(self, player: int, coord: Coord) -> None:
        if player == 1:
            self.p1 = coord
        else:
            self.p2 = coord

    # --- movimientos ---
    def legal_moves(self, player: int) -> Set[Coord]:
        """Movimiento ortogonal 1 casilla (sin saltos)."""
        src = self.pos(player)
        opp = self.pos(2 if player == 1 else 1)
        moves: Set[Coord] = set()
        for nb in self.board.adj[src]:
            if nb != opp:
                moves.add(nb)
        return moves

    def apply_move(self, dest: Coord) -> Tuple[bool, str]:
        if dest not in self.legal_moves(self.turn):
            return False, "Movimiento ilegal."
        self.set_pos(self.turn, dest)
        if self.victory():
            return True, f"Jugador {self.turn} gana."
        self.turn = 2 if self.turn == 1 else 1
        return True, "OK"

    # --- muros ---
    def apply_wall(self, w: Wall) -> Tuple[bool, str]:
        if self.walls_left[self.turn] <= 0:
            return False, "No quedan muros."
        ok, msg = self.board.place_wall(w, self.p1, self.p2)
        if not ok:
            return False, msg
        self.walls_left[self.turn] -= 1
        self.turn = 2 if self.turn == 1 else 1
        return True, "OK"

    # --- victoria ---
    def victory(self) -> bool:
        return (self.p1[0] == GOAL_P1) or (self.p2[0] == GOAL_P2)
