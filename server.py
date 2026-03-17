################################################################################
# PROJET : SMA (Systees Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/03/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronidere
#   - Paul Guimbert
#
# FILE: server.py
################################################################################

import mesa
import solara
from agents import *
from objects import *
from model import RobotModel
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle
import warnings
warnings.filterwarnings("ignore", message=".*unfilled marker.*")

model_params = {
    "n_green_agents" : 1,
    "n_yellow_agents" : 2,
    "n_red_agents" : 2,
    "n_green_wastes" : 20,
    "n_yellow_wastes" : 2,
    "n_red_wastes" : 2,
    "height" : 10,
    "width_z1" : 10,
    "width_z2" : 5,
    "width_z3" : 3,
    }


style = """
    .mesa-viz-component {
        width: 100% !important;
        max-width: none !important;
    }
    .v-card {
        width: 100% !important;
    }
"""


def configure_axes(ax):
    ax.set_aspect('equal', adjustable='box') # Force le ratio 1:1
    ax.axis('off')                            # Supprime les numéros (0, 5, 10...)
    return ax


def agent_portrayal(agent):
    if isinstance(agent, WasteDisposalZone):
        colors = {1: "#73ff78", 2: "#ffe482", 3: "#f59188"}
        return AgentPortrayalStyle(marker="s", 
                                color=colors[agent.type],  
                                size=None, 
                                zorder=1, 
                                edgecolors="black",
                                linewidths=0.5)

    elif isinstance(agent, Radioactivity):
        colors = {1: "#73ff78", 2: "#ffe482", 3: "#f59188"}
        return AgentPortrayalStyle(marker="s", color=colors[agent.type], size=None, zorder=1)

    elif isinstance(agent, Waste):
        colors = {1: "#165c0c", 2: "#ff8000", 3: "#cd1a06"}
        return AgentPortrayalStyle(marker="s", color=colors[agent.color], size=10, zorder=10)

    elif isinstance(agent, Robot):
        if isinstance(agent, GreenAgent):
            color = "#165c0c"
        elif isinstance(agent, YellowAgent):
            color = "#ff8000"
        elif isinstance(agent, RedAgent):
            color = "#cd1a06"
        return AgentPortrayalStyle(marker="o", color=color, size=80, zorder=20)

model = RobotModel(**model_params, seed=0)

SpaceGraph = make_space_component(agent_portrayal, 
                                post_process=configure_axes)


# Create the Dashboard
@solara.component
def StyledDashboard():
    solara.Style(style)
    SolaraViz(
        model,
        components=[SpaceGraph],
        model_params=model_params,
    )


# This is required to render the visualization in the Jupyter notebook
page = StyledDashboard()
# to start : "solara run server.py"
