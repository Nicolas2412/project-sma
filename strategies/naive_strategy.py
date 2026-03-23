import random

def naive_deliberate(knowledge, low_waste:int, high_waste:int, epsilon:float):
    """naive strategy used for green and yellow agents"""

    x, y = knowledge["current_pos"]

    possible_actions = [{"type": "move", "target": (x, y + 1)},
                        {"type": "move", "target": (x, y - 1)},
                        {"type": "move", "target": (x + 1, y)},
                        {"type": "move", "target": (x + -1, y)}
                        ]

    current_pos = knowledge["current_pos"]
    inventory = knowledge["inventory"]

    # Transformation
    if len(inventory[low_waste]) == 2:
        return {"type": "transform"}

    # Puting away
    x, y = current_pos
    if len(inventory[high_waste]) == 1 and knowledge["grid"][(x+1, y)]["zone"] == high_waste:
        return {"type": "put"}

    # # --- 2. PICK UP WASTE ---
    # # Look at the parsed data for our current coordinate
    if len(inventory[low_waste]) < 2 and len(inventory[high_waste]) == 0 and \
            knowledge['grid'][current_pos]['wastes'][low_waste] > 0 and knowledge["cooldown_remaining"] == 0:
        return {"type": "pick"}

    # # --- 3. MOVEMENT ---
    if len(inventory[high_waste]) == 1:
        x, y = current_pos
        return {"type": "move", "target": (x + 1, y)}

    # Drop if holding one low level item with a little probabilty
    if len(inventory[low_waste]) == 1 and random.random() < epsilon:
        return {"type": "put"}

    return random.choice(possible_actions)

def naive_deliberate_red(knowledge):
    x, y = knowledge["current_pos"]

    possible_actions = [{"type": "move", "target": (x, y + 1)},
                        {"type": "move", "target": (x, y - 1)},
                        {"type": "move", "target": (x + 1, y)},
                        {"type": "move", "target": (x - 1, y)}
                        ]

    current_pos = knowledge["current_pos"]
    inventory = knowledge["inventory"]

    # Si déchet rouge + sur zone de dépôt -> put
    if len(inventory[3]) == 1 and knowledge["grid"][current_pos]["drop"] and knowledge["grid"][current_pos]["zone"] == 3:
        return {"type": "put"}

    # Si déchet rouge + pas à l'extrémité droite (<=> la case de droite est dans le knowledge) -> move droite
    if len(inventory[3]) == 1 and (x + 1, y) in knowledge["grid"]:
        return {"type": "move", "target": (x + 1, y)}

    # Si déchet rouge + à l'extrémité droite -> move haut ou bas
    if len(inventory[3]) == 1 and (x + 1, y) not in knowledge["grid"]:
        return random.choice([
            {"type": "move", "target": (x, y + 1)},
            {"type": "move", "target": (x, y - 1)}
        ])

    # Si déchet rouge sur la case -> pick
    if len(inventory[3]) == 0 and knowledge["grid"][current_pos]["wastes"][3] > 0:
        return {"type": "pick"}

    # Sinon -> move aléatoire
    return random.choice(possible_actions)
