################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
#
# FILE: strategies/smart_strategy.py
#
# Stratégie "smart" : exploration progressive + pathfinding BFS sur la carte
# connue. Sans communication entre agents.
#
# Principe :
#   - L'agent mémorise les déchets qu'il a observés dans known_wastes.
#   - S'il connaît la position d'un déchet pertinent, il planifie un chemin
#     via BFS et stocke la file d'actions dans action_queue.
#   - Si un déchet apparaît dans son voisinage immédiat pendant un déplacement,
#     il interrompt le plan et ramasse immédiatement.
#   - Si l'agent arrive à destination et que le déchet a disparu (ramassé par
#     un autre agent), il invalide la cible et reprend l'exploration.
################################################################################

import random
from collections import deque


# ──────────────────────────────────────────────────────────────────────────────
# BFS sur la grille connue
# ──────────────────────────────────────────────────────────────────────────────

def _bfs(start, goal, known_grid, max_zone):
    """
    Retourne la liste ordonnée des positions à traverser pour aller de
    `start` à `goal`, en ne passant que par les cases connues accessibles
    (zone <= max_zone).

    Retourne [] si aucun chemin n'est trouvé dans la carte connue.
    """
    if start == goal:
        return []

    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        current = path[-1]
        cx, cy = current

        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
            npos = (nx, ny)
            if npos in visited:
                continue
            if npos not in known_grid:
                continue
            if known_grid[npos]["zone"] > max_zone:
                continue
            visited.add(npos)
            new_path = path + [npos]
            if npos == goal:
                return new_path[1:]  # on exclut la position de départ
            queue.append(new_path)

    return []  # pas de chemin connu


def _path_to_queue(path):
    """Convertit une liste de positions en file d'actions 'move'."""
    return [{"type": "move", "target": pos} for pos in path]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de sélection de cible
# ──────────────────────────────────────────────────────────────────────────────

def _nearest_known_waste(pos, waste_color, known_wastes, known_grid, max_zone):
    """
    Parmi les déchets connus de la couleur voulue, retourne la position la
    plus proche (BFS) et le chemin associé. Retourne (None, []) si aucune
    cible atteignable.
    """
    best_target = None
    best_path = None

    for wpos, color in known_wastes.items():
        if color != waste_color:
            continue
        path = _bfs(pos, wpos, known_grid, max_zone)
        # path vide peut signifier "déjà sur place" ou "inatteignable"
        if wpos == pos:
            return wpos, []
        if path:
            if best_path is None or len(path) < len(best_path):
                best_target = wpos
                best_path = path

    return best_target, best_path or []


def _nearest_known_drop(pos, known_grid, max_zone):
    """
    Retourne la position de dépôt (drop=True) la plus proche dans la carte
    connue, et le chemin BFS associé.
    """
    best_target = None
    best_path = None

    for gpos, info in known_grid.items():
        if not info.get("drop", False):
            continue
        if info["zone"] > max_zone:
            continue
        if gpos == pos:
            return gpos, []
        path = _bfs(pos, gpos, known_grid, max_zone)
        if path:
            if best_path is None or len(path) < len(best_path):
                best_target = gpos
                best_path = path

    return best_target, best_path or []


# ──────────────────────────────────────────────────────────────────────────────
# Mise à jour du known_wastes dans update() — appelée depuis agents.py
# ──────────────────────────────────────────────────────────────────────────────

def update_known_wastes(knowledge, percepts):
    """
    À appeler depuis Robot.update() pour les agents utilisant la stratégie
    smart. Met à jour known_wastes à partir des nouveaux percepts :
        - Ajoute les déchets observés.
        - Invalide les positions maintenant vides (déchet disparu).
    """
    known_wastes = knowledge["known_wastes"]

    for pos, cell in percepts["grid"].items():
        # Invalider les positions vides que l'on croyait occupées
        if pos in known_wastes and cell["wastes"][known_wastes[pos]] == 0:
            del known_wastes[pos]

        # Enregistrer les déchets observés (on ne garde que le premier type
        # trouvé par priorité croissante pour simplifier)
        for color in (1, 2, 3):
            if cell["wastes"][color] > 0:
                known_wastes[pos] = color
                break


# ──────────────────────────────────────────────────────────────────────────────
# Stratégie smart — agents verts et jaunes
# ──────────────────────────────────────────────────────────────────────────────

