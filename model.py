################################################################################
# PROJET : SMA (Systees Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/03/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronidere
#   - Paul Guimbert
#
# FILE: model.py
################################################################################

import mesa
from agents import *
from objects import *

class RobotModel(mesa.Model):
    def __init__(self,
                n_green_agents:int,
                n_yellow_agents:int,
                n_red_agents:int,
                n_green_wastes: int,
                n_yellow_wastes: int,
                n_red_wastes: int,
                height:int,
                width_z1:int,
                width_z2:int,
                width_z3:int,
                seed = None):
        """Creates a new RobotModel

        Args:
            seed (_type_, optional): Seed for the randoms. Defaults to None.
        """
        super().__init__(seed=seed)
        
        self.n_green = n_green_agents
        self.n_yellow = n_yellow_agents
        self.n_red = n_red_agents
        self.n_green_wastes_wastes= n_green_wastes
        self.n_yellow_wastes = n_yellow_wastes
        self.n_red_wastes = n_red_wastes
        
        self.height = height
        
        self.width_z1 = width_z1
        self.width_z2 = width_z2
        self.width_z3 = width_z3
        self.total_width = width_z1 + width_z2 + width_z3

        self.grid = mesa.space.MultiGrid(self.total_width, height, False)
        
        for i in range(self.width_z1):
            for j in range(self.height):
                agent = Radioactivity(self, zone=1)
                self.grid.place_agent(agent, (i, j))
                
        for i in range(self.width_z1):
            for j in range(self.height):
                agent = Radioactivity(self, zone=2)
                self.grid.place_agent(agent, (self.width_z1 + i, j))
                
        for i in range(self.width_z1):
            for j in range(self.height):
                agent = Radioactivity(self, zone=3)
                self.grid.place_agent(
                    agent, (self.width_z1 + self.width_z2 + i, j))
        
        green_wastes = Waste.create_agents(model=self, n=n_green_wastes, color=1)
        # Create x and y positions for agents
        x = self.rng.integers(0, self.width_z1, size=(n_green_wastes,))
        y = self.rng.integers(0, self.grid.height, size=(n_green_wastes,))
        for a, i, j in zip(green_wastes, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))
            
        yellow_wastes = Waste.create_agents(
            model=self, n=n_yellow_wastes, color=2)
        # Create x and y positions for agents
        x = self.rng.integers(
            self.width_z1, self.width_z1 + self.width_z2, size=(n_yellow_wastes,))
        y = self.rng.integers(0, self.grid.height, size=(n_yellow_wastes,))
        for a, i, j in zip(yellow_wastes, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))

        red_wastes = Waste.create_agents(
            model=self, n=n_red_wastes, color=3)
        # Create x and y positions for agents
        x = self.rng.integers(self.width_z1 + self.width_z2,self.width_z1 + self.width_z2 + self.width_z3, size=(n_red_wastes,))
        y = self.rng.integers(0, self.grid.height, size=(n_red_wastes,))
        for a, i, j in zip(red_wastes, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))
            
        green_agents = GreenAgent.create_agents(model=self, n=n_green_agents)
        # Create x and y positions for agents
        x = self.rng.integers(0, self.width_z1, size=(n_green_agents,))
        y = self.rng.integers(0, self.grid.height, size=(n_green_agents,))
        for a, i, j in zip(green_agents, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))
            
            
    # def do(self, agent:mesa.Agent, action:str):
        
        # if action == "move_up":
        #     new_pos = (agent.pos[0], agent.pos[1] - 1)
        #     if self.grid.is_cell_empty(new_pos):
        #         self.model.grid.move_agent(agent, new_pos)
        #     else:
        #         pass