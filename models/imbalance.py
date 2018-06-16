"""Functions linked with the imbalance of a Partition.


How to compute the igain (gain in imbalance) of a weight?
=========================================================

 0) Notations
    ---------

    S_p denotes the weight        of part p.
    T_p denotes the target weight of part p.
    imb is the imbalance.
    We consider that the weights are normalized:
    Sum_p (S_p) = 1.

    Recall that we have:

                                  S_p-T_p
    imb = max_p( imb_p ) = max_p( ------- )
                                  1/nbr_p
                         = max_p( nbr_p * (S_p-T_p) ).

    Let h be the most imbalanced part. Then,
    imb = imb_h = nbr_p * (S_h-T_h).

    Let s be the source part of w.
    Let t be the target part of w.

    We call imb' the imbalance after moving w in t.
    We have:
    imb'_s = nbr_p * (S_s - w - T_s)
    imb'_t = nbr_p * (S_t + w - T_t)

    Let g be the gain of moving w from s to t:
    g = imb - imb'.

    If t = h, then the most imbalanced part remains the same, and:
        g = imb_t - imb'_t = - nbr_p*w

 1) Bipartitioning case (nbr_p = 2)
    -------------------------------

    In this case, we have imb_s = -imb_t

    As said before,
    If t = h, then we directly have
        g = -2w
    Else, s = h, so we have
        g = imb_s - max( 2*(S_s - w - T_s),  2*(S_t + w - T_t) )
          = imb_s - max( 2*(S_s - w - T_s), -2*(S_s - w - T_s) )
          = imb_s - max( +(imb_s-2w), -(imb_s-2w) )
          = / 2w          if w < imb_s/2
            \ imb_s - 2w  otherwise

"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.weights import init_Weights_normalized
from crack.utils.errors   import crack_error


def init_even_targets(nbr_p, nbr_c):
    return [[1/nbr_p] * nbr_p for _ in range(nbr_c)]


def imbalances(
    models, records,
    key_nweights="nweights",
    key_partition="partition",
    targets=None,
):
    """Returns a matrix, containing in cell [c][p] the imbalance of
    part p for criterion c.

    Arguments:
        targets: None or list of list of float: Matrix containing in
            cell [c][p] the target normalized weights of part p for
            criterion c. If None, will be set to
                        nbr_p columns
                [ [ 1/nbr_p ... 1/nbr_p ],
                      |      |      |        nbr_c rows
                  [ 1/nbr_p ... 1/nbr_p ] ]
            NB1: Values in targets should be between 0 and 1.
            NB2: If we denote by:
                - sigma_c_p the        weight of part p for criterion c;
                - s_tgt_c_p the target weight of part p for criterion c
                  (s_tgt_c_p = targets[c][p] * totals[c]);
                then the imbalance of part p for criterion c is:
                          sigma_c_p - s_tgt_c_p
                imb_c_p = --------------------- .
                            totals_c / nbr_p
    """
    ### Arguments ###
    nbr_c = models[key_nweights] ["nbr_c"]
    nbr_p = models[key_partition]["nbr_p"]

    parts = models[key_partition]["parts"]
    wgts  = models[key_nweights] ["weights"]
    tots  = models[key_nweights] ["totals"]
    if targets is None:
        targets = init_even_targets(nbr_p, nbr_c)
    ### Compute the imbalances ###
    imbs = [None] * nbr_c
    for c in range(nbr_c):
        pwgts = [
            sum(w[c] for i, w in enumerate(wgts) if parts[i] == p)
                for p in range(nbr_p)
        ]
        imbs[c] = [
            nbr_p * (pwgt/tots[c] - tgt)
                for pwgt, tgt in zip(pwgts, targets[c])
        ]
    return imbs


def imbalance(
    models, records,
    key_nweights="nweights",
    key_partition="partition",
    targets=None,
):
    """The imbalance of a Partition is the maximum imbalance across
    all criteria.
    """
    imbs = imbalances(
        models, records, key_nweights, key_partition, targets
    )
    return max(max(imb_c) for imb_c in imbs)


def get_c_max(imbs):
    imbs_per_c = []
    for c, imbs_c in enumerate(imbs):
        imb_c = max(imbs_c)
        imbs_per_c.append((imb_c, c))
    return max(imbs_per_c)[1]


def get_cp_max(imbs):
    imbs_per_c = []
    for c, imbs_c in enumerate(imbs):
        imb_c = max(imbs_c)
        imbs_per_c.append((imb_c, c, imbs_c.index(imb_c)))
    m = max(imbs_per_c)
    return (m[1], m[2])


def get_p_maxs(imbs):
    p_maxs = []
    for c, imbs_c in enumerate(imbs):
        imb_c = max(imbs_c)
        p_maxs.append(imbs_c.index(imb_c))
    return p_maxs


def get_p_max(imbs):
    imbs_per_c = []
    for imbs_c in imbs:
        imb_c = max(imbs_c)
        imbs_per_c.append((imb_c, imbs_c.index(imb_c)))
    return max(imbs_per_c)[1]


def imbalances_after_move(ws, p_src, p_tgt, nbr_p, imbs):
    """Returns the imbalances if [ws] is moved from [p_src] to
    [p_tgt]. [ws] must be normalized.
    """
    new_imbs = [list(imbs_per_c) for imbs_per_c in imbs]
    for w, imbs_per_c in zip(ws, new_imbs):
        imbs_per_c[p_src] -= nbr_p * w
        imbs_per_c[p_tgt] += nbr_p * w
    return new_imbs


class ConstraintsImbalance(object):
    """Imbalance constraints: partitions that imbalanced more than a
    tolerance are not valid.

    Must provide the following services:
    - can_move(i, p_src, p_tgt, stats): Return a bool,
        indicating if node i can move from p_src to p_tgt.
    - moved(i, p_src, p_tgt, stats): Inform the object that
        node i has moved.
    - copy: Enables to recover the same status to avoid
        recomputing data.
    """
    _KEY_NWGTS = "_normalized_nweights"

    def __init__(self, models=None, records=None, algopt=None, stats=None):
        self.models  = models
        self.records = records
        self.nwgts = None
        self.nbr_p = None
        self.tols  = None
        self.imbs  = None
        self.opts  = None
        if models is not None:
            ### Arguments ###
            # nwgts #
            key_nweights = algopt.get("key_nweights", "nweights")
            if key_nweights not in models:
                init_NWeights_unit(models, records, nbr_n)
            if ConstraintsImbalance._KEY_NWGTS not in models:
                init_Weights_normalized(
                    models, records,
                    key_in=key_nweights,
                    key_out=ConstraintsImbalance._KEY_NWGTS,
                )
            # parts #
            key_partition = algopt.get("key_partition", "partition")
            nbr_p = models[key_partition]["nbr_p"]
            # tolerance #
            tol = algopt["constraints_args"]["tolerance"]
            if not isinstance(tol, list):
                nbr_c = models[key_nweights]["nbr_c"]
                tol = [tol] * nbr_c
            # targets #
            targets = algopt.get("targets")
            ### Attributes ###
            self.nwgts = models[ConstraintsImbalance._KEY_NWGTS]["weights"]
            self.nbr_p = nbr_p
            self.tols  = tol
            self.imbs  = imbalances(
                models, records,
                key_nweights=ConstraintsImbalance._KEY_NWGTS,
                key_partition=key_partition,
                targets=targets,
            )
            self.opts  = {
                "msg": algopt.get("msg", 0)
            }
            if self.opts["msg"] > 0:
                stats["cnstr_value"] = "{:8.3%}".format(max(max(imbsc for imbsc in self.imbs)))

    def can_move(self, i, p_src, p_tgt, stats):
        """This should be a little faster than calling the
        imbalances_after_move function.
        """
        ws   = self.nwgts[i]
        imbs = self.imbs
        tols = self.tols
        nbr_p = self.nbr_p
        return next(
            (False for w, imbsc, tol_c in zip(ws, imbs, tols)
                if imbsc[p_tgt] + nbr_p * w > tol_c
            ),
            True
        )

    def moved(self, i, p_src, p_tgt, stats):
        for w, imbs_per_c in zip(self.nwgts[i], self.imbs):
            imbs_per_c[p_src] -= self.nbr_p * w
            imbs_per_c[p_tgt] += self.nbr_p * w
        if self.opts["msg"] > 0:
            stats["cnstr_value"] = "{:8.3%}".format(max(max(imbsc for imbsc in self.imbs)))

    def copy(self):
        dup = ConstraintsImbalance()
        dup.models  = self.models
        dup.records = self.records
        dup.nwgts   = self.nwgts
        dup.nbr_p   = self.nbr_p
        dup.tols    = self.tols
        dup.imbs    = [list(imbsc) for imbsc in self.imbs]
        dup.opts    = self.opts
        return dup

    def __str__(self):
        imb = max(max(imbsc) for imbsc in self.imb)
        return "imbalance: {:7.3%}".format(self.imb)


