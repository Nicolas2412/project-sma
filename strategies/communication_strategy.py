################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/04/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronnière
#   - Paul Guimbert
#
# FILE: strategies/communication_strategy.py
#
# Stratégie "communicating" : smart BFS + rendezvous protocol.
# The rendezvous negotiation (PROPOSE/ACCEPT/COMMIT/CANCEL) is handled
# by _RendezvousMixin in agents.py.
# This module provides the deliberate() function that uses BFS pathfinding
# both for normal waste collection AND for navigating to/waiting at a
# rendezvous point.
################################################################################

import random
from strategies.smart_strategy import (
    _bfs, _path_to_queue, _nearest_known_waste, update_known_wastes
)


def comm_deliberate(knowledge, low_waste: int, high_waste: int, epsilon: float):
    """
    BFS deliberation for GreenAgent (low=1, high=2)
    and YellowAgent (low=2, high=3) with rendezvous support.

    Priority order:
      1. Transform (2 own-colour wastes in hand)
      2. Deposit high_waste at zone boundary
      3. Rendezvous behaviour (requester navigates; acceptor waits and picks)
      4. Opportunistic pick on current cell
      5. Opportunistic pick in immediate neighbourhood
      6. Invalidate stale BFS target
      7. Drain BFS action queue
      8. Epsilon-drop to unblock (triggers cooldown)
      9. BFS toward nearest known waste
      10. Random exploration
    """
    current_pos  = knowledge["current_pos"]
    inventory    = knowledge["inventory"]
    known_grid   = knowledge["grid"]
    known_wastes = knowledge["known_wastes"]
    action_queue = knowledge["action_queue"]
    rendezvous   = knowledge.get("rendezvous")
    max_zone     = low_waste
    x, y         = current_pos

    possible_actions = [
        {"type": "move", "target": (x, y + 1)},
        {"type": "move", "target": (x, y - 1)},
        {"type": "move", "target": (x + 1, y)},
        {"type": "move", "target": (x - 1, y)},
    ]

    # ── 1. Transform ──────────────────────────────────────────────────────────
    if len(inventory[low_waste]) == 2:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        # Rendezvous is complete once we have 2 wastes — clear it so we don't
        # remain frozen as an acceptor after picking up the dropped waste.
        knowledge["rendezvous"] = None
        return {"type": "transform"}

    # ── 2. Deposit high_waste at zone boundary ────────────────────────────────
    if len(inventory[high_waste]) == 1:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        right = (x + 1, y)
        if right in known_grid and known_grid[right]["zone"] == high_waste:
            return {"type": "put"}
        return {"type": "move", "target": (x + 1, y)}

    # ── 3. Rendezvous-driven behaviour ────────────────────────────────────────
    if rendezvous is not None:
        role       = rendezvous["role"]
        target_pos = rendezvous.get("target_pos")

        # ── ACCEPTOR ─────────────────────────────────────────────────────────
        if role == "acceptor":
            # Priority 1: pick up waste that was just dropped on our cell.
            # This MUST come before the no-op so the acceptor doesn't sit
            # on top of the waste forever without picking it up.
            if (knowledge["cooldown_remaining"] == 0 and
                    known_grid.get(current_pos, {}).get("wastes", {}).get(low_waste, 0) > 0):
                print(f"[acceptor at {current_pos}] picking up dropped waste")
                return {"type": "pick"}

            # Otherwise stay put — the requester is on its way.
            return {"type": "move", "target": current_pos}  # no-op

        # ── REQUESTER ─────────────────────────────────────────────────────────
        if role == "requester":
            if target_pos is None:
                # Still waiting for ACCEPT — keep exploring (don't pick).
                return random.choice(possible_actions)

            # Arrived at acceptor's cell → drop waste and end rendezvous.
            if current_pos == target_pos:
                knowledge["rendezvous"] = None
                knowledge["action_queue"] = []
                knowledge["target"] = None
                print(f"[requester at {current_pos}] ARRIVED — dropping waste")
                return {"type": "put"}

            # Navigate toward acceptor via BFS.
            # Re-plan whenever the queued target differs from target_pos
            # (target_pos can update if acceptor moves) or the queue is empty.
            if not action_queue or knowledge.get("target") != target_pos:
                path = _bfs(current_pos, target_pos, known_grid, max_zone)
                if path:
                    knowledge["action_queue"] = _path_to_queue(path)
                    knowledge["target"] = target_pos
                else:
                    # Path not known yet — explore randomly until the grid
                    # is filled in enough for BFS to find a route.
                    return random.choice(possible_actions)

            if action_queue:
                return action_queue.pop(0)

    # ── 4. Opportunistic pick on current cell ─────────────────────────────────
    if (knowledge["cooldown_remaining"] == 0 and
            len(inventory[low_waste]) < 2 and
            len(inventory[high_waste]) == 0 and
            known_grid.get(current_pos, {}).get("wastes", {}).get(low_waste, 0) > 0):
        knowledge["action_queue"] = []
        knowledge["target"] = None
        return {"type": "pick"}

    # ── 5. Opportunistic pick in immediate neighbourhood ──────────────────────
    if (knowledge["cooldown_remaining"] == 0 and
            len(inventory[low_waste]) < 2 and
            len(inventory[high_waste]) == 0):
        for neighbor in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if (neighbor in known_grid and
                    known_grid[neighbor]["zone"] <= max_zone and
                    known_grid[neighbor]["wastes"].get(low_waste, 0) > 0):
                knowledge["action_queue"] = [{"type": "pick"}]
                knowledge["target"] = neighbor
                return {"type": "move", "target": neighbor}

    # ── 6. Invalidate stale BFS target ────────────────────────────────────────
    target = knowledge.get("target")
    if target is not None:
        cell = known_grid.get(target, {})
        if cell.get("wastes", {}).get(low_waste, 0) == 0:
            known_wastes.pop(target, None)
            knowledge["action_queue"] = []
            knowledge["target"] = None

    # ── 7. Drain BFS action queue ─────────────────────────────────────────────
    if action_queue:
        return action_queue.pop(0)

    # ── 8. Epsilon-drop to unblock (triggers cooldown) ────────────────────────
    if len(inventory[low_waste]) == 1 and random.random() < epsilon:
        knowledge["action_queue"] = []
        knowledge["target"] = None
        return {"type": "put"}

    # ── 9. BFS toward nearest known waste ────────────────────────────────────
    if len(inventory[low_waste]) < 2:
        best_target, path = _nearest_known_waste(
            current_pos, low_waste, known_wastes, known_grid, max_zone
        )
        if best_target is not None:
            knowledge["target"] = best_target
            queue = _path_to_queue(path) + [{"type": "pick"}]
            knowledge["action_queue"] = queue
            if queue:
                return knowledge["action_queue"].pop(0)

    # ── 10. Random exploration ────────────────────────────────────────────────
    return random.choice(possible_actions)