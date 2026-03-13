# multi_core.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Set, List, Callable, Optional

from core import Board, Coord, BOARD_N, WALLS_PER_PLAYER

@dataclass
class PlayerGoal:
    """Condición de victoria para un jugador."""
    name: str  # "NORTE", "SUR", "OESTE", "ESTE"
    predicate: Callable[[Coord], bool]  # devuelve True si la celda cumple meta


def _row_goal(target_row: int) -> Callable[[Coord], bool]:
    def goal(c: Coord) -> bool:
        return c[0] == target_row
    return goal


def _col_goal(target_col: int) -> Callable[[Coord], bool]:
    def goal(c: Coord) -> bool:
        return c[1] == target_col
    return goal


# Configuraciones hasta 4 jugadores en el mismo tablero 9x9
MULTI_CONFIG: Dict[int, Dict[int, Tuple[Coord, PlayerGoal]]] = {
    # 2 jugadores: tu configuración actual
    2: {
        1: ((BOARD_N - 1, BOARD_N // 2), PlayerGoal("SUR→NORTE", _row_goal(0))),      # (8,4) meta fila 0
        2: ((0, BOARD_N // 2),             PlayerGoal("NORTE→SUR", _row_goal(BOARD_N - 1))),  # (0,4) meta 8
    },
    # 3 jugadores: agregamos jugador Oeste
    3: {
        1: ((BOARD_N - 1, BOARD_N // 2), PlayerGoal("SUR→NORTE", _row_goal(0))),
        2: ((0, BOARD_N // 2),           PlayerGoal("NORTE→SUR", _row_goal(BOARD_N - 1))),
        3: ((BOARD_N // 2, 0),           PlayerGoal("OESTE→ESTE", _col_goal(BOARD_N - 1))),   # (4,0) meta col 8
    },
    # 4 jugadores: añadimos jugador Este
    4: {
        1: ((BOARD_N - 1, BOARD_N // 2), PlayerGoal("SUR→NORTE", _row_goal(0))),
        2: ((0, BOARD_N // 2),           PlayerGoal("NORTE→SUR", _row_goal(BOARD_N - 1))),
        3: ((BOARD_N // 2, 0),           PlayerGoal("OESTE→ESTE", _col_goal(BOARD_N - 1))),
        4: ((BOARD_N // 2, BOARD_N - 1), PlayerGoal("ESTE→OESTE", _col_goal(0))),
    },
}


class MultiGame:
    """
    Versión generalizada del juego para 2–4 jugadores.
    - Mantiene el mismo Board (muros, BFS, etc.).
    - Rota turno entre los jugadores activos.
    """

    def __init__(self, num_players: int) -> None:
        if num_players not in (2, 3, 4):
            raise ValueError("MultiGame solo soporta 2, 3 o 4 jugadores.")
        self.num_players = num_players
        self.board = Board()
        cfg = MULTI_CONFIG[num_players]

        # Posiciones y metas
        self.positions: Dict[int, Coord] = {}
        self.goals: Dict[int, PlayerGoal] = {}
        for pid, (start, goal) in cfg.items():
            self.positions[pid] = start
            self.goals[pid] = goal

        # muros por jugador
        self.walls_left: Dict[int, int] = {pid: WALLS_PER_PLAYER for pid in cfg.keys()}
        self.turn: int = 1
        self.winner: Optional[int] = None

    # ---- utilidades ----
    def players_ids(self) -> List[int]:
        return list(self.positions.keys())

    def next_player(self, pid: int) -> int:
        """Rota el turno circularmente 1→2→3→4→1 (según num_players)."""
        p = pid + 1
        while True:
            if p > self.num_players:
                p = 1
            if p in self.positions:   # por si en futuro hay jugadores inactivos
                return p
            p += 1

    def pos(self, pid: int) -> Coord:
        return self.positions[pid]

    def set_pos(self, pid: int, coord: Coord) -> None:
        self.positions[pid] = coord

    # ---- movimientos ----
    def legal_moves(self, pid: int) -> Set[Coord]:
        """Movimientos ortogonales de una casilla sin saltos, evitando peones."""
        src = self.pos(pid)
        occupied = {self.pos(p) for p in self.players_ids() if p != pid}
        moves: Set[Coord] = set()
        for nb in self.board.adj[src]:
            if nb not in occupied:
                moves.add(nb)
        return moves

    def apply_move(self, dest: Coord) -> Tuple[bool, str]:
        if self.winner is not None:
            return False, "La partida ya terminó."
        if dest not in self.legal_moves(self.turn):
            return False, "Movimiento ilegal."
        self.set_pos(self.turn, dest)

        # ¿alguien gana?
        if self._check_victory(self.turn):
            self.winner = self.turn
            return True, f"Jugador {self.turn} gana."

        # pasar turno
        self.turn = self.next_player(self.turn)
        return True, "OK"

    # ---- muros ----
    def apply_wall(self, w) -> Tuple[bool, str]:
        from core import Wall  # reusar clase existente

        if self.winner is not None:
            return False, "La partida ya terminó."
        if not isinstance(w, Wall):
            return False, "Tipo de muro inválido."
        if self.walls_left[self.turn] <= 0:
            return False, "No quedan muros para este jugador."

        # posiciones actuales de TODOS los jugadores
        # (Board.can_place_wall estaba pensado para 2, lo adaptaremos aquí)
        p_positions = list(self.positions.values())
        # comprobamos que NADIE pierda conectividad a su meta
        ok, msg = self._can_place_wall_for_all(w, p_positions)
        if not ok:
            return False, msg

        # si es válido, lo aplicamos en el Board “real”
        ok2, msg2 = self.board.place_wall(w, p_positions[0], p_positions[1])
        if not ok2:
            return False, msg2

        self.walls_left[self.turn] -= 1
        self.turn = self.next_player(self.turn)
        return True, "OK"

    def _can_place_wall_for_all(self, w, positions: List[Coord]) -> Tuple[bool, str]:
        """
        Reutiliza la lógica de Board.can_place_wall, pero extendida:
        - verifica BFS para todos los jugadores hacia su meta correspondiente.
        """
        # Simulamos en una copia
        test = self.board.clone()

        ok_base, msg = test.can_place_wall(w, positions[0], positions[1])
        if not ok_base:
            return False, msg

        # Comprobamos conectividad individual con las metas (generalizadas)
        for pid, coord in self.positions.items():
            goal = self.goals[pid]
            if not self._reachable_to_goal(test, coord, goal.predicate):
                return False, f"El muro bloquearía completamente al jugador {pid}."
        return True, "OK"

    # ---- BFS generalizado ----
    def _reachable_to_goal(self, board: Board,
                           start: Coord,
                           goal_pred: Callable[[Coord], bool]) -> bool:
        from collections import deque
        dq = deque([start])
        seen = {start}
        while dq:
            u = dq.popleft()
            if goal_pred(u):
                return True
            for v in board.adj[u]:
                if v not in seen:
                    seen.add(v)
                    dq.append(v)
        return False

    # ---- victoria ----
    def _check_victory(self, pid: int) -> bool:
        coord = self.pos(pid)
        goal = self.goals[pid]
        return goal.predicate(coord)
