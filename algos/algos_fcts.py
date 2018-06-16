"""Regroup all the partitioning functions in a common dictionary.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import crack.algos.direct_algos.all_in_one_part as direct_all_in_one
import crack.algos.direct_algos.random_part     as direct_random
import crack.algos.refine_algos.vn_first_part   as refine_vn_first
import crack.algos.refine_algos.vn_best_part    as refine_vn_best
import crack.algos.refine_algos.fm_part         as refine_fm


ALGOS = {
    "all_in_one_part": direct_all_in_one.all_in_one_part,
    "random_part"    : direct_random.random_part,

    "vn_first_part"  : refine_vn_first.vn_first_part,
    "vn_best_part"   : refine_vn_best.vn_best_part,
    "fm_part"        : refine_fm.fm_part,
}

