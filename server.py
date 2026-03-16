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

model_params = {
    "n_green_agents" : 2,
    "n_yellow_agents" : 2,
    "n_red_agents" : 2,
    "n_green_wastes" : 2,
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
    # Dictionnaire avec des clés standard Matplotlib
    portrayal = {}

    if isinstance(agent, Radioactivity):
        # On définit la couleur selon la zone
        portrayal["marker"] = "s"
        portrayal["size"] = 50
        portrayal["zorder"] = 0

        if agent.type == 1:
            portrayal["color"] = "#73ff78"  # Vert clair
        elif agent.type == 2:
            portrayal["color"] = "#ffe482"  # Jaune clair
        elif agent.type == 3:
            portrayal["color"] = "#f59188"  # Rouge clair
            
    elif isinstance(agent, Waste):
        # On définit la couleur selon la zone
        portrayal["marker"] = "o"
        portrayal["size"] = 50
        portrayal["zorder"] = 1
        
        if agent.color == 1:
            portrayal["color"] = "#29a918"  # Vert clair
        elif agent.color == 2:
            portrayal["color"] = "#ecac0a"  # Jaune clair
        elif agent.color == 3:
            portrayal["color"] = "#e41300"  # Rouge clair
            
    elif isinstance(agent, GreenAgent):
        # On définit la couleur selon la zone
        portrayal["marker"] = "o"
        portrayal["size"] = 50
        portrayal["zorder"] = 1
        portrayal["color"] = "#154e0e"
        
    elif isinstance(agent, YellowAgent):
        # On définit la couleur selon la zone
        portrayal["marker"] = "o"
        portrayal["size"] = 50
        portrayal["zorder"] = 1
        portrayal["color"] = "#884400"
        
    elif isinstance(agent, RedAgent):
        # On définit la couleur selon la zone
        portrayal["marker"] = "o"
        portrayal["size"] = 50
        portrayal["zorder"] = 1
        portrayal["color"] = "#3c0000"
        
    return portrayal

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
