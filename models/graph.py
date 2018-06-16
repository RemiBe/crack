"""A Graph G = (V,E) is a set of vertices/nodes (V) and a set of edges
(E included in V^2).

A Graph is a dictionary defining the fields:
- entity: 'graph'
- nbr_n: int: The number of Nodes.
- nbr_e: int: The number of Edges.
                   a node
           ,----------'-----------,
- nodes: ( ((int, ...), (int, ...)), ... )
            '---.----'  '---.----'
            neighbors     edges

- edges: ( (int, int), ... )
           '---.----'
            an edge
The 'nodes' key stores in cell i the neighbors and the edges of the ith
node.
The 'edges' key stores in cell i the ends of the ith edge.
We use tuples to have a fast access to the ngbrs/edges of a node,
because we assume that the graph will not change.

Optional fields are:
- dimns: int: The Geometrical dimension of the Graph
- coord: ((float, ...), ...): The coordinates of the Nodes
NB: these fields are initialized by the init_GraphGeometry function.

Example:

    Consider the Graph:    0     1
                        0 --- 1 --- 2
                             2|     |
                              3 ----'3

    Then the corresponding dictionary is:
>>> graph_key = {
        "entity": "graph",
        "nbr_n": 4,
        "nbr_e": 4,
        "nodes": [
            [ [1    ], [0    ] ], # node 0 has 1 neighbor along edge 0
            [ [0,2,3], [0,1,2] ], # node 1 has 3 neighbors
            [ [1,3  ], [1,3  ] ], # node 2 has 2 neighbors
            [ [1,2  ], [2,3  ] ], # node 3 has 2 neighbors
        ],
        "edges": [
            [0,1],
            [1,2],
            [1,3],
            [2,3],
        ],
    }
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.nweights import init_NWeights_from_args
from crack.models.eweights import init_EWeights_from_args


#################################
### Initialization (topology) ###
#################################

#****************#
# Init from file #
#****************#

def init_Graph_from_grf(models, records, filename,
    key_topology="graph", key_nweights="nweights",
    key_eweights="eweights"):
    """Build the Graph stored in a .grf file (format used by Scotch).
    Can initialize the [NE]Weights if specified in [entities].

    Arguments:
        models: dict: The created Graph will be assigned to
            [key_topology] in [models].
        filename: Path to the .grf file.

    Optional Arguments:
        extract_keys: str or list or str or dict: Apart from the
            Graph, can also initialize the '[ne]weights'. In this
            case, if a dict is provided, is maps '[ne]weights' to
            the new keys. If None is provided, will try to
            initialize the '[ne]weights'.
    """
    with open(filename, "r") as f:
        version = int(f.readline())
        nbr_n, nbr_e = tuple(int(w) for w in f.readline().split())
        base, fmt = tuple(w for w in f.readline().split())
        # fmt = "ijk" where - i indicates if there are labels
        #                   - j indicates if there are weights on edges
        #                   - k indicates if there are weights on nodes
        nbr_e = int(nbr_e/2)
        nodes = [[None, []] for i in range(nbr_n)]
        edges = [None] * nbr_e
        def read_ngbrs(i, ngbrs, ne):
            nodes[i][0] = ngbrs
            for ngbr in ngbrs:
                if i < ngbr: # otherwise, already considered
                    edges[ne] = (i, ngbr)
                    nodes[   i][1].append(ne)
                    nodes[ngbr][1].append(ne)
                    ne += 1
            return ne
        def read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne):
            nodes[i][0] = ngbrs
            for ngbr, ew in zip(ngbrs, ews):
                if i < ngbr: # otherwise, already considered
                    edges[ne] = (i, ngbr)
                    ewgts[ne] = [ew]
                    nodes[   i][1].append(ne)
                    nodes[ngbr][1].append(ne)
                    ne += 1
            return ne
        if fmt == "000": # No labels, no ewgts, no nwgts
            nbr_c = 0
            nwgts = None
            ewgts = None
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
#                degree = words[0]
                return read_ngbrs(i, words[1:], ne)
        elif fmt == "001": # No labels, no ewgts, nwgts
            nbr_c = 1
            nwgts = [None] * nbr_n
            ewgts = None
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
                nwgts[i] = (words[0],)
#                degree = words[1]
                return read_ngbrs(i, words[2:], ne)
        elif fmt == "002": # No labels, no ewgts, nbr_c nwgts
            nbr_c = int(f.readline())
            nwgts = [None] * nbr_n
            ewgts = None
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
                nwgts[i] = list(words[:nbr_c])
#                degree = words[nbr_c]
                ngbrs = list(words[nbr_c+1:])
                return read_ngbrs(i, ngbrs, ne)
        elif fmt == "100": # labels, no ewgts, no nwgts
            nbr_c = 0
            nwgts = None
            ewgts = None
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
#                degree = words[1]
                return read_ngbrs(i, words[2:], ne)
        elif fmt == "101": # labels, no ewgts, nwgts
            nbr_c = 1
            nwgts = [None] * nbr_n
            ewgts = None
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
                nwgts[i] = [words[1]]
#                degree = words[2]
                return read_ngbrs(i, words[3:], ne)
        elif fmt == "102": # labels, no ewgts, nbr_c nwgts
            nbr_c = int(f.readline())
            nwgts = [None] * nbr_n
            ewgts = None
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
                nwgts[i] = list(words[1:nbr_c+1])
#                degree = words[nbr_c+1]
                return read_ngbrs(i, words[nbr_c+2:], ne)
        elif fmt == "010": # No labels, ewgts, no nwgts
            nbr_c = 0
            nwgts = None
            ewgts = [None] * nbr_e
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
#                degree = words[0]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(1, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        elif fmt == "110": # labels, ewgts, no nwgts
            nbr_c = 0
            nwgts = None
            ewgts = [None] * nbr_e
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
#                degree = words[1]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(2, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        elif fmt == "011": # No labels, ewgts, nwgts
            nbr_c = 1
            nwgts = [None] * nbr_n
            ewgts = [None] * nbr_e
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
                nwgts[i] = [words[0]]
#                degree = words[1]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(2, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        elif fmt == "012": # No labels, ewgts, nbr_c nwgts
            nbr_c = int(f.readline())
            nwgts = [None] * nbr_n
            ewgts = [None] * nbr_e
            def init(i, line, ne):
                words = tuple(int(w) for w in line.split())
                nwgts[i] = tuple(words[:nbr_c])
#                degree = words[nbr_c]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(nbr_c+1, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        elif fmt == "111": # labels, ewgts, nwgts
            nbr_c = 1
            nwgts = [None] * nbr_n
            ewgts = [None] * nbr_e
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
                nwgts[i] = (words[1],)
#                degree = words[2]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(3, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        elif fmt == "112": # labels, ewgts, nbr_c nwgts
            nbr_c = int(f.readline())
            nwgts = [None] * nbr_n
            ewgts = [None] * nbr_e
            def init(_, line, ne):
                words = tuple(int(w) for w in line.split())
                i = words[0]
                nwgts[i] = tuple(words[1:nbr_c+1])
#                degree = words[nbr_c+2]
                ews, ngbrs = tuple(zip(*[(words[j],words[j+1]) for j in range(nbr_c+3, len(words), 2)]))
                return read_ngbrs_ewgts(i, ewgts, ngbrs, ews, ne)
        else:
            raise ValueError("Wrong format in {}: got {}".format(filename, fmt))
        ne = 0
        for i, line in enumerate(f):
            ne = init(i, line, ne)
    assert ne == nbr_e
    models[key_topology] = {
        "entity": "graph",
        "nbr_n": nbr_n,
        "nbr_e": nbr_e,
        "nodes": nodes,
        "edges": edges,
    }
    if nwgts is not None and key_nweights is not None:
        init_NWeights_from_args(models, records, nwgts, key_in=key_topology, key_out=key_nweights)
    if ewgts is not None and key_eweights is not None:
        init_EWeights_from_args(models, records, ewgts, key_in=key_topology, key_out=key_eweights)
    models["key_lead"] = key_topology


def init_Graph_from_mtx(models, records, filename=None, key="graph"):
    """Build the Graph specified in a .mtx file (format used to store
    matrices).

    Arguments:
        models: dict: The created Graph will be assigned to [key]
            in [models].
        filename: Path to the .grf file.

    Structure of a .mtx file:
    ,--------------------------------------------------------------,
    | % Header line                                                |
    | % Comment lines                                              |
    | #lines #columns #entries  <-- for us: #nodes #nodes #edges   |
    | #in #out #value           <-- for each edge, there is a line |
    '--------------------------------------------------------------'
    NB: - the ids in the mesh begin at 1...
        - the edges are specified twice in the mesh
        - see: http://math.nist.gov/MatrixMarket/formats.html

    Arguments:
        models: dict: The created Graph will be assigned to [key]
            in [models].
        filename: Path to the .mtx file.
    """
    with open(filename, "r") as f:
        line = f.readline()
        fmt = line.split()[-1]
        assert fmt in ["symmetric", "general"]
        assert "array" not in line # specifier for dense matrices
        while line[0] == "%":
            line = f.readline()
        nbr_n, nbr_n_, nbr_f = tuple(int(w) for w in line.split())
        if nbr_n != nbr_n_:
            crack_error(ValueError, "init_Graph_from_mtx",
            "Non symmetric matrices: {} rows and {} columns.".format(nbr_n, nbr_n_))
        nodes = [ [[], []] for _ in range(nbr_n)]
        edges = []
        nbr_e = 0
        for line in f:
            i, j = tuple(int(w)-1 for w in line.split()[:2])
            if i > j:
                # Update Nodes
                # - Ngbrs
                nodes[i][0].append(j)
                nodes[j][0].append(i)
                # - Edges
                nodes[i][1].append(nbr_e)
                nodes[j][1].append(nbr_e)
                # Create Edge
                edges.append([i, j])
                nbr_e += 1
            elif i == j:
                nbr_f -= 1
    if fmt == "general":
        assert 2*nbr_e == nbr_f
    else:
        assert nbr_e == nbr_f
    models[key] = {
        "entity": "graph",
        "nbr_n": nbr_n,
        "nbr_e": nbr_e,
        "nodes": nodes,
        "edges": edges,
    }
    models["key_lead"] = key


#************************#
# Init from other models #
#************************#

def init_Graph_from_Hypergraph(models, algopt, stats):
    """Split the hyperedges into edges to form a Graph.
    """
    # TODO
    pass


def init_Graph_from_Mesh(models, records, key="graph", mesh_key="mesh", ngbr_dim="dual"):
    """Build a Graph depending on geometrical attributes of the Mesh.

    Arguments:
        models: dict: The created Graph will be assigned to [key]
            in [models].

    Optional Arguments:
        mesh_key: str: The Mesh that will be used to create the Graph.
        ngbr_dim: int [default: dim(Mesh)-1]: Cells that share an
            object of exactly dimension [ngbr_dim] are considered
            neighbors. Example; in 3D, if ngbr_dim = 2, two cells
            that share a face are neighbors.
            NB: when ngbr_dim == dim(Mesh)-1, we say that we build
            the Dual Graph of the Mesh.
    """
    nbr_n = models[mesh_key]["nbr_n"]
    dimns = models[mesh_key]["dimns"]
    elems = models[mesh_key]["elems"]
    verts = models[mesh_key]["verts"]
    nodes = [ ([], []) for _ in range(nbr_n) ]
    edges = []
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
    # Find the neighbors of each Element and create the Edges.
    nbr_e = 0
    for elem, pot_ngbrs in enumerate(elems_com_verts):
        ngbrs = set(ei for ei in pot_ngbrs
                    if (elem < ei
                    and cond(len([i for i in pot_ngbrs if i == ei]))
                    )
                )
        nodes[elem][0].extend(list(ngbrs))
        edge_beg = nbr_e
        for ngbr in ngbrs:
            edges.append([elem, ngbr])
            nodes[ngbr][0].append(elem)
            nodes[ngbr][1].append(nbr_e)
            nbr_e += 1
        nodes[elem][1].extend(list(range(edge_beg, nbr_e)))
    models[key] = {
        "entity": "graph",
        "nbr_n": nbr_n,
        "nbr_e": nbr_e,
        "nodes": nodes,
        "edges": edges,
        "dimns": models[mesh_key]["dimns"],
        "coord": models[mesh_key]["coord"],
    }
    models["key_lead"] = key


#################################
### Initialization (geometry) ###
#################################

#****************#
# Init from file #
#****************#

def init_GraphGeom_from_mtx(models, records, filename):
    """Build the Graph Geometry (coordinates of the vertices)
    specified by a coord.mtx file.

    NB: There may be one coord per line, or all the coords for one
    element on the same line.
    """
    with open(filename, 'r') as f:
        for line in f:
            if line[0] != "%":
                break
        nbr_n, dimns = tuple(int(w) for w in line.split()[:2])
        coord = []
        line = f.readline()
        words = line.split()
        if len(words) == 1: # one coord per line
            pt = [float(words[0])]
            d = 1
            for line in f:
                pt.append(float(line))
                d += 1
                if d == dimns:
                    coord.append(tuple(pt))
                    d = 0
                    pt = []
        else: # all coords for one node on one line
            coord.append(tuple(float(w) for w in words))
            for line in f:
                coord.append(tuple(float(w) for w in line.split()))
    if "graph" not in models:
        models["graph"] = {
            "nbr_n": nbr_n,
        }
    models["graph"]["dimns"] = dimns
    models["graph"]["coord"] = tuple(coord)


def init_GraphGeom_from_xyz(models, records, filename):
    with open(filename, "r") as f:
        dimns = int(f.readline())
        nbr_n = int(f.readline())
        coord = [None] * nbr_n
        for line in f:
            words = line.split()
            label = int(words[0])
            coord[label] = tuple(float(w) for w in words[1:])
    if "graph" not in models:
        models["graph"] = {
            "nbr_n": nbr_n,
        }
    models["graph"]["dimns"] = dimns
    models["graph"]["coord"] = tuple(coord)


###################################
### Transformation & Properties ###
###################################

def coarsen_Graph(models, records, c_models, key_topo, aggregation):
    """
    """
    nbr_n  = models[key_topo]["nbr_n"]
    edges  = models[key_topo]["edges"]
    nbr_n_ = max(aggregation) + 1
    nodes_ = [ [[], []] for _ in range(nbr_n_) ]
    edges_ = []
    nbr_e_ = 0
    for edge in edges:
        i = aggregation[edge[0]]
        j = aggregation[edge[1]]
        if i != j and i not in nodes_[j][0]:
            edges_.append([i, j])
            nodes_[i][0].append(j)
            nodes_[j][0].append(i)
            nodes_[i][1].append(nbr_e_)
            nodes_[j][1].append(nbr_e_)
            nbr_e_ += 1
    c_models[key_topo] = {
        "entity": "graph",
        "nbr_n" : nbr_n_,
        "nbr_e" : nbr_e_,
        "nodes" : nodes_,
        "edges" : edges_,
    }
    if "dimns" in models[key_topo]:
        c_models[key_topo]["dimns"] = models[key_topo]["dimns"]
        c_models[key_topo]["coord"] = [0] * nbr_n_
        for i, i_ in enumerate(aggregation):
            c_models[key_topo]["coord"][i_] = models[key_topo]["coord"][i]


def check_Graph(models, records, print_models=True):
    """Properties checked:
    (1) Each node's edge contains the node
    (2) Each node's neighbour 'knows' node is one of its neighbors
    (3) Each edge's node contains the edge
    (4) Each edge has exactly 2 ends
    (5) edge[0] < edge[1]
    (6) The ngbrs and edges are ordered and correspond
        (for node i, the jst edge links i to its jst neighbor)
    """
    # TODO
    pass


##############
### Record ###
##############

def Graph_to_grf(models, records, out_file,
    nwgt_version=2, key_topology="graph",
    key_nweights="nweights", key_eweights="eweights",
):
    """Register the Graph in a .grf file (format used by Scotch).

    Keyword argument:
        nwgt_version: 1 or 2: version of grf file to use.
    """
    graph = models[key_topology]
    nwgts = models.get(key_nweights, None)
    ewgts = models.get(key_eweights, None)
    nodes = graph["nodes"]
    if nwgts is None:
        nwgt_version = 1
    # Format
    fmt = [0] # fmt = "ijk" where - i indicates if there are labels
              #                   - j indicates if there are weights on edges
              #                   - k indicates if there are weights on nodes
    fmt.append(int(ewgts is not None))
    if nwgts is not None:
        fmt.append(nwgt_version)
        nbr_c = nwgts["nbr_c"]
        nwgts = nwgts["weights"]
    else:
        fmt.append(0)
    fmt = "".join([str(i) for i in fmt])
    # Write the file
    with open(out_file, "w") as f:
        # Version line
        f.write("0\n")
        # Header line: nb_nodes nb_edges
        f.write("{} {}\n".format(graph["nbr_n"], graph["nbr_e"] * 2))
        f.write("{} {}\n".format(0, fmt))
        # For nwgt_version_2: must write the number of criteria
        if nwgt_version == 2:
            f.write("{}\n".format(nbr_c))
        # Write functions
        # - Node weight
        if nwgts is None:
            def write_nwgt(*args):
                pass
        elif nwgt_version == 1:
            def write_nwgt(f, nwgt):
                f.write("{} ".format(nwgt))
                if wgt == 0:
                    raise ValueError("scotch does not support null weights (node {} has a null weight)".format(ni))
        else:
            def write_nwgt(f, nwgt):
                for wgt in nwgt:
                    f.write("{} ".format(wgt))
        # - Node degree
        def write_deg (f, ngbrs):
            f.write("{} ".format(len(ngbrs)))
        # - Ewgts and ngbrs
        if ewgts is None:
            def write_ewgts_ngbrs(f, nbgrs, _):
                for ngbr in ngbrs:
                    f.write("{} ".format(ngbr))
        else:
            ewgts = ewgts["weights"]
            def write_ewgts_ngbrs(f, nbgrs, edges):
                for ngbr in ngbrs:
                    ei = next(e for e in edges if e in nodes[ngbr][1])
                    wgt = ewgts[ei][0]
                    if wgt == 0:
                        raise ValueError("edge {} has a null weight".format(ei))
                    f.write("{} {} ".format(wgt, ngbr))
        # Write
        for ni, (ngbrs,edges) in enumerate(nodes):
            write_nwgt(f, nwgts[ni])
            write_deg (f, ngbrs)
            write_ewgts_ngbrs(f, ngbrs, edges)
            f.write("\n")


def list_to_line(l):
    return "{}\n".format(str(l)[1:-1].replace(", ", " "))

def Graph_to_mesh(models, filename, z=-1):
    """Register the Graph in a .mesh format.
    NB: Graph Vertices become Mesh Vertices (not Elements).

    Arguments:
        z: int: -1: Use the original coordinate (None in 2D).
                 i >= 0: Use the ith node weight.
    """
    n      = models["n"]
    e      = models["e"]
    edges  = models["graph"]["edges"]
    dimns  = models["geometry"]["dimns" ]
    ecoord = models["geometry"]["ecoord"]
    if z >= 0:
        dimns = 3
        nwgts = models.get("nweights", ((1,) for _ in range(n)))
        nwmax = max(wgt[z] for wgt in nwgts)
        coord = lambda i: list(ecoord[i]) + [nwgts[i][z]*5.0/nwmax] + [0]
    else:
        coord = lambda i: list(ecoord[i]) + [0]
    with open(filename, "w") as f:
        f.write("MeshVersionFormatted 2\n")
        f.write("Dimension\n{}\n".format(dimns))
        f.write("Vertices\n{}\n".format(n))
        for i in range(n):
            f.write(list_to_line(coord(i)))
        f.write("Edges\n{}\n".format(e))
        for j in range(e):
            f.write(list_to_line([end + 1 for end in edges[j]] + [0]))
        f.write("End\n")


def Graph_to_mgraph(models, filename):
    """Register the Graph in a .mgraph file (format used by MeTiS).
    """
    grph = models["graph"]
    nwgt = models.get("nweights")
    hwgt = models.get("hweights")
    ewgt = models.get("eweights")
    n  = models["n"]
    e  = models["e"]
    nbr_c = models["c"]
    nodes = grph["nodes"]
    fmt = "{}{}{}".format(
        0 if hwgt is None else 1, # vertex sizes (communication volume if the node is to transmit)
        0 if nwgt is None else 1, # vertex weights
        0 if ewgt is None else 1, # edge   weights
    )
    # Define function that write a node data #
    # Beware: indexes begin at 1
    def write_node_size(f, node):
        f.write("{}\t".format(hwgt[node][0]))
    def write_node_nwgts(f, node):
        for c in range(nbr_c):
            f.write("{}\t".format(nwgt[node][c]))
    def write_node_ngbrs_ewgts(f, node):
        for ngbr in nodes[node][0]:
            ei = next(e for e in nodes[node][1] if e in nodes[ngbr][1])
            wgt = ewgt[ei][0]
            if wgt == 0:
                raise ValueError("edge {} has a null weight".format(ei))
            f.write("{}\t{}\t".format(ngbr + 1, wgt))
        f.write("\n")
    def write_node_ngbrs(f, node):
        for ngbr in nodes[node][0]:
            f.write("{}\t".format(ngbr + 1))
        f.write("\n")
    # Define the write node function #
    write_fcts = []
    if hwgt is not None:
        write_fcts.append(write_node_size)
    if nwgt is not None:
        write_fcts.append(write_node_nwgts)
    if ewgt is None:
        write_fcts.append(write_node_ngbrs)
    else:
        write_fcts.append(write_node_ngbrs_ewgts)
    write_fcts = tuple(write_fcts)
    def write_node(f, node):
        for write_fct in write_fcts:
            write_fct(f, node)
    # Write the file #
    with open(filename, "w") as f:
        f.write("{}\t{}\t{}\t{}\n".format(n, e, fmt, nbr_c))
        for i in range(n):
            write_node(f, i)


def Graph_to_u(models, filename):
    """Register the Graph in a .u file (format used by PaToH).
    """
    # TODO
    pass


####################
### Function IDs ###
####################

INIT_GRAPH_FCTS = {
    "init_Graph_from_grf"       : init_Graph_from_grf,
    "init_Graph_from_Hypergraph": init_Graph_from_Hypergraph,
    "init_Graph_from_Mesh"      : init_Graph_from_Mesh,
    "init_Graph_from_mtx"       : init_Graph_from_mtx,
    "init_Graph_from_u"         : None, # TODO
}

INIT_GRAPHGEOM_FCTS = {
    "init_GraphGeom_from_mtx": init_GraphGeom_from_mtx,
    "init_GraphGeom_from_xyz": init_GraphGeom_from_xyz,
}

OUTPUT_GRAPH_FCTS = {
    "Graph_to_grf": Graph_to_grf,
}

