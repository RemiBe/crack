"""Regroup all the analysis functions in a common dictionary.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.analysis.plot        import plot_Graph_svg, plot_Hypergraph_svg, plot_Mesh_svg
from crack.analysis.print_stats import print_stats


ANALYZE_FCTS = {
    "plot_Graph"         : plot_Graph_svg,
    "plot_Graph_svg"     : plot_Graph_svg,
    "plot_Hypergraph"    : plot_Hypergraph_svg,
    "plot_Hypergraph_svg": plot_Hypergraph_svg,
    "plot_Mesh"          : plot_Mesh_svg,
    "plot_Mesh_svg"      : plot_Mesh_svg,
    "print_stats"        : print_stats,
}

