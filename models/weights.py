"""Weights are associated with nodes/elements and/or edges.
To each node/edge, multiple weights can be given.

Weights are stored as a dictionary:
- nbr_n  : int: Number of nodes/edges.
- nbr_c  : int: Number of criteria: number of weights per node/edge.
- weights: ((int, ...), ...): In cell (i, c): the cth weight of
  the ith node/edge.
- totals : (int, ...): If cell c: the sum of the cth weight of all
  nodes/edges
"""

__author__ = "Remi Barat"
__version__ = "1.0"


from crack.utils.errors import crack_error


######################
### Initialization ###
######################

def format_crit(crit_spec):
    """Format the criteria as a list of int. Criteria can be entered
    as:
    - an int
    >>> crit: 1      # outputs: [1]

    - a list of int
    >>> crit: [0, 2] # outputs: [0, 2]

    - a string seperating numbers with ',' and/or '-'
    >>> crit: 0, 2-4 # outputs: [0, 2, 3, 4]
    """
    if isinstance(crit_spec, int):
        crit = [crit_spec]
    elif isinstance(crit_spec, list):
        crit = crit_spec
    elif isinstance(crit_spec, str):
        crit = []
        for subc in crit_spec.split(","):
            if "-" in subc:
                begin, end = tuple(subc.split("-"))
                crit.extend(range(int(begin), int(end)))
            else:
                crit.append(int(subc))
    else:
        crack_error(ValueError, "init_Weights_...",
            "Unrecognized 'crit' (got {}). Should be an int, or list of int, or str of int and ',' and '-'.".format(crit_spec))
    return crit


def _add_wgts_key(models, key_in, key_out, nbr_n, nbr_c, entity):
    """If [key_out] (typically, "nweights") is not in [models],
    add it and initialize its fields. [key_in] is the list of the
    weights keys (used to automatically modify the weights when
    coarsening/prolonging).
    """
    if not isinstance(key_in, list):
        key_in = [key_in]
    if key_out in models:
        wgts = models[key_out]
        c_old = wgts["nbr_c"]
        if nbr_c > c_old:
            d = nbr_c - c_old
            wgts["nbr_c"  ] = nbr_c
            wgts["weights"] = [w + [0] * d for w in wgts["weights"]]
            wgts["totals" ] = wgts["totals"] + [0] * d
            for k in key_in:
                if k not in wgts["keys"]:
                    wgts["keys"].append(key_in)
    else:
        models[key_out] = {
            "entity" : entity,
            "nbr_n"  : nbr_n,
            "nbr_c"  : nbr_c,
            "weights": [[0] * nbr_c for _ in range(nbr_n)],
            "totals" : [0] * nbr_c,
            "keys"   : key_in,
        }


# Called before the nweights/eweights initialization functions
def condition_models(init_fct, models, records, crit, key_out, entity, **kwargs):
    """Prepare the [models] to the [init_fct].

    Indeed, an init_[NEH]Weights_xxx function will add the computed
    weights to *models[key_out][c]* where c are specified in [crit].

    Arguments:
        crit: int or list of int or str. See *format_crit* function.
        key_out: str
    """
    keys_in = kwargs.get("key_in")
    if isinstance(keys_in, list):
        key_in = keys_in[0]
    else:
        key_in = keys_in
    if key_in is not None:
        kwargs["key_in"] = key_in
    # Format the list of criteria that will be initialized
    crit  = format_crit(crit)
    nbr_c = max(crit) + 1
    for c in crit:
        wgts = init_fct(models, records, **kwargs)
        nbr_n = len(wgts)
        if key_out not in models or nbr_c > models[key_out]["nbr_c"]:
            _add_wgts_key(models, keys_in, key_out, nbr_n, nbr_c, entity)
        totc = 0
        for i, w in enumerate(wgts):
            models[key_out]["weights"][i][c] += w
            totc += w
        models[key_out]["totals"][c] += totc


#*********************************#
# Common initialization functions #
#*********************************#
# (that are not specific to nweights/eweights)

def init_Weights_from_file(models, records, filename=None, extract_keys=None):
    """Initialize the weights from data stored in a file.

    Arguments:
        models: dict: The Weights will be stored here.
        filename: str: Path to the file which contains the data. An
            example of such file is provided below.

    Optional Arguments:
        extract_keys: str or list of str or dict: The keys of the
            weights that will be extracted. If dict, maps the extracted
            keys with the keys that will be used in the current session.
            If None, all weights will be extracted.

    Example: 2 node weights of 3 criteria, 2 edge weights of 1 criterion
        >>> # weights nweights 2 3
        >>> 10 80 13
        >>> 100 93 12
        >>> # weights my_edge_wgts 2 1
        >>> 12
        >>> 39

        If [extract_keys] is None, [models] will be updated with:
        >>> "nweights": {
        >>>     "entity" : "weights",
        >>>     "nbr_n"  : 2,
        >>>     "nbr_c"  : 3,
        >>>     "weights": ((10, 80, 13), (100, 93, 12)),
        >>>     "totals" : (110, 173, 25)
        >>> }
        >>> "my_edge_wgts": {
        >>>     "entity" : "weights",
        >>>     "nbr_n"  : 2,
        >>>     "nbr_c"  : 1,
        >>>     "weights": ((12,), (39,))
        >>>     "totals" : (51,)
        >>> }
    """
    if filename is None:
        crack_error(ValueError, "init_Weights_from_file",
            "Need to provide a 'filename' from which the Weights will be read.")
    # Which keys will we retrieve data from?
    if extract_keys is not None:
        if isinstance(extract_keys, str):
            extract_keys = {extract_keys: extract_keys}
        elif isinstance(extract_keys, list):
            extract_keys = {k: k for k in extract_keys}
        elif not isinstance(extract_keys, dict):
            crack_error(ValueError, "init_Weights_from_file",
                "Wrong type of 'extract_keys' (should be str, list or dict).")
    # Read file to retrieve data
    with open(filename, "r") as f:
        for line in f:
            if not line or line[0] != "#":
                continue
            words = line.split()
            if words[1] != "weights":
                continue
            key_out = None
            if extract_keys is None:
                key_out = words[2]
            elif words[2] in extract_keys:
                key_out = extract_keys[words[2]]
            if key_out is not None:
                nbr_n = int(words[3])
                nbr_c = int(words[4])
                wgts  = [None] * nbr_n
                tots  = [0] * nbr_c
                for i in range(nbr_n):
                    line = f.readline()
                    wgts[i] = [int(w) for w in line.split()]
                    for c, w in enumerate(wgts):
                        tots[c] += w
                models[key_out] = {
                    "entity" : "weights",
                    "nbr_n"  : nbr_n,
                    "nbr_c"  : nbr_c,
                    "weights": wgts,
                    "totals" : tots,
                }


def init_Weights_normalized(models, records, key_in, key_out=None):
    """Create a normalized weight distribution (in [key_out]) from the
    weight distribution in [key_in].
    """
    if key_out is None:
        key_out = key_in + "__norm"
    wgts = models[key_in]["weights"]
    tots = models[key_in]["totals"]
    models[key_out] = {
        "entity" : "weights",
        "nbr_n"  : models[key_in]["nbr_n"],
        "nbr_c"  : models[key_in]["nbr_c"],
        "weights": [
                [wc / tot_c for wc, tot_c in zip(w, tots)]
                for w in wgts
        ],
        "totals" : [1] * models[key_in]["nbr_c"],
    }


