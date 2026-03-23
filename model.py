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
            
            
        # Initialization of the data collector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Green Waste": lambda m: sum(1 for a in m.agents if isinstance(a, Waste) and a.color == 1),
                "Yellow Waste": lambda m: sum(1 for a in m.agents if isinstance(a, Waste) and a.color == 2),
                "Red Waste": lambda m: sum(1 for a in m.agents if isinstance(a, Waste) and a.color == 3),
            }
        )
        
        # Initialize grid cach, used to improve computation 
        self._grid_cache = {}
        for _, pos in self.grid.coord_iter():
            self._update_cache_at(pos)

    def do(self, agent:Robot, action:str):
        
        action_type = action["type"]
        agent.cooldown_remaining = max(0, agent.cooldown_remaining - 1)
        
        if action_type == "move": 
            new_pos = action["target"]
            if not self.grid.out_of_bounds(new_pos) and self._grid_cache[new_pos]["zone"] <= agent.type:
                    old_pos = agent.pos
                    self.grid.move_agent(agent, new_pos)
                    self._update_cache_at(old_pos)
                    self._update_cache_at(new_pos)
        
        elif action_type == "pick":
            if (isinstance(agent, RedAgent) and len(agent.wastes[agent.type]) == 1) or \
                ((isinstance(agent, YellowAgent) or isinstance(agent, GreenAgent)) and \
                    (len(agent.wastes[agent.type]) == 2 or len(agent.wastes[agent.type + 1]) == 1)):
                pass #Action not feasable
            elif self._grid_cache[agent.pos]["wastes"][agent.type] > 0:
                agents_on_pos = self.grid.get_cell_list_contents([agent.pos])
                for agent_on_pos in agents_on_pos:
                    if isinstance(agent_on_pos, Waste) and agent_on_pos.color == agent.type:
                        agent.wastes[agent.type].append(agent_on_pos)
                        self.grid.remove_agent(agent_on_pos)
                        self._update_cache_at(agent.pos)
                        break
                
        elif action_type == "put":
            current_zone = self._grid_cache[agent.pos]["zone"]

            if isinstance(agent, RedAgent):
                if len(agent.wastes[agent.type]) == 1 and self._grid_cache[agent.pos]["drop"]:
                    waste = agent.wastes[agent.type].pop()
                    waste.remove()
                    agent.wastes[agent.type] = []
                    self._update_cache_at(agent.pos)
                    
            elif len(agent.wastes[agent.type + 1]) == 1 and current_zone == agent.type : #Normal put in the frontier of next zone
                waste = agent.wastes[agent.type + 1].pop()
                self.grid.place_agent(waste, agent.pos)
                agent.wastes[agent.type + 1] = []
                self._update_cache_at(agent.pos)
                
            elif len(agent.wastes[agent.type]) == 1 and current_zone == agent.type: #Random drop
                waste = agent.wastes[agent.type].pop()
                self.grid.place_agent(waste, agent.pos)
                agent.wastes[agent.type] = []
                self._update_cache_at(agent.pos)
                agent.cooldown_remaining = agent.cooldown

        elif action_type == "transform":
            if len(agent.wastes[agent.type]) == 2:
                # Supprimer les 2 déchets portés
                for waste in agent.wastes[agent.type]:
                    waste.remove()
                agent.wastes[agent.type] = []
                # Créer le nouveau déchet de niveau supérieur
                new_waste = Waste(self, color=agent.type + 1)
                agent.wastes[agent.type + 1].append(new_waste)
                
        else:
            raise ValueError(f"Unknown action type: {action_type}")
                
        percepts = self.get_percepts(agent)
        return percepts
    
    def get_percepts(self, agent: Robot):
        percepts = {'current_pos': agent.pos, 'cooldown_remaining': agent.cooldown_remaining, 'grid': {}}
        neighboor_positions = self.grid.get_neighborhood(agent.pos, moore=True, include_center=True)
        for pos in neighboor_positions:
            if pos in self._grid_cache:
                percepts["grid"][pos] = self._grid_cache[pos]
        return percepts
    
    def _update_cache_at(self, pos):    
        """Recompute cache for a single cell."""
        agents_at_pos = self.grid.get_cell_list_contents([pos])
        sq_info = {
            "radioactivity_level": None,
            "zone": 1,
            "wastes": {1: 0, 2: 0, 3: 0},
            "drop": False
        }
        for obj in agents_at_pos:
            if isinstance(obj, Radioactivity):
                sq_info["zone"] = obj.type
                sq_info["radioactivity_level"] = getattr(obj, 'level', None)
                if isinstance(obj, WasteDisposalZone):
                    sq_info["drop"] = True
            elif isinstance(obj, Waste):
                sq_info["wastes"][obj.color] += 1
        self._grid_cache[pos] = sq_info
    
    def step(self):
        """do one step of the model"""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        
        green_count = sum(
            1 for a in self.agents if isinstance(a, Waste) and a.color == 1
        )
        
        yellow_count = sum(
            1 for a in self.agents if isinstance(a, Waste) and a.color == 2
        )

        red_count = sum(
            1 for a in self.agents if isinstance(a, Waste) and a.color == 3
        )
        if green_count < 2 and yellow_count < 2 and red_count == 0:
            self.running = False
