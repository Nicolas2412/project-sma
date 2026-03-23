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
from mesa import DataCollector
import pandas as pd

warnings.filterwarnings("ignore", message=".*unfilled marker.*")

# Fix the datacollector class
original_get = DataCollector.get_model_vars_dataframe

def safe_get_model_vars_dataframe(self):
    try:
        return original_get(self)
    except ValueError:
        min_len = min(len(v) for v in self.model_vars.values())
        truncated = {k: v[:min_len] for k, v in self.model_vars.items()}
        return pd.DataFrame(truncated)

DataCollector.get_model_vars_dataframe = safe_get_model_vars_dataframe

model_params = {
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Height:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "width_z1": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 1:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "width_z2": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 2:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "width_z3": {
        "type": "SliderInt",
        "value": 10,
        "label": "Width of zone 3:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_green_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of green agents:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_yellow_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of yellow agents:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_red_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of red agents:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_green_wastes": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of green wastes:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_yellow_wastes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of yellow wastes:",
        "min": 1,
        "max": 100,
        "step": 1,
    },
    "n_red_wastes": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of red wastes:",
        "min": 1,
        "max": 100,
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
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.set_xlim(xlim[0] + 0.0, xlim[1] + 0.0)
    ax.set_ylim(ylim[0] + 0.0, ylim[1] + 0.0)
    n_cols = int(xlim[1] - xlim[0])
    n_rows = int(ylim[1] - ylim[0])

    # Supprimer les lignes de grille de Mesa
    for line in ax.get_lines():
        line.remove()

    # Redessiner la grille alignée avec les markers
    for x in range(n_cols + 1):
        ax.axvline(x - 0.5, color="#4e4e4e", linewidth=0.7, alpha=0.4)
    for y in range(n_rows + 1):
        ax.axhline(y - 0.5, color="#4e4e4e", linewidth=0.7, alpha=0.4)

    fig = ax.get_figure()
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width_inches = bbox.width
    height_inches = bbox.height

    cell_width_pts = (width_inches * 72) / n_cols
    cell_height_pts = (height_inches * 72) / n_rows
    cell_pts = min(cell_width_pts, cell_height_pts)
    
    for collection in ax.collections:
        zorder = collection.get_zorder()
        if zorder == 1:
            collection.set_sizes([cell_pts ** 2])
        elif zorder == 10:
            collection.set_sizes([(cell_pts * 0.3) ** 2])
        elif zorder == 20:
            collection.set_sizes([(cell_pts * 0.7) ** 2])

    return ax

def agent_portrayal(agent):
    
    cell_size = 1
    
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
            return AgentPortrayalStyle(marker="s", color='black', size=cell_size, zorder=1)
        return AgentPortrayalStyle(marker="s", color=color, size=cell_size, zorder=1)

    elif isinstance(agent, Waste):
        colors = {1: "#165c0c", 2: "#ff8000", 3: "#cd1a06"}
        return AgentPortrayalStyle(marker="s", color=colors[agent.color], size=cell_size/3, zorder=10)

    elif isinstance(agent, Robot):
        if isinstance(agent, GreenAgent):
            color = "#165c0c"
        elif isinstance(agent, YellowAgent):
            color = "#ff8000"
        elif isinstance(agent, RedAgent):
            color = "#cd1a06"
        return AgentPortrayalStyle(marker="o", color=color, size=cell_size/2, zorder=20)

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
        components=[SpaceGraph,WastePlot],
        model_params=model_params,
    )


# This is required to render the visualization in the Jupyter notebook
page = StyledDashboard()
# to start : "solara run server.py"
