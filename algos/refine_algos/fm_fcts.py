"""Options for the FM algorithm.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


#######################
### Stop outer loop ###
#######################

def stop__no_improvement(models, records, algopt, stats):
    if "last_obj_value" not in stats:
        stop = False
    else:
        stop = stats["last_obj_value"] <= stats["obj_value"]
    stats["last_obj_value"] = stats["obj_value"]
    if algopt["msg"] > 0:
        print("  |   [FM] Extern loop: {:5} moves (total: {:6}), obj: {:8}, cnstr: {}".format(
            stats["inner__moves_done"],
            stats["moves_done"],
            stats["obj_value"],
            stats["cnstr_value"])
        )
    return stop


#######################
### Stop inner loop ###
#######################

def stop__all_locked(models, records, algopt, stats, locks):
#    stop = next((l for l in locks if not l), None) is None
    if "stop_inner__all_locked_nbr_n" not in stats:
        entity = algopt.get("key_partition_out", "partition")
        stats["stop_inner__all_locked_nbr_n"] = models[entity]["nbr_n"]
    nbr_n = stats["stop_inner__all_locked_nbr_n"]
    return stats["inner__moves_done"] >= nbr_n


def stop__cng(models, records, algopt, stats, locks):
    if "stop_inner__cng__nbr_moves" not in stats: # init
        nbr_moves = algopt["stop_inner"]["args"]["nbr_moves"]
        if nbr_moves < 1:
            entity = algopt.get("key_partition_out", "partition")
            nbr_moves = nbr_moves * models[entity]["nbr_n"]
        stats["stop_inner__cng__nbr_moves"] = nbr_moves
    nbr_moves = stats["stop_inner__cng__nbr_moves"]
    stop = stats["inner__moves_neg_row"] >= nbr_moves
    return stop


def stop__ng(models, records, algopt, stats, locks):
    if "stop_inner__ng__nbr_moves" not in stats: # init
        nbr_moves = algopt["stop_inner"]["args"]["nbr_moves"]
        if nbr_moves < 1:
            entity = algopt.get("key_partition_out", "partition")
            nbr_moves = nbr_moves * models[entity]["nbr_n"]
        stats["stop_inner__ng__nbr_moves"] = nbr_moves
    nbr_moves = stats["stop_inner__ng__nbr_moves"]
    stop = stats["inner__moves_neg"] >= nbr_moves
    return stop


####################
### Function IDs ###
####################

STOP_OUT_FCTS = {
    "no_improvement": stop__no_improvement,
}

STOP_INN_FCTS = {
    "all_locked"               : stop__all_locked,
    "consecutive_negative_gain": stop__cng,
    "negative_gain"            : stop__ng,
}


