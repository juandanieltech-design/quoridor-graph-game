# main.py
import sys
import tkinter as tk

from core import Game
from multi_core import MultiGame
from player import HumanPlayer, CPUPlayer
from interface import QuoridorApp


def build_players_from_pattern(pattern: str):
    """
    Recibe un string como:
      "HC"   -> humano vs CPU
      "HH"   -> humano vs humano
      "CC"   -> CPU vs CPU
      "HCC"  -> J vs CPU vs CPU
      "HCCC" -> J vs CPU vs CPU vs CPU
      "CCC"  -> CPU vs CPU vs CPU
      "CCCC" -> CPU vs CPU vs CPU vs CPU

    Devuelve:
      - num_players
      - diccionario {pid -> instancia Player}
      - flag use_multi_game (True si son 3 o 4 jugadores)
    """
    pat = pattern.upper().strip()
    if not pat:
        pat = "HC"  # por defecto humano vs CPU

    num_players = len(pat)
    if num_players == 1:
        # Forzamos 2 jugadores; el segundo será CPU
        pat = pat + "C"
        num_players = 2

    if num_players > 4:
        raise ValueError("Máximo 4 jugadores soportados.")

    players = {}
    for i, ch in enumerate(pat, start=1):
        if ch == "H":
            players[i] = HumanPlayer()
        else:
            players[i] = CPUPlayer()

    use_multi = (num_players >= 3)
    return num_players, players, use_multi, pat


def start_quoridor(root: tk.Tk, pattern: str):
    """Limpia la ventana y crea el juego según el patrón elegido."""
    num_players, players, use_multi, pat = build_players_from_pattern(pattern)

    if use_multi or num_players > 2:
        game = MultiGame(num_players)
    else:
        game = Game()

    # Eliminar widgets del selector de modo
    for widget in root.winfo_children():
        widget.destroy()

    root.title(f"Quoridor – {num_players} jugadores ({pat})")

    # Crear la app principal sobre el mismo root
    QuoridorApp(root, game, players)


def main():
    # Si vienes desde consola con patrón, saltamos el selector
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        root = tk.Tk()
        start_quoridor(root, pattern)
        root.mainloop()
        return

    # ---------- Selector gráfico de modo ----------
    root = tk.Tk()
    root.title("Quoridor – seleccionar modo de juego")

    pattern_var = tk.StringVar(value="HC")
    desc_var = tk.StringVar(value="Jugador vs CPU")

    patterns = [
        ("Jugador vs CPU",                 "HC"),
        ("Jugador vs Jugador",             "HH"),
        ("CPU vs CPU",                     "CC"),
        ("J vs CPU vs CPU",                "HCC"),
        ("J vs CPU vs CPU vs CPU",         "HCCC"),
        ("CPU vs CPU vs CPU",              "CCC"),
        ("CPU vs CPU vs CPU vs CPU (demo)","CCCC"),
    ]

    tk.Label(root, text="Selecciona el modo de juego:") \
        .pack(padx=10, pady=(10, 4), anchor="w")

    for text, pat in patterns:
        def make_cmd(p=pat, t=text):
            def _cmd():
                pattern_var.set(p)
                desc_var.set(t)
            return _cmd

        rb = tk.Radiobutton(
            root,
            text=text,
            value=pat,
            variable=pattern_var,
            command=make_cmd()
        )
        rb.pack(anchor="w", padx=20)

    tk.Label(root, textvariable=desc_var, fg="gray") \
        .pack(pady=(4, 8))

    def on_start():
        pattern = pattern_var.get()
        start_quoridor(root, pattern)

    tk.Button(root, text="Iniciar partida", command=on_start) \
        .pack(pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    main()
