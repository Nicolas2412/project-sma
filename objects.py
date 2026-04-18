from mesa import Agent, Model
import random as rd

class Radioactivity(Agent):
    def __init__(self, model:Model, zone:int):
        """Create a new Racioactivity agent.

        Args:
            model (Model): The model instance that contains the agent
        """
        super().__init__(model)

        self.type = zone
        self.radioactivity = ((zone - 1) / 3) + rd.uniform(0, 1/3)


class WasteDisposalZone(Radioactivity):
    def __init__(self, model: Model, zone: int):
        """Create a new WasteDisposalZone agent.

        Args:
            model (Model): The model instance that contains the agent
            zone (int): The zone in wich the agent is (1, 2 or 3)
        """
        super().__init__(model, zone)


class Waste(Agent):
    def __init__(self, model: Model, color:int):
        """Create a new Waste agent.

        Args:
            model (Model): The model instance that contains the agent
            color (str): The color of the waste (1:'green', 2:'yellow' or 3:'red')
        """
        super().__init__(model)
        
        self.color = color