def smart_deliberate(knowledge, low_waste: int, high_waste: int, epsilon:float):
    """
    Stratégie smart pour GreenAgent (low=1, high=2)
    et YellowAgent (low=2, high=3).
    """
    current_pos = knowledge["current_pos"]
    inventory = knowledge["inventory"]
    known_grid = knowledge["grid"]
    known_wastes = knowledge["known_wastes"]
    action_queue = knowledge["action_queue"]
    max_zone = low_waste  # l'agent ne peut pas aller au-delà de sa zone

    x, y = current_pos

    # ── 1. Transformation ────────────────────────────────────────────────────
    if len(inventory[low_waste]) == 2:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        return {"type": "transform"}

    # ── 2. Dépôt du déchet transformé (high_waste) ───────────────────────────
    if len(inventory[high_waste]) == 1:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        # Case de droite dans la zone suivante ?
        right = (x + 1, y)
        if right in known_grid and known_grid[right]["zone"] == high_waste:
            return {"type": "put"}
        # Sinon avancer vers la droite (frontière de zone)
        return {"type": "move", "target": (x + 1, y)}

    # ── 3. Ramassage opportuniste dans le voisinage immédiat ─────────────────
    # Priorité absolue : si un low_waste est visible autour, on interrompt
    # tout plan en cours et on ramasse (ou on s'y déplace si pas sur la case).
    if len(inventory[low_waste]) < 2 and knowledge["cooldown_remaining"] == 0:
        # D'abord la case courante
        if known_grid.get(current_pos, {}).get("wastes", {}).get(low_waste, 0) > 0:
            knowledge["action_queue"] = []
            knowledge["target"] = None
            return {"type": "pick"}
        # Ensuite le voisinage Moore immédiat (distance 1)
        for neighbor in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if neighbor in known_grid and known_grid[neighbor]["wastes"].get(low_waste, 0) > 0:
                knowledge["action_queue"] = [{"type": "pick"}]
                knowledge["target"] = neighbor
                return {"type": "move", "target": neighbor}

    # ── 4. Vérification de la cible courante (déchet disparu ?) ──────────────
    target = knowledge.get("target")
    if target is not None:
        cell = known_grid.get(target, {})
        waste_gone = cell.get("wastes", {}).get(low_waste, 0) == 0
        if waste_gone:
            # Le déchet a été ramassé par quelqu'un d'autre → invalider
            knowledge["known_wastes"].pop(target, None)
            knowledge["action_queue"] = []
            knowledge["target"] = None
            target = None

    # ── 5. Dépiler la file d'actions planifiées ───────────────────────────────
    if action_queue:
        return action_queue.pop(0)
    
    # ── 6. Lâcher aléatoire d'un déchet (évite les blocages) ──────────────────
    if len(inventory[low_waste]) == 1 and random.random() < epsilon:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        return {"type": "put"}

    # ── 7. Planification BFS vers le déchet connu le plus proche ─────────────
    if len(inventory[low_waste]) < 2:
        best_target, path = _nearest_known_waste(
            current_pos, low_waste, known_wastes, known_grid, max_zone
        )
        if best_target is not None:
            knowledge["target"] = best_target
            # Ajouter un pick à la fin du chemin
            queue = _path_to_queue(path) + [{"type": "pick"}]
            knowledge["action_queue"] = queue
            if queue:
                return knowledge["action_queue"].pop(0)

    # ── 8. Exploration aléatoire (aucune cible connue) ────────────────────────
    possible = [
        {"type": "move", "target": (x+1, y)},
        {"type": "move", "target": (x-1, y)},
        {"type": "move", "target": (x,   y+1)},
        {"type": "move", "target": (x,   y-1)},
    ]
    return random.choice(possible)


# ──────────────────────────────────────────────────────────────────────────────
# Stratégie smart — agent rouge
# ──────────────────────────────────────────────────────────────────────────────

def smart_deliberate_red(knowledge):
    """
    Stratégie smart pour RedAgent.
    Si déchet rouge connu → BFS vers lui.
    Si tient un déchet rouge → BFS vers zone de dépôt connue.
    Sinon → exploration aléatoire.
    """
    current_pos = knowledge["current_pos"]
    inventory = knowledge["inventory"]
    known_grid = knowledge["grid"]
    known_wastes = knowledge["known_wastes"]
    action_queue = knowledge["action_queue"]

    x, y = current_pos

    # ── 1. Dépôt ─────────────────────────────────────────────────────────────
    if len(inventory[3]) == 1:
        knowledge["action_queue"] = []
        knowledge["target"] = None

        # Déjà sur la zone de dépôt ?
        if known_grid.get(current_pos, {}).get("drop", False):
            return {"type": "put"}

        # Zone de dépôt connue → BFS
        drop_target, path = _nearest_known_drop(
            current_pos, known_grid, max_zone=3)
        if drop_target is not None:
            queue = _path_to_queue(path) + [{"type": "put"}]
            knowledge["action_queue"] = queue
            if queue:
                return knowledge["action_queue"].pop(0)

        # Pas de zone connue → avancer à droite si possible, sinon longer le mur (haut/bas)
        if (x + 1, y) in known_grid:
            return {"type": "move", "target": (x + 1, y)}
        else:
            return random.choice([
                {"type": "move", "target": (x, y + 1)},
                {"type": "move", "target": (x, y - 1)}
            ])

    # ── 2. Ramassage opportuniste ─────────────────────────────────────────────
    if known_grid.get(current_pos, {}).get("wastes", {}).get(3, 0) > 0:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        return {"type": "pick"}

    for neighbor in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
        if neighbor in known_grid and known_grid[neighbor]["wastes"].get(3, 0) > 0:
            knowledge["action_queue"] = [{"type": "pick"}]
            knowledge["target"] = neighbor
            return {"type": "move", "target": neighbor}

    # ── 3. Vérification cible périmée ────────────────────────────────────────
    target = knowledge.get("target")
    if target is not None:
        cell = known_grid.get(target, {})
        if cell.get("wastes", {}).get(3, 0) == 0:
            knowledge["known_wastes"].pop(target, None)
            knowledge["action_queue"] = []
            knowledge["target"] = None
            target = None

    # ── 4. Dépiler file ───────────────────────────────────────────────────────
    if action_queue:
        return action_queue.pop(0)

    # ── 5. Planification BFS ──────────────────────────────────────────────────
    best_target, path = _nearest_known_waste(
        current_pos, 3, known_wastes, known_grid, max_zone=3
    )
    if best_target is not None:
        knowledge["target"] = best_target
        queue = _path_to_queue(path) + [{"type": "pick"}]
        knowledge["action_queue"] = queue
        if queue:
            return knowledge["action_queue"].pop(0)

    # ── 6. Exploration aléatoire ──────────────────────────────────────────────
    possible = [
        {"type": "move", "target": (x+1, y)},
        {"type": "move", "target": (x-1, y)},
        {"type": "move", "target": (x,   y+1)},
        {"type": "move", "target": (x,   y-1)},
    ]
    return random.choice(possible)
