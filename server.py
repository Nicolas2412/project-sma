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
    "width_z2" : 10,
    "width_z3" : 10,
    }

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
        portrayal["size"] = 500
        portrayal["zorder"] = 0

        if agent.zone == 1:
            portrayal["color"] = "#73ff78"  # Vert clair
        elif agent.zone == 2:
            portrayal["color"] = "#ffe482"  # Jaune clair
        elif agent.zone == 3:
            portrayal["color"] = "#f59188"  # Rouge clair
            
    elif isinstance(agent, Waste):
        # On définit la couleur selon la zone
        portrayal["marker"] = "o"
        portrayal["size"] = 10
        portrayal["zorder"] = 1
        
        if agent.color == 1:
            portrayal["color"] = "#29a918"  # Vert clair
        elif agent.color == 2:
            portrayal["color"] = "#ecac0a"  # Jaune clair
        elif agent.color == 3:
            portrayal["color"] = "#e41300"  # Rouge clair

    return portrayal

model = RobotModel(**model_params, seed=0)

SpaceGraph = make_space_component(agent_portrayal, post_process=configure_axes)


# Create the Dashboard
page = SolaraViz(
    model,
    components=[SpaceGraph],
    model_params=model_params,
    name="Waste Collection",
)
# This is required to render the visualization in the Jupyter notebook
page
# to start : "solara run server.py"
