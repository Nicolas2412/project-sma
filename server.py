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

from matplotlib.figure import Figure
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import mesa
import solara
from agents import *
from objects import *
from model import RobotModel
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle
import warnings
from mesa.visualization.utils import update_counter

warnings.filterwarnings("ignore", message=".*unfilled marker.*")

model_params = {
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Height:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "width_z1": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 1:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "width_z2": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 2:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "width_z3": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 3:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_green_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of green agents:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_yellow_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of yellow agents:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_red_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of red agents:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_green_wastes": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of green wastes:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_yellow_wastes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of yellow wastes:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_red_wastes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of red wastes:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    }

initial_params = {
    "n_green_agents": 10,
    "n_yellow_agents": 10,
    "n_red_agents": 10,
    "n_green_wastes": 10,
    "n_yellow_wastes": 10,
    "n_red_wastes": 10,
    "height": 10,
    "width_z1": 10,
    "width_z2": 10,
    "width_z3": 10,
}

style = """
    .widget-image {
        width: 80% !important;
        height: 80% !important;
        object-fit: contain !important;
    }
"""

def configure_axes(ax):
    ax.set_aspect('equal', adjustable='box') # Force le ratio 1:1
    ax.axis('off')
    for line in ax.get_lines():
        line.set_color("#4e4e4e")   # color
        line.set_linewidth(0.7)     # thickness
        line.set_linestyle("-")    # '--', ':', '-', '-.'
        line.set_alpha(0.4)         # transparency
    return ax


def agent_portrayal(agent):

    if isinstance(agent, Radioactivity):
        if agent.type == 1:
            # 0 to 1/3: very pale to medium green
            low, high = "#cfffc4", "#5bff45"
        elif agent.type == 2:
            # 1/3 to 2/3: very pale to medium yellow
            low, high = "#fbffc2", "#fff825"
        elif agent.type == 3:
            # 2/3 to 1: very pale to medium red
            low, high = "#ffaea5", "#ff4343"

        zone_ranges = {1: (0, 1/3), 2: (1/3, 2/3), 3: (2/3, 1)}
        zone_min, zone_max = zone_ranges[agent.type]
        norm = np.clip((agent.radioactivity - zone_min) /
                    (zone_max - zone_min), 0, 1)

        low_rgb = mcolors.to_rgb(low)
        high_rgb = mcolors.to_rgb(high)

        r = low_rgb[0] + norm * (high_rgb[0] - low_rgb[0])
        g = low_rgb[1] + norm * (high_rgb[1] - low_rgb[1])
        b = low_rgb[2] + norm * (high_rgb[2] - low_rgb[2])

        color = mcolors.to_hex((r, g, b))
        if isinstance(agent, WasteDisposalZone):
            return AgentPortrayalStyle(marker="s", color=color, size=100, zorder=1, edgecolors="black", linewidths=0.5)
        return AgentPortrayalStyle(marker="s", color=color, size=100, zorder=1)

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
        return AgentPortrayalStyle(marker="o", color=color, size=70, zorder=20)

model = RobotModel(**initial_params)
SpaceGraph = make_space_component(agent_portrayal, 
                                post_process=configure_axes)


def remove_legend(ax):
    ax.get_legend().remove()
    ax.set_ylim(bottom=0)
    return ax


WastePlot = make_plot_component(
    {"Green Waste": "green", "Yellow Waste": "orange", "Red Waste": "red"}, post_process=remove_legend)


# Create the Dashboard
@solara.component
def StyledDashboard():
    solara.Style(style)
    SolaraViz(
        model,
        components=[SpaceGraph, WastePlot],
        model_params=model_params,
    )


# This is required to render the visualization in the Jupyter notebook
page = StyledDashboard()
# to start : "solara run server.py"
