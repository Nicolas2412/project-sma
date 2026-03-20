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
        super().__init__(rng=seed)
        
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
        
        # for j in range(self.height):
        #     agent = WasteDisposalZone(self, zone=1)
        #     self.grid.place_agent(agent, (self.width_z1-1, j))
            
        for i in range(self.width_z1, self.width_z1 + self.width_z2):
            for j in range(self.height):
                agent = Radioactivity(self, zone=2)
                self.grid.place_agent(agent, (i, j))
        
        # for j in range(self.height):
        #     agent = WasteDisposalZone(self, zone=2)
        #     self.grid.place_agent(
        #         agent, (self.width_z1 + self.width_z2 - 1, j))
            
        for i in range(self.width_z1 + self.width_z2, self.total_width):
            if i == self.total_width-1:
                disposal = self.rng.integers(0, self.height)
            for j in range(self.height):
                if i == self.total_width-1 and j == disposal:
                    agent = WasteDisposalZone(self, zone=3)
                else:
                    agent = Radioactivity(self, zone=3)
                self.grid.place_agent(agent, (i, j))
        
        
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
            
        yellow_agents = YellowAgent.create_agents(
            model=self, n=n_yellow_agents)
        # Create x and y positions for agents
        x = self.rng.integers(self.width_z1, self.width_z1 + self.width_z2, size=(n_yellow_agents,))
        y = self.rng.integers(0, self.grid.height, size=(n_yellow_agents,))
        for a, i, j in zip(yellow_agents, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))
            
        red_agents = RedAgent.create_agents(
            model=self, n=n_red_agents)
        # Create x and y positions for agents
        x = self.rng.integers(self.width_z1 + self.width_z2, self.width_z1 +
                            self.width_z2 + self.width_z3, size=(n_red_agents,))
        y = self.rng.integers(0, self.grid.height, size=(n_red_agents,))
        for a, i, j in zip(red_agents, x, y):
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (i, j))
            
    def do(self, agent:Robot, action:str):
        action_type = action["type"]
        
        if action_type == "move": 
            new_pos = action["target"]
            if not self.grid.out_of_bounds(new_pos):
            
                agents_on_new_pos = self.grid.get_cell_list_contents([new_pos])
                perform = True
                for agent_on_new_pos in agents_on_new_pos:
                    if not isinstance(agent_on_new_pos, Radioactivity):
                        pass
                    else:
                        if agent.type < agent_on_new_pos.type:
                            # Invalid action
                            perform = False
                if perform:
                    self.grid.move_agent(agent, new_pos)
        
        elif action_type == "pick":
            if (isinstance(agent, RedAgent) and agent.wastes[agent.type] == 1) or \
                ((isinstance(agent, YellowAgent) or isinstance(agent, GreenAgent)) and \
                    (agent.wastes[agent.type] == 2 or agent.wastes[agent.type + 1] == 1)):
                pass #Action not feasable
            else:
                agents_on_new_pos = self.grid.get_cell_list_contents([agent.pos])
                for agent_on_new_pos in agents_on_new_pos:
                    if isinstance(agent_on_new_pos, Waste) and agent_on_new_pos.color == agent.type:
                        agent.wastes[agent.type] += 1
                        self.grid.remove_agent(agent_on_new_pos)
                        break
                    
        elif action_type == "put":
            agents_on_pos = self.grid.get_cell_list_contents([agent.pos])
            for agent_on_pos in agents_on_pos:
                if isinstance(agent, RedAgent):
                    if agent.wastes[agent.type] == 1:
                        agent.wastes[agent.type] -= 1
                        break
                else:
                    if agent.wastes[agent.type+1] == 1:
                        agent.wastes[agent.type+1] = 0
                        waste= Waste(self, agent.type+1)
                        self.grid.place_agent(waste, agent.pos)
                        break
                
        elif action_type == "transform":
            if agent.wastes[agent.type] == 2:
                agent.wastes[agent.type] = 0
                agent.wastes[agent.type + 1] = 1

        else:
            raise ValueError(f"Unknown action type: {action_type}")
                
        percepts = self.get_percepts(agent)
        return percepts
    

    def get_percepts(self, agent:Robot):
        
        percepts = {'current_pos': agent.pos,
                    'grid': {}}
        
        neighboor_positions = self.grid.get_neighborhood(agent.pos, moore=True, include_center=True)
        
        
        for pos in neighboor_positions:
            agents_at_pos = self.grid.get_cell_list_contents([pos])

            # Default information for a square
            sq_info = {
                "radioactivity_level": None,
                "zone": 1,  # Defaults to 1 if no radioactivity agent is found
                "wastes": {1: 0, 2: 0, 3: 0},
                "drop":False
            }

            for obj in agents_at_pos:
                
                if isinstance(obj, Radioactivity):
                    sq_info["zone"] = obj.type
                    sq_info["radioactivity_level"] = getattr(
                        obj, 'level', None)
                    if isinstance(obj, WasteDisposalZone):
                        sq_info["drop"] = True
                
                elif isinstance(obj, Waste):
                    # Translate integer to string key using the map
                    sq_info["wastes"][obj.color] += 1
            
            percepts["grid"][pos] = sq_info
            
        return percepts
        
    def step(self):
        """do one step of the model"""
        self.agents.shuffle_do("step")