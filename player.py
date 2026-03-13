# player.py
from __future__ import annotations
import random
from typing import Optional, Tuple, Any

# IMPORT ABSOLUTO (estructura plana)
from core import Game, Wall


class Player:
    """Interfaz común de jugador."""
    def choose_action(self, game: Any) -> Tuple[str, Optional[Tuple]]:
        """
        Debe devolver:
        - ("move", (r,c)) o 
        - ("wall", (r,c,'H'/'V')) o 
        - ("wait", None)
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """El humano no decide desde aquí: la GUI entrega la acción."""
    def choose_action(self, game: Any) -> Tuple[str, Optional[Tuple]]:
        return ("wait", None)


class CPUPlayer(Player):
    def __init__(self, wall_prob: float = 0.35) -> None:
        self.wall_prob = wall_prob

    # --------- helper interno para validar muros en Game o MultiGame ----------
    def _can_place_wall_generic(self, game: Any, wall: Wall) -> bool:
        """
        Intenta validar un muro tanto en:
        - Game clásico (2 jugadores, atributos p1/p2)
        - MultiGame (2–4 jugadores, posiciones en un diccionario)
        sin modificar el estado real de la partida.
        """
        # Caso MultiGame: tiene players_ids() y método interno _can_place_wall_for_all
        if hasattr(game, "players_ids") and hasattr(game, "pos") and hasattr(game, "_can_place_wall_for_all"):
            positions = [game.pos(pid) for pid in game.players_ids()]
            ok, _ = game._can_place_wall_for_all(wall, positions)
            return ok

        # Caso Game clásico
        if isinstance(game, Game):
            ok, _ = game.board.can_place_wall(wall, game.p1, game.p2)
            return ok

        # Fallback: no sabemos validar -> no colocar muro
        return False

    def choose_action(self, game: Any) -> Tuple[str, Optional[Tuple]]:
        # ¿Intentar muro este turno?
        do_wall = (random.random() < self.wall_prob) and (game.walls_left[game.turn] > 0)

        if do_wall:
            # intentar algunos muros válidos al azar
            for _ in range(40):
                r = random.randint(0, 7)
                c = random.randint(0, 7)
                ori = random.choice(["H", "V"])
                w = Wall(r, c, ori)
                if self._can_place_wall_generic(game, w):
                    return ("wall", (r, c, ori))

        # Si no se pudo (o no se quiso) poner muro, hacemos movimiento aleatorio válido
        moves = list(game.legal_moves(game.turn))
        if moves:
            return ("move", random.choice(moves))

        # Si ni siquiera puede moverse, pasa (acción nula)
        return ("wait", None)
