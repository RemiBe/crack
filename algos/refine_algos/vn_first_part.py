"""Partition a set of vectors of numbers by moving at each step a
vector that decreases the imbalance.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import bisect
import math
import sys
from   time import time

from crack.models.partition    import copy_Partition
from crack.models.imbalance    import imbalances, imbalances_after_move
from crack.models.weights      import init_Weights_normalized
from crack.operators.iterators import ITER_NODES_FCTS, ITER_PARTS_FCTS, update_iter_opts
from crack.utils.errors        import crack_error


def vn_first_part(models, records,
    key_nweights="nweights",
    key_partition_in="partition", key_partition_out="partition",
    iter_nodes="first_cycle", iter_parts="first_cycle",
    stop_after=None, stop_balanced=False, # TODO
    targets=None,
    msg=False,
    **algopt
):
    """Refine an initial partition by successively moving nodes when
    it decreases the imbalance.

    Arguments:
        nbr_p: Number of parts required.

    Options:
        key_partition_in: str: Key of the Partition in [models] that
            will be refined. (Default is 'partition.)
        key_nweights: str: Key of the Weights in [models] that will be
            partitioned. (Default is 'nweights'.)
        key_partition_out: str: Key to store the Partition in [models].
            (Default is 'partition').
        iter_nodes: 'first_cycle'|'random'
        iter_parts: 'first_cycle'
        stop_after: int or (float in [0, 1])
    """
    ### Arguments
    try:
        nbr_p = algopt["nbr_p"]
    except KeyError:
        crack_error(ValueError, "random_part",
            "Missing argument(s): nbr_p")
    ### Options ###
    if nbr_p == 2:
        iter_parts = "bipart"
    if key_partition_in != key_partition_out:
        copy_Partition(models, key_partition_in, key_partition_out)
    parts = models[key_partition_out]["parts"]
    key_norm_wgts = key_nweights + "__norm"
    if key_norm_wgts not in models:
        init_Weights_normalized(
            models, records,
            key_in=key_nweights,
        )
    nwgts = models[key_norm_wgts]["weights"]
    if stop_after is None:
        stop_after = models[key_nweights]["nbr_n"]
    elif stop_after > 0 and stop_after < 1:
        stop_after = models[key_nweights]["nbr_n"] * stop_after

    start = time()

    ### Initialize ###
    moves_done   = 0
    moves_tslm   = 0 # Number of move Tested Since Last Move
    moves_tested = 0
    iter_nodes_fct = ITER_NODES_FCTS[iter_nodes]
    iter_nodes_opts = {
        "key_topology": key_norm_wgts,
    }
    iter_parts_fct = ITER_PARTS_FCTS[iter_parts]
    iter_parts_opts = {
        "key_topology": key_norm_wgts,
        "last_p_tgt"  : nbr_p-1,
    }
    imbs = imbalances(models, records, key_nweights=key_nweights, key_partition=key_partition_out, targets=targets)
    imb  = max(max(imb_cp) for imb_cp in imbs)
    if msg:
        print("'-|-, [vn_first] imb = {:6.5f}".format(imb))

    ### Algorithm ###

    for i in iter_nodes_fct(models, iter_nodes_opts):
        moves_tested += 1
        moves_tslm   += 1
        p_src = parts[i]
        ws    = nwgts[i]
        for p_tgt in iter_parts_fct(models, nbr_p, p_src, iter_parts_opts):
            new_imbs = imbalances_after_move(ws, p_src, p_tgt, nbr_p, imbs)
            new_imb  = max(max(imb_cp) for imb_cp in new_imbs)
            if new_imb < imb:
                # Move the node
                moves_done += 1
                moves_tslm = 0
                parts[i] = p_tgt
                imbs     = new_imbs
                imb      = new_imb
                update_iter_opts(iter_nodes_opts, restart=True)
                update_iter_opts(iter_parts_opts, restart=True, last_p_tgt=p_tgt)
                if msg:
                    print("  |   [vn_first] {:3d}/{:5d}: moved {:3d} (p{} -> p{}) imb = {:6.5f}".format(moves_done, moves_tested, i, p_src, p_tgt, new_imb))
                break
        if moves_tslm > stop_after:
            break

    if msg:
        print("  |   [vn_first] {:3d}/{:5d}: imb = {:6.5f}".format(moves_done, moves_tested, imb))


