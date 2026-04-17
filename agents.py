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
import numpy as np
from objects import Waste, Radioactivity
import random
from strategies.naive_strategy import naive_deliberate, naive_deliberate_red
from strategies.random_strategy import random_deliberate
from strategies.smart_strategy import smart_deliberate, smart_deliberate_red, update_known_wastes

class Robot(Agent):
    """ Robot Parent class """
    def __init__(self, model, cooldown=3):
        super().__init__(model)
        
        # Real inventory (Will be modified by model.do() when actions succeed)
        self.wastes = {1: [], 2: [], 3: []}
        
        # Strictly structured knowledge base
        self.knowledge = {
            "current_pos": None,
            "inventory": self.wastes.copy(),
            "grid": {},
            "cooldown_remaining": 0,
            "known_wastes": {},
            "action_queue": [],
            "target": None,
        }
        
        self.cooldown = cooldown
        self.cooldown_remaining = 0
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
        self.knowledge["cooldown_remaining"] = percepts["cooldown_remaining"]
        update_known_wastes(self.knowledge, percepts)

    def deliberate(self, knowledge):
        """To be overridden by child classes. MUST NOT use 'self.xxx' variables."""
        pass
    

class GreenAgent(Robot):
    """Green robot class: Handles Green Waste -> Yellow Waste"""
    def __init__(self, model, strategy:str='naive'):
        super().__init__(model)
        self.type = 1
        self.epsilon = 0.05
        self.strategy = strategy
        
    def deliberate(self, knowledge):
        
        if self.strategy == 'naive':
            return naive_deliberate(knowledge=knowledge, low_waste=1, high_waste=2, epsilon=self.epsilon)
        elif self.strategy == 'random':
            return random_deliberate(knowledge=knowledge)
        elif self.strategy == 'smart':
            return smart_deliberate(knowledge=knowledge, low_waste=1, high_waste=2, epsilon=self.epsilon)
        else:
            raise ValueError("Invalid strategy: " + self.strategy)


class YellowAgent(Robot):
    """Yellow robot class: Handles Yellow Waste -> Red Waste"""
    def __init__(self, model, strategy:str='naive'):
        super().__init__(model)
        self.epsilon = 0.05
        self.type = 2
        self.strategy = strategy
    
    def deliberate(self, knowledge):

        if self.strategy == 'naive':
            return naive_deliberate(knowledge=knowledge, low_waste=2, high_waste=3, epsilon=self.epsilon)
        elif self.strategy == 'random':
            return random_deliberate(knowledge=knowledge)
        elif self.strategy == 'smart':
            return smart_deliberate(knowledge=knowledge, low_waste=2, high_waste=3, epsilon=self.epsilon)
        else:
            raise ValueError("Invalid strategy: " + self.strategy)

    

class RedAgent(Robot):
    """Red robot class: Handles Red Waste -> Disposal Zone"""
    def __init__(self, model, strategy:str='naive'):
        super().__init__(model)
        self.type = 3
        self.strategy = strategy
        
    def deliberate(self, knowledge):

        if self.strategy == 'naive':
            return naive_deliberate_red(knowledge=knowledge)
        elif self.strategy == 'random':
            return random_deliberate(knowledge=knowledge, is_red=True)
        elif self.strategy == 'smart':
            return smart_deliberate_red(knowledge=knowledge)
        else:
            raise ValueError("Invalid strategy: " + self.strategy)
