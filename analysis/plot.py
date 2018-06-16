"""Display a model (Mesh, Graph, Hypergraph...) with its Partition
using different colors for each part.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import math
import svgwrite as svgw
from   time import time

from crack.analysis.colors  import COLOR_DISTINCT, COLOR_DEFAULT, COLOR_BLIND
from crack.models.geom_fcts import homothetic, translate, dist_d2
from crack.models.topo_fcts import min_dist_nodes
from crack.utils.errors     import crack_error


#####################################
### Initialization of the options ###
#####################################

def _set_default_options(algopt):
    """Set some parameters needed for the figure if not specified by
    the user.
    """
    algopt.setdefault("node_in_radius" ,       0.3 ) # 1/3 of the node_radius
    algopt.setdefault("image_size"     , (500, 500))
    algopt.setdefault("margin"         ,       0.05) # 5% of the size
    algopt.setdefault("text_color"     ,    "black")
    algopt.setdefault("text_size"      ,         45)
    algopt.setdefault("edge_stroke_min",          1)
    algopt.setdefault("edge_stroke_max",         10)


def _set_hypergraph_options(algopt):
    """Set some parameters specific with Hypergraphs.
    """
    algopt.setdefault("hopacity"       ,        0.2)


def _adapt_options_homothetic(algopt, coefs):
    c_min = min(coefs)
    algopt["node_radius"] *= c_min
    algopt["text_size"  ] *= c_min


###############################################
### Adapt the coordinates to the image size ###
###############################################

def _adapt_coords(models, geom_key, algopt):
    """Modify the coordinates so that the plot will fit in the size
    required. Also compute the node_radius if not initialized.

    The new coordinates are stored for later use if the same image
    size is required.
    """
    geom   = models[geom_key]
    coord  = geom  ["coord"]
    size   = algopt["image_size"]
    margin = algopt["margin"]
    # Check if we really need to adapt the coordinates
    geom.setdefault("_plot_opts", {})
    if geom["_plot_opts"].get("coord_adapted_for_size") == size:
        algopt.setdefault("node_radius", geom["_plot_opts"]["node_radius"])
        return
    # Compute node_radius
    topo_entities = ("graph", "hypergraph")
    if "node_radius" not in algopt:
        if geom_key in topo_entities:
            topo_key = geom_key
        else:
            try:
                topo_key = next(key for key in models if isinstance(models[key], dict) and models[key].get("entity") in topo_entities)
            except StopIteration:
                crack_error(ValueError, "plot",
                    "Could not find topological data")
        algopt["node_radius"] = 2 * min_dist_nodes(models[topo_key]) / 5
    # Translation to get positive coordinates beginning at (0,0)
    lmin = list(coord[0])
    lmax = list(coord[0])
    for pt in coord[1:]:
        for c, l in enumerate(pt):
            lmin[c] = min(lmin[c], l)
            lmax[c] = max(lmax[c], l)
    delta = [-pmin for pmin in lmin]
    translate(geom, delta=delta)
    # Homothetic transformation to fit in the required size
    coefs = []
    for pmin, pmax, s in zip(lmin, lmax, size):
        if pmin == pmax:
            coefs.append(1)
        else:
            coefs.append( (s - 2*margin*s) / (pmax - pmin) )
    homothetic(geom, coefs)
    # Adapt the node_radius to the homothetic transformation
    _adapt_options_homothetic(algopt, coefs)
    # Translation for horizontal/vertical margin
    delta = [margin*s for s in size]
    translate(geom, delta=delta)
    # Record the transformation
    geom["_plot_opts"]["node_radius"] = algopt["node_radius"]
    geom["_plot_opts"]["coord_adapted_for_size"] = size


################################
### Compute nodes attributes ###
################################

def _model_to_values(model):
    if model["entity"] in ("graph", "hypergraph", "mesh"):
        return [[i] for i in range(model["nbr_n"])] # IDs
    elif model["entity"] in ["nweights", "eweights", "hweights"]:
        return list(list(l) for l in model["weights"])
    elif model["entity"] in "partition":
        return [[p] for p in model["parts"]]
    else:
        crack_error(ValueError, "_model_to_values",
            "Unknown entity: {}.".format(model["entity"]))


def _compute_colors_discrete(values):
    global COLOR_DISTINCT
    nbr_diff_values = len(set(values))
    if nbr_diff_values > len(COLOR_DISTINCT):
        crack_error(ValueError, "_compute_colors_discrete",
            "Current color scheme limited to {} different values, while {} different values were provided... Add new colors in the COLOR_DISTINCT of crack.colors.".format(len(COLOR_DISTINCT), nbr_diff_values))
    return [COLOR_DISTINCT[value] for value in values]


def _compute_colors_continuous(values):
    c_min = 0.2 * 255 # Almost white
    c_max = 1.0 * 255 # Black
    nbr_c = len(values[0])
    nbr_n = len(values)
    v_max = list(values[0])
    v_min = list(values[0])
    if nbr_c < 3: # Fill with 'white'
        for l in values:
            l.extend([0] * (3-nbr_c))
        v_max.extend([1] * (3-nbr_c))
        v_min.extend([0] * (3-nbr_c))
    nbr_c = min(3, nbr_c) # Discard criteria after the first 3
    for i in range(1, nbr_n):
        for c in range(nbr_c):
            v_min[c] = min(v_min[c], values[i][c])
            v_max[c] = max(v_max[c], values[i][c])
    colors = [[int(c_min + (c_max-c_min) * (1-(value[c]-v_min[c]) / v_max[c])) for c in range(3)] for value in values]
    return ["rgb({}, {}, {})".format(*color) for color in colors]


def _compute_node_colors(models, algopt, nbr_n):
    color_attr = {
        "colors"       : None,
        "circle_colors": None,
    }
    for color_key in color_attr:
        if color_key in algopt:
            model_key = algopt[color_key]
            if models[model_key]["entity"] == "partition":
                color_attr[color_key] = _compute_colors_discrete  (models[model_key]["parts"])
            else:
                values = _model_to_values(models[model_key])
                color_attr[color_key] = _compute_colors_continuous(values)
    if color_attr["colors"] is None:
        color_attr["colors"] = [COLOR_DEFAULT] * nbr_n
    return color_attr["colors"], color_attr["circle_colors"]


def _compute_node_bars(models, algopt):
    bars = None
    if "bars" in algopt:
        model_key = algopt["bars"]
        values = _model_to_values(models[model_key])
        nbr_n  = len(values)
        nbr_c  = len(values[0])
        l_max  = algopt["node_radius"] * 1.5
        v_max  = [max(v[c] for v in values) for c in range(nbr_c)]
        # When unit weights, increase v_max so that the length of the
        # bars will not be maximal
        v_min  = [min(v[c] for v in values) for c in range(nbr_c)]
        for c in range(nbr_c):
            if v_min[c] == v_max[c]:
                v_max[c] *= 4
        bars = [[values[i][c] / v_max[c] * l_max for c in range(nbr_c)] for i in range(nbr_n)]
    return bars


def _compute_node_numbers(models, algopt):
    numbers = None
    if "numbers" in algopt:
        model_key = algopt["numbers"]
        numbers = _model_to_values(models[model_key])
    return numbers


def _compute_edge_strokes(models, algopt, nbr_e):
    if "edge_strokes" in algopt:
        model_key = algopt["edge_strokes"]
        values  = _model_to_values(models[model_key])
        max_v   = max(l[0] for l in values)
        min_v   = min(l[0] for l in values)
        max_s   = algopt["edge_stroke_max"]
        min_s   = algopt["edge_stroke_min"]
        a       = (max_s - min_s) / (max_v - min_v)
        strokes = [a * (l[0] - min_v) + min_s for l in values]
    else:
        strokes = [1] * nbr_e
    return strokes


############################################
### Functions adding shapes to a Drawing ###
############################################

def _add_elem_bar(draw, center, bar_lengths, algopt):
    """Add bars centered on the given [center] position.
    Originally, the bars represent the weights of the node.
    """
    global COLOR_BLIND
    h = 2 * algopt["node_radius"] / len(bar_lengths)
    for c, l in enumerate(bar_lengths):
        draw.add(draw.rect(
            insert=(center[0]-l/2, center[1] - h * c),
            size=(l, h),
            fill=COLOR_BLIND[c],
            stroke="black", stroke_width=1
        ))


def _add_elem_circle(draw, center, color, algopt):
    """Add a circle inside a node.
    The circle color can represent the part, or the weight of the node.
    """
    r = algopt["node_radius"] * algopt["node_in_radius"]
    draw.add(draw.circle(center, r=r, fill=color, stroke="black"))


def _add_elem_number(draw, center, numbers, algopt):
    """Add the index of the node, quite centered.
    """
    nbr_c = len(numbers)
    for c in range(nbr_c):
        g = draw.add(draw.g(stroke=algopt["text_color"], stroke_width=0.5))
        x = center[0] - algopt["node_radius"]
        y = center[1] - (c - (nbr_c-1)/2) * algopt["node_radius"]
        g.add(svgw.text.Text(str(numbers[c]), insert=(x,y), textLength=algopt["node_radius"]))


def _add_square(draw, c, r, color):
    stroke_width = 10
    dx = 5
    draw.add(draw.line(start=(c[0]-r-dx,c[1]-r), end=(c[0]+r+dx, c[1]-r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]+r,c[1]-r), end=(c[0]+r, c[1]+r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]+r+dx,c[1]+r), end=(c[0]-r-dx, c[1]+r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]-r,c[1]+r), end=(c[0]-r, c[1]-r), stroke=color, stroke_width=stroke_width))


def _add_shape_triangle(draw, c, r, color):
    stroke_width = 10
    draw.add(draw.line(start=(c[0]  ,c[1]-r), end=(c[0]+r, c[1]+r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]  ,c[1]-r), end=(c[0]-r, c[1]+r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]-r,c[1]+r), end=(c[0]+r, c[1]+r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.circle((c[0]  , c[1]-r), r=r/4, fill=color))
    draw.add(draw.circle((c[0]-r, c[1]+r), r=r/4, fill=color))
    draw.add(draw.circle((c[0]+r, c[1]+r), r=r/4, fill=color))

def _add__shape_cross(draw, c, r, color):
    stroke_width = 10
    draw.add(draw.line(start=(c[0]-r,c[1]+r), end=(c[0]+r, c[1]-r), stroke=color, stroke_width=stroke_width))
    draw.add(draw.line(start=(c[0]+r,c[1]+r), end=(c[0]-r, c[1]-r), stroke=color, stroke_width=stroke_width))


def _add_elem_shape(draw, center, shape_id, algopt):
    """Add a shape depending on the shape_id (originally, the part
    of the node).
    """
    r = 10
    color = "black"
    id_to_shape = {
        0: _add_shape_triangle,
        1: _add_shape_square,
        2: _add_shape_cross,
    }
    id_to_shape[shape_id](draw, center, r, color)


######################
### Plot functions ###
######################

def plot_Mesh_svg(models, records, out_file, key_geometry="mesh", **algopt):
    """Output a Mesh in a .svg format.

    Options:
        key_geometry: str: The Mesh key in [models]. Default: 'mesh'.
        border: "line": Separate the parts with a line.
        bars         : [key]: Add bars    to the Cells, whose lengths...
        circle_colors: [key]: Add circles in the Cells, whose colors...
        colors       : [key]: The Cells colors...
        numbers      : [key]: Add numbers to the Cells, whose values...
            ...depend on their:
            id     if the entity of [key] is 'graph'|'hypergraph'|'mesh'
            weight if the entity of [key] is 'weight'
            part   if the entity of [key] is 'partition'
        dmin: float: Minimum distance between two cells.
        text_color: str: Color of the text.
    """
    mesh = models[key_geometry]

    if mesh["dimns"] >= 3:
        print("#!# Crack Error: cannot plot 3D meshes #!#")
        return
    if out_file[-4:] != ".svg":
        out_file += ".svg"

    ### Set default options ###
    _set_default_options(algopt)
    _adapt_coords(models, key_geometry, algopt)
    ### Plot ###
    draw = svgw.Drawing(out_file, size=algopt["image_size"])
    nbr_n  = mesh["nbr_n"]
    elems  = mesh["elems"]
    coord  = mesh["coord"]
    vcoord = mesh["vcoord"]
    # Compute node attributes (if needed)
    colors, circles = _compute_node_colors (models, algopt, mesh["nbr_n"])
    bars            = _compute_node_bars   (models, algopt)
    numbers         = _compute_node_numbers(models, algopt)
    # Plot the cells
    for i, (ev, ec) in enumerate(zip(elems, coord)):
        draw.add(draw.polygon((vcoord[v] for v in ev),
            fill=colors[i],
            stroke="black", stroke_width=1))
        if circles is not None:
            _add_elem_circle(draw, ec, circles[i], algopt)
        if bars    is not None:
            _add_elem_bar   (draw, ec, bars[i]   , algopt)
        if numbers is not None:
            _add_elem_number(draw, ec, numbers[i], algopt)
    # Plot the border
    # TODO

    ### End of drawing ###
    draw.save()


def plot_Graph_svg(models, records, out_file, key_topology="graph", **algopt):
    """Output a Graph in a .svg format.

    Options:
        key_topology: str: The Graph key in [models]. Default: 'graph'.
        border: "line": Separate the parts with a line.
        bars         : [key]: Add bars    to the Nodes, whose lengths...
        circle_colors: [key]: Add circles in the Nodes, whose colors...
        colors       : [key]: The Nodes colors...
        numbers      : [key]: Add numbers to the Nodes, whose values...
        edge_strokes : [key]: The width of the Edges depend on their:
            ...depend on their:
            id     if the entity of [key] is 'graph'|'hypergraph'|'mesh'
            weight if the entity of [key] is 'weight'
            part   if the entity of [key] is 'partition'
        dmin: float: Minimum distance between two cells.

    Display Options:
        image_size: (int, int): Width and height of the image
            (default: (1000, 1000)).
        node_radius: Multiply the radiuses of the nodes by this value.
        node_in_radius: Multiply the radiuses of the circle/shapes
            inside nodes by this value.
        dist_coef: int|"auto": Adjust the distance between two nodes.
        text_color: str: Color of the text.
    """
    graph = models[key_topology]
    if "coord" not in graph:
        raise ValueError("Nodes coordinates ('coord') were not initialized.")

    if graph["dimns"] >= 3:
        print("#!# Crack Error: cannot plot Graphs of more than 2D #!#")
        return
    if out_file[-4:] != ".svg":
        out_file += ".svg"

    ### Set default options ###
    _set_default_options(algopt)
    _adapt_coords(models, key_topology, algopt)
    ### Plot ###
    draw = svgw.Drawing(out_file, size=algopt["image_size"])
    nbr_n = graph["nbr_n"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    coord = graph["coord"]
    # Compute node and edge attributes (if needed)
    colors, circles = _compute_node_colors (models, algopt, graph["nbr_n"])
    bars            = _compute_node_bars   (models, algopt)
    numbers         = _compute_node_numbers(models, algopt)
    strokes         = _compute_edge_strokes(models, algopt, graph["nbr_e"])
    ### Plot ###
    # Plot the graph
    for i, pi in enumerate(coord):
        # Draw the edges until its neighbors (need to do it first or
        # the edges would traverse the circles)
        for j, e in zip(nodes[i][0], nodes[i][1]):
            if j > i: # Center not ploted yet: draw the edge before.
                draw.add(draw.line(start=pi, end=coord[j],
                    stroke="black", stroke_width=strokes[e]))
        # Draw the node
        draw.add(draw.circle(pi, r=algopt["node_radius"],
            fill=colors[i], stroke="black"))
        # Node attributes
        if circles is not None:
            _add_elem_circle(draw, pi, circles[i], algopt)
        if bars    is not None:
            _add_elem_bar   (draw, pi, bars[i]   , algopt)
        if numbers is not None:
            _add_elem_number(draw, pi, numbers[i], algopt)
    # Plot the border
    # TODO

    ### End of drawing ###
    draw.save()


def plot_Hypergraph_svg(models, records, out_file, key_topology="hypergraph", **algopt):
    """Output a Hypergraph in a .svg format.

    Options:
        key_topology: str: The Graph key in [models]. Default:
            'hypergraph'.
        border: "line": Separate the parts with a line.
        bars         : [key]: Add bars    to the Nodes, whose lengths...
        circle_colors: [key]: Add circles in the Nodes, whose colors...
        colors       : [key]: The Nodes colors...
        numbers      : [key]: Add numbers to the Nodes, whose values...
            ...depend on their:
            id     if the entity of [key] is 'graph'|'hypergraph'|'mesh'
            weight if the entity of [key] is 'weight'
            part   if the entity of [key] is 'partition'
        hopacity: float <0.2>: Control the opacity of the hyperedges.
        dmin: float: Minimum distance between two cells.

    Display Options:
        image_size: (int, int): Width and height of the image
            (default: (1000, 1000)).
        node_radius: Multiply the radiuses of the nodes by this value.
        node_in_radius: Multiply the radiuses of the circle/shapes
            inside nodes by this value.
        dist_coef: int|"auto": Adjust the distance between two nodes.
        text_color: str: Color of the text.
    """
    hgraph = models[key_topology]
    if "coord" not in hgraph:
        raise ValueError("Nodes coordinates ('coord') were not initialized.")

    if hgraph["dimns"] >= 3:
        print("#!# Crack Error: cannot plot Hypergraphs of more than 2D #!#")
        return
    if out_file[-4:] != ".svg":
        out_file += ".svg"

    ### Set default options ###
    _set_default_options   (algopt)
    _set_hypergraph_options(algopt)
    _adapt_coords(models, key_topology, algopt)
    ### Plot ###
    draw = svgw.Drawing(out_file, size=algopt["image_size"])
    nbr_n = hgraph["nbr_n"]
    nodes = hgraph["nodes"]
    edges = hgraph["edges"]
    coord = hgraph["coord"]
    # Compute node and edge attributes (if needed)
    colors, circles = _compute_node_colors (models, algopt, hgraph["nbr_n"])
    bars            = _compute_node_bars   (models, algopt)
    numbers         = _compute_node_numbers(models, algopt)
    ### Plot ###
    lsquare = algopt["node_radius"]
    # Plot the hypergraph
    # First, draw the node
    for i, pi in enumerate(coord):
        draw.add(draw.circle(pi, r=algopt["node_radius"],
            fill=colors[i], stroke="black"))
    # Then, draw the hyperedges
    for e, ends in enumerate(edges):
        ends = set(ends)
        l    = len(ends)
        barycenter = [sum(coord[i][d] for i in ends)/l for d in range(2)]
        square = (
            (barycenter[0] - lsquare/2.0, barycenter[1] - lsquare/2.0),
            (barycenter[0] - lsquare/2.0, barycenter[1] + lsquare/2.0),
            (barycenter[0] + lsquare/2.0, barycenter[1] - lsquare/2.0),
            (barycenter[0] + lsquare/2.0, barycenter[1] + lsquare/2.0),
        )
        for end in ends:
            # find 2 closest ends of square
            dists = [dist_d2(corner, coord[end]) for corner in square]
            indices = list(range(4))
            i1 = min(indices, key=lambda i: dists[i])
            del indices[i1]
            i2 = min(indices, key=lambda i: dists[i])
            # draw a triangle from the end to the square corners
            draw.add(draw.polygon(points=[coord[end], square[i1], square[i2]],
                fill="black", stroke="black",
                opacity=algopt["hopacity"], stroke_width=1))
        # draw the square
        edge_center = [barycenter[d] - lsquare/2 for d in range(2)]
        draw.add(draw.rect(insert=edge_center, size=(lsquare,lsquare),
            fill="black", opacity=0.9))
    # Finally, add the node attributes
    if circles is not None:
        for i, pi in enumerate(coord):
            _add_elem_circle(draw, pi, circles[i], algopt)
    if bars    is not None:
        for i, pi in enumerate(coord):
            _add_elem_bar   (draw, pi, bars[i]   , algopt)
    if numbers is not None:
        for i, pi in enumerate(coord):
            _add_elem_number(draw, pi, numbers[i], algopt)
    # Plot the border
    # TODO

    ### End of drawing ###
    draw.save()


