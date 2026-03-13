# interface.py
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple, Dict

# IMPORT ABSOLUTO (estructura plana)
from core import Game, Wall, BOARD_N

CELL = 54      # tamaño de una celda (px)
MARGIN = 6     # margen de la interfaz (px)
PAWN_R = 16    # radio peones
W_THICK = 10   # grosor visual del muro


class QuoridorApp:
    def __init__(self, root: tk.Tk, game, players: Dict[int, object]) -> None:
        self.root = root
        self.game = game          # puede ser Game o MultiGame
        self.players = players    # {pid -> Player}
        self.mode = tk.StringVar(value="move")  # "move", "H", "V"
        self.status_var = tk.StringVar(value="Listo.")
        self.game_over = False  # bloquear acciones cuando termina

        # dibujamos aristas; nodos a cada intersección
        side = MARGIN * 2 + CELL * (BOARD_N - 1)
        self.canvas = tk.Canvas(root, width=side, height=side + CELL, bg="white")
        self.canvas.grid(row=0, column=0, columnspan=3, padx=6, pady=6)

        # Controles
        tk.Radiobutton(root, text="Mover", variable=self.mode, value="move") \
            .grid(row=1, column=0, sticky="w", padx=10)
        tk.Radiobutton(root, text="Muro H", variable=self.mode, value="H") \
            .grid(row=1, column=1, sticky="w", padx=10)
        tk.Radiobutton(root, text="Muro V", variable=self.mode, value="V") \
            .grid(row=1, column=2, sticky="w", padx=10)
        tk.Label(root, textvariable=self.status_var) \
            .grid(row=2, column=0, columnspan=3, sticky="we", padx=10, pady=(0, 8))

        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_board()
        self.refresh()

        # si arranca CPU
        self.after_human_if_cpu()

    # ------------- dibujo -------------
    def draw_board(self):
        self.canvas.delete("all")
        # dibujar rejilla de celdas 9x9 (líneas finas)
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                x = MARGIN + c * CELL
                y = MARGIN + r * CELL
                # puntos de intersección (nodos)
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                                        fill="#8aa", outline="")
        # líneas entre nodos (aristas libres)
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                x = MARGIN + c * CELL
                y = MARGIN + r * CELL
                if c < BOARD_N - 1:
                    self.canvas.create_line(x, y, x + CELL, y,
                                            fill="#bbb", width=2)
                if r < BOARD_N - 1:
                    self.canvas.create_line(x, y, x, y + CELL,
                                            fill="#bbb", width=2)

    def draw_walls(self):
        for w in self.game.board.walls:
            if w.orientation == "H":
                # muro horizontal ocupa dos aristas verticales contiguas
                x1 = MARGIN + w.c * CELL
                y = MARGIN + w.r * CELL + CELL / 2
                x2 = x1 + 2 * CELL
                self.canvas.create_rectangle(
                    x1, y - W_THICK / 2, x2, y + W_THICK / 2,
                    fill="#7b3", outline=""
                )
            else:
                # muro vertical ocupa dos aristas horizontales contiguas
                x = MARGIN + w.c * CELL + CELL / 2
                y1 = MARGIN + w.r * CELL
                y2 = y1 + 2 * CELL
                self.canvas.create_rectangle(
                    x - W_THICK / 2, y1, x + W_THICK / 2, y2,
                    fill="#b37", outline=""
                )

    def draw_pawns(self):
        # Paleta de colores para hasta 4 jugadores
        colors = {
            1: "#2573ff",  # azul
            2: "#ff6a00",  # naranja
            3: "#2abf5a",  # verde
            4: "#b832f5",  # morado
        }

        if hasattr(self.game, "players_ids"):  # MultiGame
            ids = self.game.players_ids()
            for pid in ids:
                r, c = self.game.pos(pid)
                x = MARGIN + c * CELL
                y = MARGIN + r * CELL
                color = colors.get(pid, "#000000")
                self.canvas.create_oval(
                    x - PAWN_R, y - PAWN_R, x + PAWN_R, y + PAWN_R,
                    fill=color, outline="#222", width=2
                )
        else:
            # modo clásico 2 jugadores (Game original)
            for player, color in [(1, "#2573ff"), (2, "#ff6a00")]:
                r, c = self.game.pos(player)
                x = MARGIN + c * CELL
                y = MARGIN + r * CELL
                self.canvas.create_oval(
                    x - PAWN_R, y - PAWN_R, x + PAWN_R, y + PAWN_R,
                    fill=color, outline="#222", width=2
                )

    def refresh(self):
        self.draw_board()
        self.draw_walls()
        self.draw_pawns()

        # construir string de muros por jugador
        if hasattr(self.game, "players_ids"):
            parts = []
            for pid in self.game.players_ids():
                parts.append(f"J{pid}={self.game.walls_left[pid]}")
            muros_txt = " ".join(parts)
        else:
            muros_txt = (f"J1={self.game.walls_left[1]} "
                         f"J2={self.game.walls_left[2]}")

        self.status_var.set(
            f"Turno J{self.game.turn} | Muros {muros_txt}"
        )

    # ------------- interacción -------------
    def on_click(self, event):
        if self.game_over:
            return

        player = self.game.turn
        pl = self.players[player]
        if pl.__class__.__name__ != "HumanPlayer":
            return  # si no es humano, ignorar clicks

        mode = self.mode.get()

        if mode == "move":
            cell = self._nearest_cell(event.x, event.y)
            if cell is None:
                return
            ok, msg = self.game.apply_move(cell)
            if not ok:
                messagebox.showinfo("Movimiento", msg)
            self.refresh()
            self._check_end()
            if not self.game_over:
                self.after_human_if_cpu()
            return

        # modo muro: H o V
        slot = self._nearest_slot(event.x, event.y)
        if slot is None:
            return
        r, c = slot
        w = Wall(r, c, mode)
        ok, msg = self.game.apply_wall(w)
        if not ok:
            messagebox.showinfo("Muro", msg)

        # refrescar SIEMPRE, haya o no éxito (si fue válido, ya cambió el turno)
        self.refresh()
        self._check_end()
        if not self.game_over:
            self.after_human_if_cpu()

    def after_human_if_cpu(self):
        """Si ahora es el turno de la CPU, que actúe de forma automática."""
        if self.game_over:
            return
        current = self.players[self.game.turn]
        if current.__class__.__name__ == "CPUPlayer":
            self.root.after(250, self.cpu_step)

    def cpu_step(self):
        if self.game_over:
            return
        current = self.players[self.game.turn]
        action, payload = current.choose_action(self.game)
        if action == "move" and payload:
            self.game.apply_move(payload)
        elif action == "wall" and payload:
            r, c, ori = payload
            self.game.apply_wall(Wall(r, c, ori))

        self.refresh()
        self._check_end()
        if not self.game_over:
            self.after_human_if_cpu()

    # ------------ helpers de coordenadas --------
    def _nearest_cell(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Mapea un click a la celda (nodo) más cercana (0..8, 0..8)."""
        c = round((x - MARGIN) / CELL)
        r = round((y - MARGIN) / CELL)
        if 0 <= r < BOARD_N and 0 <= c < BOARD_N:
            return (r, c)
        return None

    def _nearest_slot(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Mapea un click a la rejilla 8x8 de anclas de muros (0..7, 0..7)."""
        c = round((x - MARGIN - CELL / 2) / CELL)
        r = round((y - MARGIN - CELL / 2) / CELL)
        if 0 <= r < BOARD_N - 1 and 0 <= c < BOARD_N - 1:
            # los anclajes válidos están en 0..7 (BOARD_N-2),
            # pero redondear puede empujar a 8; acotamos al rango permitido
            if r > BOARD_N - 2:
                r = BOARD_N - 2
            if c > BOARD_N - 2:
                c = BOARD_N - 2
            return (r, c)
        return None

    # ------------ fin de partida --------
    def _check_end(self):
        """Si alguien llegó a su meta, bloquea la UI y avisa."""
        # Caso Game clásico (2 jugadores)
        if hasattr(self.game, "victory"):
            if self.game.victory():
                winner = 1 if self.game.p1[0] == 0 else 2
                self.game_over = True
                self.status_var.set(f"¡Juego terminado! Gana J{winner}")
                messagebox.showinfo("Fin de la partida",
                                    f"¡Gana el Jugador {winner}!")
            return

        # Caso MultiGame
        winner = getattr(self.game, "winner", None)
        if winner is not None:
            self.game_over = True
            self.status_var.set(f"¡Juego terminado! Gana J{winner}")
            messagebox.showinfo("Fin de la partida",
                                f"¡Gana el Jugador {winner}!")
