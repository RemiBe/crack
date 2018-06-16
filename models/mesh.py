"""A Mesh is a set of Elements placed in space. Elements can be
associated with Vertices that delimitate them.

A Mesh is a dictionary defining the fields:
- nbr_n : int: The number of Elements.
- nbr_v : int: The number of Vertices (ends of the Elements).
- dimns : int: The dimension of the Mesh: 2D, 3D...
- elems : ((int, ...), ...): Every Element is a set of Vertices.
- verts : ((int, ...), ...): Every Vertex belongs to some Elements.
- coord : ((float, ...), ...): The coordinates of the Elements.
- vcoord: ((float, ...), ...): The coordinates of the Vertices.

Example:
                        y
    Consider the Mesh:  ^ ,---,---,---,
                       2| | 0 | 1 | 2 |
                        | '---+---+---'
                       1|     | 3 |
                        |     '---'
                       0+---,---,---,---,--> x
                        0   1   2   3   4

    Then the corresponding dictionary is:
>>> mesh = {
        "dimns": 2,
        "coord": (
            (1, 2),
            (2, 2),
            (3, 2),
            (2, 1),
        )
    }

    If we use letters to represent the vertices indexes:
                         y
                         ^ a---b---c---d
                        2| | 0 | 1 | 2 |
                         | e---f---g---h
                        1|     | 3 |
                         |     i---j
                        0+---,---,---,---,--> x
                         0   1   2   3   4

    Then the additional fields would be:
>>> mesh = {
        "vcoord": (
            (0.5, 2,5),  # assuming a corresponds to index 0
            (1.5, 2,5),  # assuming b corresponds to index 1
            (2.5, 2,5),  # assuming c corresponds to index 2
            (3.5, 2,5),  # assuming d corresponds to index 3
            (0.5, 1,5),  # assuming e corresponds to index 4
            (1.5, 1,5),  # assuming f corresponds to index 5
            (2.5, 1,5),  # assuming g corresponds to index 6
            (3.5, 1,5),  # assuming h corresponds to index 7
            (1.5, 0,5),  # assuming i corresponds to index 8
            (2.5, 0,5),  # assuming j corresponds to index 9
        ),
        "elems" : (
            (a,b,f,e),
            (b,c,g,f),
            (c,d,h,g),
            (f,g,j,i),
        ),
        "verts" : (
            (0,),      # a
            (0, 1),    # b
            (1, 2),    # c
            (2,),      # d
            (0,),      # e
            (0, 1, 3), # f
            (0, 1, 3), # g
            (2,),      # h
            (3,),      # i
            (3,),      # j
        ),
    }
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import warnings


######################
### Initialization ###
######################

#****************#
# Init from file #
#****************#

### .mesh file ###

def _read_int(line):
    return int(line.split()[0])

def _mesh_read_dimension(f, mesh):
    """Dimension of the mesh
    """
    mesh["dimns"] = _read_int(f.readline())
    return f

def _mesh_read_edges(f, mesh):
    """Edges between vertices? Do not need to consider them.
    """
    nbr_e = _read_int(f.readline())
    for _ in range(nbr_e):
        f.readline()
    return f

def _mesh_read_pass(f, mesh):
    nbr_e = _read_int(f.readline())

def _mesh_read_elements(f, mesh):
    """Geometrical shapes, that are called Elements.
    """
    elems = mesh["elems"]
    nbr_n = mesh["nbr_n"] # elements already read (of different shape)
    nbr_n_add = _read_int(f.readline()) # additional elements
    for i in range(nbr_n, nbr_n + nbr_n_add):
        line  = f.readline().split()
        verts = tuple(int(vi) - 1 for vi in line[:-1]) # last number is an unknown coefficient
        for vi in verts:
            mesh["verts"][vi].append(i)
        elems.append(verts)
    mesh["nbr_n"] += nbr_n_add
    return f

def _mesh_read_end(f, mesh):
    return None

def _mesh_read_version(f, mesh):
#    version = int(line[1])
    return f

def _mesh_read_vertices(f, mesh):
    dimns  = mesh["dimns"]
    nbr_v  = _read_int(f.readline())
    vcoord = tuple(
        tuple(float(c) for c in f.readline().split()[:dimns])
        for _ in range(nbr_v)
    )
    mesh["nbr_v" ] = nbr_v
    mesh["vcoord"] = vcoord
    mesh["verts" ] = [ [] for _ in range(nbr_v) ]
    return f

def init_Mesh_from_mesh(models, records, filename, key="mesh"):
    """Build the Mesh stored in a .mesh file.
    """
    nbr_n = 0
    mesh = {
        "entity": "mesh",
        "nbr_n": 0,
        "elems": [],
    }
    keywords = {
        "Dimension"           : _mesh_read_dimension,
        "Edges"               : _mesh_read_edges,
        "Quadrilaterals"      : _mesh_read_elements,
        "Quadrangles"         : _mesh_read_elements,
        "MeshVersionFormatted": _mesh_read_version,
        "Triangles"           : _mesh_read_elements,
        "Tetrahedra"          : _mesh_read_elements,
        "Vertices"            : _mesh_read_vertices,
        "End"                 : _mesh_read_end
    }
    keywords_pass = [ # For an unknown reason the number is on the same line
        "Corners",
        "RequiredVertices",
        "Ridges",
    ]
    with open(filename, 'r') as f:
        while f is not None:
            line = f.readline().split()
            if not line:
                continue
            elif line[0] in keywords:
                f = keywords[line[0]](f, mesh)
            elif line[0] in keywords_pass:
                n_pass = int(line[1])
                for _ in range(n_pass):
                    f.readline()
            else:
                warnings.warn("Unrecognized word '{}' in {} file (recognized values are {}, pass values are {}.".format(line[0], filename, keywords.keys(), keywords_pass), UserWarning)

    # Transform lists into tuples
    mesh["verts"] = tuple(tuple(l) for l in mesh["verts"])
    mesh["elems"] = tuple(mesh["elems"])
    update_coord_barycenter_vcoord(mesh)
    models[key] = mesh


#############
### Utils ###
#############

def coarsen_Mesh(models, records, c_models, key_topo, aggregation):
    """Coarsen the Mesh in [models] according to [matching] and
    store it in [c_models].
    """
    # TODO
    pass


def update_coord_barycenter_vcoord(mesh):
    """Fill the `coord` field that associates with each Element
    its barycenter.
    """
    dimns  = mesh["dimns"]
    elems  = mesh["elems"]
    vcoord = mesh["vcoord"]
    ecoord = []
    for elem in elems:
        coords = [vcoord[vi] for vi in elem]
        l = len(coords)
        ecoord.append([sum(c[d] for c in coords) / l for d in range(dimns)])
    mesh["coord"] = ecoord


def submesh(models, submodels, part_to_keep=0):
    """Returns the submesh composed of the elements whose part is
    [part_to_keep].

    Arguments:
        submodels: dict: The "models" dict to update.
        part_to_keep: int: Vertex i belongs to the subgraph if its
            parts is [part_to_keep].
    """
    # TODO
    pass


##############
### Record ###
##############

def list_to_line(l):
    return "{}\n".format(str(l)[1:-1].replace(", ", " "))

def Mesh_to_mesh(models, filename):
    """Save the Mesh in a .mesh format.
    """
    mesh   = models["mesh"]
    nbr_n  = mesh["nbr_n"]
    nbr_v  = mesh["nbr_v"]
    dimns  = mesh["dimns" ]
    elems  = mesh["elems" ]
    vcoord = mesh["vcoord"]
    elem_names = {
        3: "Triangles",
        4: "Quadrangles",
    }
    forms  = {i: [] for i in elem_names}
    for i in range(n):
        try:
            forms[len(elems[i])].append(elems[i])
        except KeyError:
            raise ValueError("Unexpected form (not in [Triangles, Quadrangles]) of length {}.".format(len(elems[i])))
    with open(filename, "w") as f:
        f.write("MeshVersionFormatted 2\n")
        f.write("Dimension\n{}\n".format(dimns))
        f.write("Vertices\n{}\n".format(v))
        for i in range(nbr_v):
            f.write(list_to_line(list(vcoord[i]) + [1]))
        for l, form in forms.items():
            if form:
                name = elem_names[l]
                f.write("{}\n{}\n".format(name, len(form)))
                for elem in form:
                    f.write(list_to_line([i+1 for i in elem] + [1]))
        f.write("End\n")


def Mesh_to_xyz(models, filename):
    """Save the Mesh in a .xyz format. This is the format
    used by Scotch.
    """
    mesh  = models["mesh"]
    nbr_n = mesh["nbr_n"]
    dimns = mesh["dimns" ]
    coord = mesh["coord"]
    with open(filename, "w") as f:
        f.write("{}\n".format(dimns))
        f.write("{}\n".format(n))
        for i in range(n):
            f.write(list_to_line(list(coord[i])))


####################
### Function IDs ###
####################

INIT_MESH_FCTS = {
    "init_Mesh_from_mesh": init_Mesh_from_mesh,
}


