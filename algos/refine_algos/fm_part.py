"""Fiduccia-Mattheyses algorithm. At each step, a move that decreases
the most the objective function is performed.

The selection of the move is accelerated by the use of a gain table
structure, defined in crack.algos.gain_tables.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


import bisect
import copy   as cp
from   time   import time

from crack.algos.fm_fcts       import STOP_OUT_FCTS, STOP_INN_FCTS
from crack.algos.gain_tables.gain_table_cut import GainTableFMCut
from crack.algos.gain_tables.gain_table_imb import GainTableFMImbalance
from crack.operators.iterators import ITER_NODES_FCTS, ITER_PARTS_FCTS
from crack.utils.errors        import crack_error


FM_GAIN_TABLES = {
    "cut"      : GainTableFMCut,
    "imbalance": GainTableFMImbalance,
}


def fm_part(
    models, records,
    **algopt
):
    """
    key_topology="graph",
    key_nweights="nweights",
    key_eweights="eweights",
    key_hweights="hweights",
    iter_parts="firsrt_cycle",
    break_ties="last",
    targets=None,
):
    """
    ### Options ###
    # parts #
    key_partition_in  = algopt.get("key_partition_in" , "partition")
    key_partition_out = algopt.get("key_partition_out", "partition")
    if key_partition_in != key_partition_out:
        copy_Partition(models, key_partition_in, key_partition_out)
    nbr_n = models[key_partition_out]["nbr_n"]

    # msg #
    algopt.setdefault("msg", 0)

    # stop loop condition #
    if "stop_inner" in algopt:
        stop_inn = STOP_INN_FCTS[algopt["stop_inner"]["algo"]]
    else:
        stop_inn = STOP_INN_FCTS["all_locked"]
    if "stop_outer" in algopt:
        stop_out = STOP_OUT_FCTS[algopt["stop_outer"]["algo"]]
    else:
        stop_out = STOP_OUT_FCTS["no_improvement"]

    # stats #
    stats = {
        "moves_done"          : 0,
        "inner__moves_done"   : 0,
        "inner__moves_neg"    : 0,
        "inner__moves_neg_row": 0,
        "obj_value"           : None,
        "cnstr_value"         : None,
    }

    # objective #
    objective_fct = algopt["objective_fct"]
    gt_obj = FM_GAIN_TABLES[objective_fct].init(
        models, records, algopt, stats
    )

    ### Algorithm ###
    while not stop_out(models, records, algopt, stats):
        locks = [False] * nbr_n
        while not stop_inn(models, records, algopt, stats, locks):
            moved = gt_obj.move(locks, stats)
            if not moved: # No more possible moves.
                break
        gt_obj = gt_obj.recover_best(stats)


