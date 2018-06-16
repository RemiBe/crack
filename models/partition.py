"""A Partition is a vector that gives in cell i the part of the ith
node.

A Partition is a dictionary defining the fields:
- entity: 'partition'
- nbr_n: int: The number of Nodes.
- nbr_p: int: The number of Parts.
- parts: list of int: In the ith cell, the part of the ith Node.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


######################
### Initialization ###
######################

def init_Partition_from_args(models, records, key="partition", nbr_p=None, parts=None):
    """Assigns in [models] a Partition model to [key].

    Arguments:
        models: dict: The created Partitionin will be assigned to [key]
            in [models].
        nbr_p: int: Number of parts.
        parts: list: Initial part of each node.
    """
    if nbr_p is None:
        nbr_p = len(set(parts))
    models[key] = {
        "entity": "partition",
        "nbr_n" : len(parts),
        "nbr_p" : nbr_p,
        "parts" : list(parts),
    }


def init_Partition_from_map(models, records, filename, key="partition", nbr_p=None):
    """Assigns in [models] a Partition (stored in a .map file, format
    used by Scotch) model to [key].

    Arguments:
        models: dict: The created Partitionin will be assigned to [key]
            in [models].
        nbr_p: int: Number of parts.
        filename: list: Path to the .map file.
    """
    with open(filename, "r") as f:
        nbr_n = int(f.readline())
        parts = [0] * nbr_n
        for line in f:
            label, part = tuple(int(w) for w in line.split())
            parts[label] = part
    if nbr_p is None:
        nbr_p = len(set(parts))
    models[key] = {
        "entity": "partition",
        "nbr_n": nbr_n,
        "nbr_p": nbr_p,
        "parts": parts,
    }


def init_Partition_from_metis_part(models, records, filename, key="partition", nbr_p=None):
    """Assigns in [models] a Partition (stored in a .part file, format
    used by MeTiS) model to [key].

    Arguments:
        models: dict: The created Partitionin will be assigned to [key]
            in [models].
        nbr_p: int: Number of parts.
        filename: list: Path to the .part file.
    """
    parts = []
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            parts.append(int(line))
    nbr_n = len(parts)
    if nbr_p is None:
        nbr_p = len(set(parts))
    models[key] = {
        "entity": "partition",
        "nbr_n": nbr_n,
        "nbr_p": nbr_p,
        "parts": parts,
    }


def init_Partition_from_patoh_part(models, records, filename, key="partition", nbr_p=None):
    """Assigns in [models] a Partition (stored in a .part.[nbr_p] file,
    format used by PaToH) model to [key].

    Arguments:
        models: dict: The created Partitionin will be assigned to [key]
            in [models].
        nbr_p: int: Number of parts.
        filename: list: Path to the .part file.
    """
    # The structures #
    parts = 0
    with open(filename, "r") as f:
        for line in f:
            for p in line.split():
                parts.append(int(p))
    nbr_n = len(parts)
    if nbr_p is None:
        nbr_p = len(set(parts))
    models[key] = {
        "entity": "partition",
        "nbr_n": nbr_n,
        "nbr_p": nbr_p,
        "parts": parts,
    }


#############
### Utils ###
#############

def copy_Partition(models, key_in, key_out):
    models[key_out] = {
        "entity": "partition",
        "nbr_n" : models[key_in]["nbr_n"],
        "nbr_p" : models[key_in]["nbr_p"],
        "parts" : list(models[key_in]["parts"]),
    }


##############
### Record ###
##############

def Partition_to_map(partition, filename):
    """Write in [filename] the Partition in the Scotch format.
    """
    nbr_n = partition["nbr_n"]
    parts = partition["parts"]
    with open(filename, "w") as f:
        f.write("{}\n".format(nbr_n))
        for i, p in enumerate(parts):
            f.write("{}\t{}\n".format(i,p))


####################
### Function IDs ###
####################

INIT_PARTITION_FCTS = {
    "init_Partition_from_args"       : init_Partition_from_args,
    "init_Partition_from_map"        : init_Partition_from_map,
    "init_Partition_from_metis_part" : init_Partition_from_metis_part,
    "init_Partition_from_patoh_part" : init_Partition_from_patoh_part,
}


