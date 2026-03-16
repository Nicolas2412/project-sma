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
        
        # Strictly structured knowledge base
        self.knowledge = {
            "current_pos": None,
            "inventory": self.wastes.copy(),
            "adjacent_squares": {}
        }
        
        self.current_percepts = {}

    def step(self):
        # If it's the very first step, we need initial percepts from the model
        if not self.current_percepts:
            self.current_percepts = self.model.get_initial_percepts(self)

        # Update knowledge based on new percepts and current real inventory
        self.knowledge = self.update(self.knowledge, self.current_percepts)
        
        # Deliberate to choose an action (pass ONLY knowledge)
        action = self.deliberate(self.knowledge)
        
        # Do action in environment, environment returns new percepts
        # percepts format: {"current_pos": (x, y), "adjacency_grid": {(x, y): [agents]}}
        self.current_percepts = self.model.do(self, action)
            
    def update(self, knowledge, percepts):
        """
        Updates the agent's knowledge base using the percepts dictionary.
        Parses raw agents into pure data for the reasoning engine.
        Handles int-to-string mapping for Waste colors (1: green, 2: yellow, 3: red).
        """
        # 1. Update Position directly from percepts
        knowledge["current_pos"] = percepts["current_pos"]
        
        # 2. Sync the knowledge inventory with the real physical inventory 
        knowledge["inventory"] = self.wastes.copy()
        
        # Map integer colors to our string-based data structure
        color_mapping = {1: "green", 2: "yellow", 3: "red"}
        
        # 3. Parse adjacency_grid into clean data for adjacent_squares
        parsed_squares = {}
        for pos, agents_list in percepts["adjacency_grid"].items():
            
            # Default information for a square
            sq_info = {
                "radioactivity_level": None,
                "zone": 1, # Defaults to 1 if no radioactivity agent is found
                "wastes": {"green": 0, "yellow": 0, "red": 0}
            }
            
            for obj in agents_list:
                if isinstance(obj, Radioactivity):
                    sq_info["zone"] = obj.zone
                    sq_info["radioactivity_level"] = getattr(obj, 'level', None) 
                
                elif isinstance(obj, Waste):
                    # Translate integer to string key using the map
                    color_name = color_mapping.get(obj.color)
                    sq_info["wastes"][color_name] += 1
                        
            parsed_squares[pos] = sq_info
            
        knowledge["adjacent_squares"] = parsed_squares
                    
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
        possible_actions = [{"type": "stay"}] 
        
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        adj_squares = knowledge["adjacent_squares"]
        
        # --- 1. TRANSFORMATION & PUT AWAY ---
        if inventory["green"] >= 2:
            possible_actions.append({"type": "transform"})
            
        if inventory["yellow"] > 0:
            possible_actions.append({"type": "put"})

        # --- 2. PICK UP WASTE ---
        # Look at the parsed data for our current coordinate
        if inventory["green"] < 2 and inventory["yellow"] == 0:
            if current_pos in adj_squares:
                if adj_squares[current_pos]["wastes"]["green"] > 0:
                    # We no longer pass the raw object. We pass the INTENT to pick a color.
                    possible_actions.append({"type": "pick"})

        # --- 3. MOVEMENT ---
        for pos, sq_info in adj_squares.items():
            if pos == current_pos:
                continue
                
            valid_move = True
            
            # DIRECTION RESTRICTION: Do not move West if holding yellow waste
            if inventory["yellow"] > 0 and pos[0] < current_pos[0]:
                valid_move = False

            # ZONE RESTRICTION
            if sq_info["zone"] > 1:
                valid_move = False
            
            if valid_move:
                possible_actions.append({"type": "move", "target": pos})

        return random.choice(possible_actions)


class YellowAgent(Robot):
    """Yellow robot class: Handles Yellow Waste -> Red Waste"""
    def __init__(self, model):
        super().__init__(model)
        self.type = 2
    
    def deliberate(self, knowledge):
        possible_actions = [{"type": "stay"}]
        
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        adj_squares = knowledge["adjacent_squares"]
        
        # --- 1. TRANSFORMATION & PUT AWAY ---
        if inventory["yellow"] >= 2:
            possible_actions.append({"type": "transform"})
            
        if inventory["red"] > 0:
            possible_actions.append({"type": "put"})

        # --- 2. PICK UP WASTE ---
        if inventory["yellow"] < 2 and inventory["red"] == 0:
            if current_pos in adj_squares:
                if adj_squares[current_pos]["wastes"]["yellow"] > 0:
                    possible_actions.append({"type": "pick"})

        # --- 3. MOVEMENT ---
        for pos, sq_info in adj_squares.items():
            if pos == current_pos:
                continue
                
            valid_move = True
            
            # DIRECTION RESTRICTION: Do not move West if holding red waste
            if inventory["red"] > 0 and pos[0] < current_pos[0]:
                valid_move = False

            # ZONE RESTRICTION
            if sq_info["zone"] > 2:
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
        
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        adj_squares = knowledge["adjacent_squares"]
        
        # --- 1. PUT AWAY ---
        if inventory["red"] > 0:
            possible_actions.append({"type": "put"})

        # --- 2. PICK UP WASTE ---
        if inventory["red"] < 1:
            if current_pos in adj_squares:
                if adj_squares[current_pos]["wastes"]["red"] > 0:
                    possible_actions.append({"type": "pick"})

        # --- 3. MOVEMENT ---
        for pos, sq_info in adj_squares.items():
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