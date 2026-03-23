import random

def random_deliberate(knowledge, is_red:bool=False):
    """naive strategy used for green and yellow agents"""

    x, y = knowledge["current_pos"]

    possible_actions = [{"type": "move", "target": (x, y + 1)},
                        {"type": "move", "target": (x, y - 1)},
                        {"type": "move", "target": (x + 1, y)},
                        {"type": "move", "target": (x + -1, y)},
                        {"type": "put"},
                        {"type": "pick"},
                        ]
    
    if not is_red:
        possible_actions.append({"type":"transform"})

    return random.choice(possible_actions)