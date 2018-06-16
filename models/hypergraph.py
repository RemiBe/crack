"""A Hypergraph H = (V,E) is a set of vertices/nodes (V) and a set of
hyperedges (E included in P(V), where P(V) is the set of all parts of
V). Therefore, a hyperedge can have an arbitrary number of ends.

A Hypergraph is a dictionary defining the fields:
- entity: 'hypergraph'
- nbr_n: int: The number of Nodes.
- nbr_e: int: The number of Hyperedges.
                   a node
           ,----------'-----------,
- nodes: ( ((int, ...), (int, ...)), ... )
            '---.----'  '---.----'
            neighbors     edges

- edges: ( (int, int, ...), ... )
           '------.------'
             a hyperedge
The "nodes" key stores in cell i the neighbors and the hyperedges of
the ith node.
The "edges" key stores in cell i the ends of the ith hyperedge.
We use tuples to have a fast access to the ngbrs/hyperedges of a node,
because we assume that the hypergraph will not change.

Optional fields are:
- dimns: int: The Geometrical dimension of the Hypergraph
- coord: ((float, ...), ...): The coordinates of the Nodes
NB: these fields are initialized by the init_HypergraphGeometry function.

Example:

    Consider the Hypergraph:

      0     1
      ,- 1 --- 2
    0-+  +-----'
      '- 3    2

    Then the corresponding dictionary is:
>>> hypergraph_key = {
        "entity": "hypergraph",
        "nbr_n": 4,
        "nbr_e": 3,
        "nodes": (
            ( (1,3    ), (0,0    ) ), # node 0 has 2 neighbors
            ( (0,2,2,3), (0,1,2,2) ), # node 1 has 3 neighbors,
                                      # but 2 appears in two hyperedges
            ( (1,1,3  ), (1,2,3  ) ), # node 2 has 2 neighbors
            ( (0,1,2  ), (0,1,1  ) ), # node 3 has 3 neighbors
        ),
        "edges": (
            (0,1,3),
            (1,2),
            (1,2,3),
        ),
    }
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.nweights import init_NWeights_from_args


######################
### Initialization ###
######################

#************************#
# Init from other models #
#************************#

def init_Hypergraph_from_Mesh(models, records, key="hypergraph", mesh_key="mesh", ngbr_dim="dual"):
    """Build a Hypergraph depending on geometrical attributes of the
    Mesh.

    Arguments:
        models: dict: The created Hypergraph will be assigned to [key]
            in [models].

    Optional Arguments:
        mesh_key: str: The Mesh that will be used to create the
            Hypergraph.
        ngbr_dim: int [default: dim(Mesh)-1]: Cells that share an
            object of exactly dimension [ngbr_dim] are considered
            neighbors. Example; in 3D, if ngbr_dim = 2, two cells
            that share a face are neighbors.
            NB: when ngbr_dim == dim(Mesh)-1, we say that we build
            the Dual Hypergraph of the Mesh.
            NB: in our model, each node is the center
            of exactly one hyperedge, which points to all its neighbors.
    """
    nbr_n = models[mesh_key]["nbr_n"]
    dimns = models[mesh_key]["dimns"]
    elems = models[mesh_key]["elems"]
    verts = models[mesh_key]["verts"]
    nodes = [ ([], []) for _ in range(nbr_n) ]
    edges = [None] * nbr_n
    # Condition for an edge #
    if ngbr_dim == "dual":
        ngbr_dim = dimns - 1
    if ngbr_dim == 0:   # point   --> Share 1 vertices
        cond = (lambda l: l == 1)
    elif ngbr_dim == 1: # segment --> Share 2 vertices
        cond = (lambda l: l == 2)
    elif ngbr_dim == 2: # face    --> Share at least 3 vertices
        cond = (lambda l: l  > 2)
    else:
        raise ValueError("Impossible value for ngbr_dim (got {}).".format(ngbr_dim))

    # 1st pass on the Vertices to assign to every Element which Elements
    # it shares Vertices with it.
    elems_com_verts = tuple([] for _ in range(nbr_n))
    for v_elems in verts:
        for elem in v_elems:
            touched = list(v_elems)
            touched.remove(elem)
            elems_com_verts[elem].extend(touched)
    # Find the neighboors of each Element and create the Hyperedges.
    for elem, pot_ngbrs in enumerate(elems_com_verts):
        ngbrs = set(ei for ei in pot_ngbrs
                    if cond(len([i for i in pot_ngbrs if i == ei]))
                )
        ngbrs = list(ngbrs)
        nodes[elem][0].extend(ngbrs)
        nodes[elem][1].extend([elem] * len(ngbrs))
        for ngbr in ngbrs:
            nodes[ngbr][0].append(elem)
            nodes[ngbr][1].append(elem)
        edges[elem] = [elem] + ngbrs
    models[key] = {
        "entity": "hypergraph",
        "nbr_n": nbr_n,
        "nbr_e": nbr_n,
        "nodes": tuple( (tuple(ngbrs), tuple(edges)) for ngbrs, edges in nodes ),
        "edges": tuple(edges),
        "dimns": models[mesh_key]["dimns"],
        "coord": models[mesh_key]["coord"],
    }


###################################
### Transformation & Properties ###
###################################

def coarsen_Hypergraph(models, records, c_models, key_topo, aggregation):
    """
    """
    # TODO
    pass


####################
### Function IDs ###
####################

INIT_HYPERGRAPH_FCTS = {
    "init_Hypergraph_from_Mesh": init_Hypergraph_from_Mesh,
}


