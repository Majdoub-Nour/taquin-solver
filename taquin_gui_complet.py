import tkinter as tk
from tkinter import ttk, messagebox
import time
import heapq


etat_depart = (1, 2, 3,
               8, 6, 0,
               7, 5, 4)

etat_final = (1, 2, 3,
              8, 0, 4,
              7, 6, 5)


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def position_case_vide(t):
    i = t.index(0)
    y, x = divmod(i, 3)
    return (x, y)

def permuter(t, c1, c2):
    x1, y1 = c1
    x2, y2 = c2
    lst = list(t)
    i1 = y1 * 3 + x1
    i2 = y2 * 3 + x2
    lst[i1], lst[i2] = lst[i2], lst[i1]
    return tuple(lst)

def transitions(t):
    x, y = position_case_vide(t)
    succ = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 3 and 0 <= ny < 3:
            succ.append(permuter(t, (x, y), (nx, ny)))
    return succ

def reconstruire_chemin(parent, goal):
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    return list(reversed(path))


# ---------------------------------------------------------------------------
# Heuristiques
# ---------------------------------------------------------------------------

def h_mal_places(t):
    """Nombre de cases mal placées (hors case vide)."""
    return sum(1 for i, v in enumerate(t) if v != 0 and v != etat_final[i])

# Position cible de chaque valeur dans l'état final
_pos_final = {v: (i % 3, i // 3) for i, v in enumerate(etat_final)}

def h_manhattan(t):
    """Distance de Manhattan — heuristique admissible et plus précise."""
    dist = 0
    for i, v in enumerate(t):
        if v != 0:
            cx, cy = i % 3, i // 3
            gx, gy = _pos_final[v]
            dist += abs(cx - gx) + abs(cy - gy)
    return dist


# ---------------------------------------------------------------------------
# Algorithmes de recherche
# ---------------------------------------------------------------------------

def DFS(start, limit=None):
    """
    Recherche en profondeur (LIFO).
    CORRECTION : utilisation de pop() et non pop(0) pour respecter l'ordre LIFO.
    """
    stack = [start]           # pile : on empile/dépile par la fin
    closedNodes = set()
    parent = {start: None}
    depth = {start: 0}
    generated_total = 0

    while stack:
        node = stack.pop()    # LIFO — CORRECTION (était pop(0))

        if node in closedNodes:
            continue
        closedNodes.add(node)

        if node == etat_final:
            return reconstruire_chemin(parent, node), generated_total, len(closedNodes)

        d = depth[node]
        if limit is not None and d >= limit:
            continue

        gen = transitions(node)
        generated_total += len(gen)

        for s in gen:
            if s not in closedNodes and s not in parent:
                parent[s] = node
                depth[s] = d + 1
                stack.append(s)

    return None, generated_total, len(closedNodes)


def BFS(start):
    """
    Recherche en largeur (FIFO).
    CORRECTION : test d'appartenance à visited avant d'ajouter dans la file
    pour éviter les doublons et accélérer la recherche.
    """
    queue = [start]
    visited = {start}         # ensemble des nœuds déjà mis en file
    closedNodes = set()
    parent = {start: None}
    generated_total = 0

    while queue:
        node = queue.pop(0)   # FIFO

        if node in closedNodes:
            continue
        closedNodes.add(node)

        if node == etat_final:
            return reconstruire_chemin(parent, node), generated_total, len(closedNodes)

        gen = transitions(node)
        generated_total += len(gen)

        for s in gen:
            if s not in visited:   # CORRECTION : test avant insertion
                visited.add(s)
                parent[s] = node
                queue.append(s)

    return None, generated_total, len(closedNodes)


def DFS_limite_iteratif(start, L0=0, Lmax=50):
    """
    DFS à profondeur limitée croissante (IDA).
    CORRECTION : Lmax par défaut à 50 (au lieu de 3 qui était trop petit).
    """
    for L in range(L0, Lmax + 1):
        path, gen, closed = DFS(start, limit=L)
        if path:
            return path, gen, closed, L
    return None, 0, 0, None


def Astar(start):
    """
    A* avec heuristique de Manhattan (plus précise que cases mal placées).
    """
    openh = []
    heapq.heappush(openh, (h_manhattan(start), 0, start))
    parent = {start: None}
    gscore = {start: 0}
    closedNodes = set()
    generated_total = 0

    while openh:
        f, g, node = heapq.heappop(openh)

        if node in closedNodes:
            continue
        closedNodes.add(node)

        if node == etat_final:
            return reconstruire_chemin(parent, node), generated_total, len(closedNodes)

        gen = transitions(node)
        generated_total += len(gen)

        for s in gen:
            if s in closedNodes:
                continue
            ng = g + 1
            if s not in gscore or ng < gscore[s]:
                gscore[s] = ng
                parent[s] = node
                heapq.heappush(openh, (ng + h_manhattan(s), ng, s))

    return None, generated_total, len(closedNodes)


# ---------------------------------------------------------------------------
# Interface graphique
# ---------------------------------------------------------------------------

# Couleurs associées à chaque valeur (1-8) pour l'affichage
TILE_COLORS = {
    1: "#4472C4", 2: "#4472C4", 3: "#4472C4",
    4: "#5B9BD5", 5: "#5B9BD5", 6: "#5B9BD5",
    7: "#70AD47", 8: "#70AD47",
}


class TaquinGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Résolution du Taquin 3×3")
        self.geometry("1200x850")
        self.resizable(False, False)
        self.config(bg="#f0f0f0")

        self.current_state = etat_depart
        self.solution_path = []
        self.step_index = 0
        self.is_animating = False

        self.create_widgets()

    def create_widgets(self):
        title_frame = ttk.Frame(self)
        title_frame.pack(pady=10)
        ttk.Label(title_frame, text="Résolution du Taquin 3×3",
                  font=("Arial", 18, "bold")).pack()

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Panneau gauche : grille ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", padx=10, pady=10)

        ttk.Label(left_frame, text="Initialisation",
                  font=("Arial", 12, "bold"), foreground="#4472C4").pack(pady=5)

        grid_frame = ttk.Frame(left_frame, relief="solid", borderwidth=2)
        grid_frame.pack(pady=5)

        self.buttons = []
        for r in range(3):
            for c in range(3):
                btn = tk.Label(grid_frame, text="", width=8, height=4,
                               font=("Arial", 18, "bold"), relief="ridge",
                               borderwidth=2, bg="#e0e0e0", fg="white")
                btn.grid(row=r, column=c, padx=2, pady=2)
                self.buttons.append(btn)

        self.rafraichir_affichage()

        self.btn_animate = ttk.Button(left_frame, text="▶ Animer la solution",
                                      command=self.animer_solution, state="disabled")
        self.btn_animate.pack(pady=10)

        self.label_step = ttk.Label(left_frame, text="", font=("Arial", 10))
        self.label_step.pack()

        # --- Panneau droit : stats et boutons ---
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        ttk.Label(right_frame, text="Nœuds visités",
                  font=("Arial", 12, "bold"), foreground="#4472C4").pack(pady=5)

        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.pack(pady=10)

        self.btn_dfs = ttk.Button(buttons_frame, text="Profondeur",
                                   command=lambda: self.resoudre("DFS"))
        self.btn_dfs.grid(row=0, column=0, padx=5, pady=5, sticky="ew", ipadx=20)

        self.btn_bfs = ttk.Button(buttons_frame, text="Largeur",
                                   command=lambda: self.resoudre("BFS"))
        self.btn_bfs.grid(row=0, column=1, padx=5, pady=5, sticky="ew", ipadx=20)

        self.btn_dfs_lim = ttk.Button(buttons_frame, text="Profondeur\nlimité",
                                       command=lambda: self.resoudre("DFS_lim"))
        self.btn_dfs_lim.grid(row=0, column=2, padx=5, pady=5, sticky="ew", ipadx=20)

        self.btn_astar = ttk.Button(buttons_frame, text="A*",
                                     command=lambda: self.resoudre("Astar"))
        self.btn_astar.grid(row=0, column=3, padx=5, pady=5, sticky="ew", ipadx=20)

        for i in range(4):
            buttons_frame.columnconfigure(i, weight=1)

        stats_frame = ttk.LabelFrame(right_frame, text="Statistiques", padding=15)
        stats_frame.pack(fill="both", expand=True, pady=10)

        self.stats_text = tk.Text(stats_frame, height=15, width=40,
                                   font=("Courier", 10), bg="#f5f5f5",
                                   relief="solid", borderwidth=1)
        self.stats_text.pack(fill="both", expand=True)

        self.stats_text.insert("1.0",
            "Cliquez sur un algorithme pour résoudre le taquin.\n\n"
            "Algorithmes disponibles:\n"
            "• Profondeur (DFS)\n"
            "• Largeur (BFS)\n"
            "• Profondeur limitée itérative\n"
            "• A* (heuristique Manhattan)"
        )
        self.stats_text.config(state="disabled")

    def rafraichir_affichage(self):
        """
        Met à jour l'affichage du taquin.
        CORRECTION : la couleur dépend de la valeur de la case, pas de sa position.
        """
        for i, val in enumerate(self.current_state):
            if val == 0:
                self.buttons[i].config(text="", bg="#f0f0f0", fg="white")
            else:
                color = TILE_COLORS.get(val, "#4472C4")
                self.buttons[i].config(text=str(val), bg=color, fg="white")

    def resoudre(self, algo):
        """Résout le taquin avec l'algorithme choisi."""
        t0 = time.perf_counter()
        self.disable_buttons()
        self.update()

        try:
            L = None
            if algo == "DFS":
                path, gen, closed = DFS(etat_depart)
                algo_name = "DFS (Profondeur)"
            elif algo == "BFS":
                path, gen, closed = BFS(etat_depart)
                algo_name = "BFS (Largeur)"
            elif algo == "DFS_lim":
                path, gen, closed, L = DFS_limite_iteratif(etat_depart)
                algo_name = "DFS Limité itératif"
            else:
                path, gen, closed = Astar(etat_depart)
                algo_name = "A* (Manhattan)"

            t1 = time.perf_counter()

            if path:
                self.solution_path = path
                self.step_index = 0
                profondeur = len(path) - 1

                stats = f"ALGORITHME: {algo_name}\n"
                stats += "=" * 35 + "\n\n"
                stats += "✓ Solution trouvée!\n\n"
                stats += f"États générés:\n  {gen}\n\n"
                # CORRECTION : on affiche 'closed' pour les nœuds visités,
                # pas len(path) qui est la longueur du chemin solution.
                stats += f"Nœuds visités (clos):\n  {closed}\n\n"
                stats += f"Profondeur (coups):\n  {profondeur}\n\n"
                stats += f"Temps d'exécution:\n  {t1 - t0:.4f}s\n"
                if L is not None:
                    stats += f"\nProfondeur limite trouvée:\n  L = {L}\n"

                self.stats_text.config(state="normal")
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", stats)
                self.stats_text.config(state="disabled")

                self.btn_animate.config(state="normal")
                self.label_step.config(text=f"Prêt à animer ({profondeur} étapes)")
            else:
                messagebox.showerror("Erreur", "Pas de solution trouvée!")
                self.label_step.config(text="Erreur : pas de solution")

        finally:
            self.enable_buttons()

    def animer_solution(self):
        """Anime la solution étape par étape."""
        if self.is_animating:
            return
        self.is_animating = True
        self.btn_animate.config(state="disabled")
        self.step_index = 0
        self.animer_step()

    def animer_step(self):
        """Affiche une étape de l'animation."""
        if self.step_index < len(self.solution_path):
            self.current_state = self.solution_path[self.step_index]
            self.rafraichir_affichage()
            self.label_step.config(
                text=f"Étape {self.step_index + 1} / {len(self.solution_path)}"
            )
            self.step_index += 1
            self.after(400, self.animer_step)
        else:
            total = len(self.solution_path) - 1
            self.label_step.config(text=f"✓ Solution complète ({total} coups)!")
            self.is_animating = False
            self.btn_animate.config(state="normal")

    def disable_buttons(self):
        for b in (self.btn_dfs, self.btn_bfs, self.btn_dfs_lim,
                  self.btn_astar, self.btn_animate):
            b.config(state="disabled")

    def enable_buttons(self):
        for b in (self.btn_dfs, self.btn_bfs, self.btn_dfs_lim, self.btn_astar):
            b.config(state="normal")


if __name__ == "__main__":
    app = TaquinGUI()
    app.mainloop()