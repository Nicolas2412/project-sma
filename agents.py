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
        self.wastes = {"green": 0, "yellow": 0, "red": 0}
        
        self.knowledge = {
            "inventory": self.wastes.copy(),
            "percepts": {},       # Will store the dictionary of adjacent cells
            "current_zone": 1,    # Default to zone 1
            "current_pos": None    # Keep track of where we are
        }
        
        self.current_percepts = None

    def step(self):
        # If it's the very first step, we need initial percepts from the model
        if self.current_percepts is None:
            self.current_percepts = self.model.get_percepts(self)
        print(self.current_percepts)

        # Update knowledge based on new percepts and current real inventory
        self.knowledge = self.update(self.knowledge, self.current_percepts)
        
        # Deliberate to choose an action (pass ONLY knowledge)
        action = self.deliberate(self.knowledge)
        
        # Do action in environment, environment returns new percepts
        self.current_percepts = self.model.do(self, action)
            
    def update(self, knowledge, percepts):
        """Updates the agent's knowledge base using the percepts dictionary."""
        knowledge["percepts"] = percepts
        
        # Update current pos WITHOUT calling self.pos inside deliberate
        knowledge["current_pos"] = percepts['pos']
        
        # Sync the knowledge inventory with the real physical inventory 
        knowledge["inventory"] = self.wastes.copy()
        
        # Determine current zone based on the Radioactivity agent in our current position
        if self.pos in percepts:
            for obj in percepts[self.pos]:
                if isinstance(obj, Radioactivity):
                    knowledge["current_zone"] = obj.zone
                    
        return knowledge
                
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
        
        # inventory = knowledge["inventory"]
        # percepts = knowledge["percepts"]
        # current_pos = knowledge["current_pos"]
        
        # # --- 1. TRANSFORMATION & PUT AWAY ---
        # if inventory["green"] >= 2:
        #     possible_actions.append({"type": "transform"})
            
        # if inventory["yellow"] > 0:
        #     possible_actions.append({"type": "put"})

        # # --- 2. PICK UP WASTE ---
        # if inventory["green"] < 2 and inventory["yellow"] == 0:
        #     if current_pos in percepts:
        #         for obj in percepts[current_pos]:
        #             if isinstance(obj, Waste) and obj.color == "green":
        #                 possible_actions.append({"type": "pick", "target": obj})

        # # --- 3. MOVEMENT ---
        # for pos, contents in percepts.items():
        #     if pos == current_pos:
        #         continue
                
        #     valid_move = True
            
        #     # DIRECTION RESTRICTION: Do not move West (pos[0] < current_pos[0]) if holding yellow waste
        #     if inventory["yellow"] > 0 and pos[0] < current_pos[0]:
        #         valid_move = False

        #     # ZONE RESTRICTION
        #     for obj in contents:
        #         if isinstance(obj, Radioactivity):
        #             if obj.zone > 1:
        #                 valid_move = False
            
        #     if valid_move:
        #         possible_actions.append({"type": "move", "target": pos})

        return random.choice(possible_actions)


class YellowAgent(Robot):
    """Yellow robot class: Handles Yellow Waste -> Red Waste"""

    def __init__(self, model):
        super().__init__( model)
        self.type = 2
    
    def deliberate(self, knowledge):
        possible_actions = [{"type": "stay"}]
        
        inventory = knowledge["inventory"]
        percepts = knowledge["percepts"]
        current_pos = knowledge["current_pos"]
        
        # --- 1. TRANSFORMATION & PUT AWAY ---
        if inventory["yellow"] >= 2:
            possible_actions.append({"type": "transform"})
            
        if inventory["red"] > 0:
            possible_actions.append({"type": "put"})

        # --- 2. PICK UP WASTE ---
        if inventory["yellow"] < 2 and inventory["red"] == 0:
            if current_pos in percepts:
                for obj in percepts[current_pos]:
                    if isinstance(obj, Waste) and obj.color == "yellow":
                        possible_actions.append({"type": "pick", "target": obj})

        # --- 3. MOVEMENT ---
        for pos, contents in percepts.items():
            if pos == current_pos:
                continue
                
            valid_move = True
            
            # DIRECTION RESTRICTION: Do not move West if holding red waste
            if inventory["red"] > 0 and pos[0] < current_pos[0]:
                valid_move = False

            # ZONE RESTRICTION
            for obj in contents:
                if isinstance(obj, Radioactivity):
                    if obj.zone > 2:
                        valid_move = False
            
            if valid_move:
                possible_actions.append({"type": "move", "target": pos})

        return random.choice(possible_actions)
    

class RedAgent(Robot):
    """Red robot class: Handles Red Waste -> Disposal Zone"""

    def __init__(self, model):
        super().__init__(model)
        self.type = 3
    
    def deliberate(self, knowledge):
        possible_actions = [{"type": "stay"}]
        
        inventory = knowledge["inventory"]
        percepts = knowledge["percepts"]
        current_pos = knowledge["current_pos"]
        
        # --- 1. PUT AWAY ---
        if inventory["red"] > 0:
            possible_actions.append({"type": "put"})

        # --- 2. PICK UP WASTE ---
        if inventory["red"] < 1:
            if current_pos in percepts:
                for obj in percepts[current_pos]:
                    if isinstance(obj, Waste) and obj.color == "red":
                        possible_actions.append({"type": "pick", "target": obj})

        # --- 3. MOVEMENT ---
        for pos, contents in percepts.items():
            if pos == current_pos:
                continue
                
            valid_move = True
            
            # DIRECTION RESTRICTION: Do not move West if holding red waste
            if inventory["red"] > 0 and pos[0] < current_pos[0]:
                valid_move = False
                
            # No zone restrictions for red robots
            if valid_move:
                possible_actions.append({"type": "move", "target": pos})

        return random.choice(possible_actions)