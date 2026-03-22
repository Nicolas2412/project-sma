################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/03/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronnière
#   - Paul Guimbert
#
# FILE: agents.py
################################################################################

from mesa import Agent
from objects import Waste, Radioactivity
import random

class Robot(Agent):
    """ Robot Parent class """
    def __init__(self, model):
        super().__init__(model)
        
        # Real inventory (Will be modified by model.do() when actions succeed)
        self.wastes = {1: [], 2: [], 3: []}
        
        # Strictly structured knowledge base
        self.knowledge = {
            "current_pos": None,
            "inventory": self.wastes.copy(),
            "grid": {}
        }
        
        self.current_percepts = None

    def step(self):
        # If it's the very first step, we need initial percepts from the model
        if not self.current_percepts:
            self.current_percepts = self.model.get_percepts(self)

        # Update knowledge based on new percepts and current real inventory
        self.update(self.current_percepts)
        # Deliberate to choose an action (pass ONLY knowledge)
        action = self.deliberate(self.knowledge)
        
        # Do action in environment, environment returns new percepts
        # percepts format: {"current_pos": (x, y), "adjency_grid": {(x, y): [agents]}}
        self.current_percepts = self.model.do(self, action)
        
    def update(self, percepts):
        """
        Updates the agent's knowledge base using the percepts dictionary.
        Parses raw agents into pure data for the reasoning engine.
        Handles int-to-string mapping for Waste colors (1: green, 2: yellow, 3: red).
        """
        # 1. Update Position directly from percepts
        self.knowledge["current_pos"] = percepts["current_pos"]
        
        # 2. Sync the knowledge inventory with the real physical inventory 
        self.knowledge["inventory"] = self.wastes.copy()
        
        self.knowledge["grid"].update(percepts["grid"])
        

    def deliberate(self, knowledge):
        """To be overridden by child classes. MUST NOT use 'self.xxx' variables."""
        pass
    

class GreenAgent(Robot):
    """Green robot class: Handles Green Waste -> Yellow Waste"""
    def __init__(self, model):
        super().__init__(model)
        self.type = 1
    
    def deliberate(self, knowledge):
        # "stay" acts as a fallback so random.choice() never crashes.
        # possible_actions = [{"type": "stay"}] 
        x, y = knowledge["current_pos"]
        
        possible_actions = [{"type": "move", "target": (x, y +1)},
                            {"type": "move", "target": (x , y -1)},
                            {"type": "move", "target": (x + 1, y)},
                            {"type": "move", "target": (x + -1, y)}
                            ] 
        
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        
        # Transformation
        if len(inventory[1]) == 2:
            return {"type": "transform"}
        
        # Puting away
        x,y = current_pos
        if len(inventory[2]) == 1 and self.knowledge["grid"][(x+1, y)]["zone"] == self.type+1:
            return {"type": "put"}

        # # --- 2. PICK UP WASTE ---
        # # Look at the parsed data for our current coordinate
        if len(inventory[1]) < 2 and len(inventory[2]) == 0 and \
            knowledge['grid'][current_pos]['wastes'][1] > 0:
            return {"type": "pick"}
        
        # # --- 3. MOVEMENT ---
        
        if len(inventory[2]) == 1:
            x, y = current_pos
            return {"type": "move", "target": (x + 1, y)}
        
        return random.choice(possible_actions)


class YellowAgent(Robot):
    """Yellow robot class: Handles Yellow Waste -> Red Waste"""
    def __init__(self, model):
        super().__init__(model)
        self.type = 2
    
    def deliberate(self, knowledge):
        x, y = knowledge["current_pos"]

        possible_actions = [{"type": "move", "target": (x, y + 1)},
                            {"type": "move", "target": (x, y - 1)},
                            {"type": "move", "target": (x + 1, y)},
                            {"type": "move", "target": (x + -1, y)}
                            ]

        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]

        # Transformation
        if len(inventory[2]) == 2:
            return {"type": "transform"}

        # Puting away
        x, y = current_pos
        if len(inventory[3]) == 1 and self.knowledge["grid"][(x+1, y)]["zone"] == self.type+1:
            return {"type": "put"}

        # # --- 2. PICK UP WASTE ---
        # # Look at the parsed data for our current coordinate
        if len(inventory[2]) < 2 and len(inventory[3]) == 0 and \
                knowledge['grid'][current_pos]['wastes'][2] > 0:
            return {"type": "pick"}

        # # --- 3. MOVEMENT ---

        if len(inventory[3]) == 1:
            x, y = current_pos
            return {"type": "move", "target": (x + 1, y)}

        return random.choice(possible_actions)
    

class RedAgent(Robot):
    """Red robot class: Handles Red Waste -> Disposal Zone"""
    def __init__(self, model):
        super().__init__(model)
        self.type = 3
        
    def deliberate(self, knowledge):
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

        # Si déchet rouge + pas à l'extrémité droite -> move droite
        if len(inventory[3]) == 1 and x < self.model.total_width - 1:
            return {"type": "move", "target": (x + 1, y)}

        # Si déchet rouge + à l'extrémité droite -> move haut ou bas
        if len(inventory[3]) == 1 and x == self.model.total_width - 1:
            return random.choice([
                {"type": "move", "target": (x, y + 1)},
                {"type": "move", "target": (x, y - 1)}
            ])

        # Si déchet rouge sur la case -> pick
        if len(inventory[3]) == 0 and knowledge["grid"][current_pos]["wastes"][3] > 0:
            return {"type": "pick"}

        # Sinon -> move aléatoire
        return random.choice(possible_actions)
