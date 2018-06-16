"""This module provides functions to partition a set of vectors of numbers.

                              Warning
+-----------------------------------------------------------------------+
| The k-partitioning version works, but I do not think that it does the |
| best movement at each step. Indeed, the computation of the gain is    |
| false, but luckily it actually does not use it...                     |
+-----------------------------------------------------------------------+

Let:
- c0 be the most imbalanced criterion:
  u_0 = max (u_c_p)
        c,p
- p0 is the heaviest part for c0: u_0_0 = u_0

Then to decrease u = max (u_c_p) = u_0, we need to remove a node
from p0.             c,p


Let w be a node.
Moving w in/from part p leads to an imbalance for p for crit c of:
u_p_c' = s_p_c - w - (s_p_c - w)
       = s_p_c - s_p_c - 2*w
       = u_p_c - 2*w
The gain of moving w in part p for criterion c is:
g_p_c = |u_p_c| - |u_p_c'|
- If u_p_c < 0 (which cannot be the case for c == c0, p == p0):
  g_p_c[w] = -u_p_c - |u_p_c - 2*w|
                      '----,----'
                          < p
  g_p_c[w] = -u_p_c -(-u_p_c + 2*w)
  g_p_c[w] = -2*w
- If u_p_c >= 0
  g_p_c[w] = u_p_c - |u_p_c - 2*w|
           = { 2*w           if w <= u_p_c/2
             { 2*u_p_c - 2*w if w >= u_p_c
We can conclude that:
1) A node of weight >= u_p_c has a negative gain.
   So, a node of weight >= u_0 will never move.
   '--> Nodes of weights >= u_0 have a None gain for
        each part and each crit.
2) The nodes of a part with a negative imbalance have a gain of -2*w.
   '--> After a move, the gains for crits for parts that
        keep a negative imbalance don't need to be updated.
3) If we order the nodes for crit c by weights:

                 u_p_c/2       u_p_c
                    |            |
                    v            v
     w0_c < w1_c < ... < wi_c < ... < wn_c
                    ^            ^
      gain = 2*w:   |  gain = u_p_c - 2*w:
       increase    peak      decrease
                                 |
                   > 0           0    < 0
   So when updating, we need to update the nodes from
   min(u_p_c/2, u_p_c'/2) to max(u_p_c, u_p_c')
   However, we only know the position of u_p_c/2.

More remarks:
4) When there is several criteria, the best move for the most imbalanced
   one is also the global best move if the most imbalanced criterion
   after this move did not change.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import bisect
import math
import sys
from   time import time

from crack.models.partition import init_Partition_from_args
from crack.models.imbalance import init_even_targets


class GainTableNumbersKPart:
    """
    Attributes:
        nbr_c: int: Number of criteria.
        nbr_p: int: Number of parts.
        wghts: tuple of tuple of int: Original weights
        wnorm: tuple of tuple of float: Normalized weights.
              (node)  (crit)  (wght)
        wposn: list of list of int  : Position in gain table of this node.
              (crit)  (node)  (index)
        gains: list of list of list of (int, float): Gains of each node of a
              (part)  (crit)  (node)  (index, gain)  part by crit, sorted by
                                                     weight.
        inflx: list of list of (int) : Positions of inflexion points for
              (part)  (crit)  (index)  gains for each part and each crit.
                                       The inflexion points are located
                                       at nodes of wght u/2.
        unbal: list of list of float: Unbalance for each part and crit.
              (part)  (crit)  (unbal) Negative when the considered part is
                                      of weight below 0.5.
    """
    def __init__(self, nweights, partition, targets=None, msg=False, debug=False):
        """Sets the global parameters (n, k, c), and initializes:
        - the wnorm table using the **init_wnorm** function
        - the unbal table using the **init_unbal** function
        - the inflx (inflexion point table) \ using the **init_gains**
          the gains table                   / function
        """
        self.nbr_n = nweights["nbr_n"]
        self.nbr_c = nweights["nbr_c"]
        self.wghts = nweights["weights"]
        self.nbr_p = partition["nbr_p"]
        self.parts = partition["parts"]

        self.wnorm = None
        self.wposn = None
        self.unbal = None
        self.gains = None
        self.inflx = None
        self.umax  = -1.0
        self.cumax = -1
        self.pumax = -1

        self.options = {"msg": msg, "debug": debug}

        self.init_wnorm(nweights["totals"])
        if targets is None:
            targets = init_even_targets(self.nbr_p, self.nbr_c)
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        targets = [[targets[c][p] for c in range(nbr_c)] for p in range(nbr_p)]
        part_wghts = [
            [
                sum(w[c] for i, w in enumerate(self.wnorm)
                    if self.parts[i] == p)
                for c in range(self.nbr_c)
            ] for p in range(self.nbr_p)
        ]
        self.init_unbal(targets, part_wghts)
        self.init_gains()

        self.stats = {
            "inner": 0,
        }

    def init_wnorm(self, wtotl):
        """Initializes the normalized weights (wnorm) table, defined
        such that wnorm[i][c] = W_c(i) / S_c
        """
        wghts = self.wghts
        self.wnorm = [
            [wc/wtotlc for wc, wtotlc in zip(w, wtotl)]
            for w in wghts
        ]

    def init_unbal(self, wtgts, wpart):
        """Initializes the unbalance (unbal) table and the maximum
        imbalance (umax), the most imbalanced criterion (cmax) and
        the overweighted part for the most imbalanced criterion
        (pmax).

        unbal[p][c] is the imbalance for part p for criterion c.
        """
        self.unbal = [
            [(w-wtgt) / wtgt for w, wtgt in zip(wp, wtgtp)]
            for wp, wtgtp in zip(wpart, wtgts)
        ]
        self.update_umax()
        if self.options["debug"]:
            unbals_th = [[round(u, 7) for u in l] for l in bal(self.wghts, self.parts)]
            unbals_fd = [[round(u, 7) for u in l] for l in self.unbal]
            if unbals_th != unbals_fd:
                raise ValueError("==Debug== Imbalance_after_move({}) are {} but should be {}".format(index, unbals_fd, unbals_th))

    def update_umax(self):
        umax = 0
        cmax = 0
        pmax = 0
        for p, imbs_p in enumerate(self.unbal):
            for c, imb_cp in enumerate(imbs_p):
                if imb_cp > umax:
                    cmax = c
                    umax = imb_cp
                    pmax = p
        self.umax  = umax
        self.cumax = cmax
        self.pumax = pmax

    def init_gains(self):
        """gains[p][c][i] gain for part p for criterion c when moving
        vertex of index i in part p.

        wposn[c][i] position of vertex i in the gain table of any part
        for criterion c.

        inflx[p][c] position of the vertex of maximum gain for
        part p for criterion c.
        """
        nbr_n  = self.nbr_n
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        self.gains = [
            [[None] * nbr_n for _ in range(nbr_c)]
            for _ in range(nbr_p)
        ]
        self.wposn = [[None] * nbr_n for _ in range(nbr_c)]
        sort_fct = lambda i: self.wghts[i][c]
        wsort = [
            [i for i in sorted(range(n), key=sort_fct)]
            for c in range(nc)
        ]

        inflx = [[0] * nbr_c for _ in range(nbr_p)]
        bestg = [[0] * nbr_c for _ in range(nbr_p)]
        for c in range(nbr_c):
            for pos, index in enumerate(wsort[c]):
                self.wposn[c][index] = pos
                for p in range(nbr_p):
                    gain = self.compute_gain(index, c, p)
                    if gain >= bestg[p][c]:
                        inflx[p][c] = pos
                        bestg[p][c] = gain
                    self.gains[p][c][pos] = (index, gain)
        self.inflx = inflx

    def compute_gain(self, index, c, p):
        """Returns the gain in imbalance for crit c when moving the [index]
        node in part p. None if one of the weights of the node is greater
        than umax.
        """
        nbr_p = self.nbr_p
        wghts = self.wnorm[index]
        if max(wghts) >= nbr_p * self.umax:
            return None
        w = wghts[c]
        u = self.unbal[p][c]
        if self.parts[index] == p:
            if u <= 0: # p is underweighted: gain < 0 and always the same
                gain = -nbr_p*w
            elif nbr_p*w < u: # no change of most imbalanced part when moving w.
                gain =  nbr_p*w
            else: # fills a bit the gap.
                gain =  2*u - nbr_p*w
        else:
            if u >= 0: # p is overweighted: gain < 0 and always the same.
                gain = -nbr_p*w
            elif nbr_p*w < -u: # no change of most imbalanced part.
                gain =  nbr_p*w
            else: # fills a bit the gap.
                gain = -2*u - k*nbr_p
        if self.options["debug"]:
            p_src = self.parts[index]
            if p == p_src:
                p_tgt = (p + 1) % k
            else:
                p_tgt = p
            unbal_old = bal(self.wghts, self.parts)
            self.parts[index] = p_tgt
            unbal_new = bal(self.wghts, self.parts)
            self.parts[index] = p_src
            gain_th = math.fabs(unbal_old[p_tgt][c]) - math.fabs(unbal_new[p_tgt][c])
        return gain

    def compute_unbal_after_move(self, index, p_src, p_tgt):
        """Computes the list of imbalance if node [index] is moved from
        p_src to p_tgt. Returns the new_umax, new_cumax, new_pumax and
        new_unbal if the move is made.

        Argument:
            index: int: index of node.
        """
        nbr_p = self.nbr_p
        imbs  = [list(l) for l in self.unbal]
        wghts = self.wnorm[index]
        for c, wc in enumerate(wghts):
            imbs[p_src][c] -= nbr_p*wc
            imbs[p_tgt][c] += nbr_p*wc
        umax  = 0
        cumax = 0
        pumax = 0
        for p, imbsc in enumerate(imbs):
            for c, imb in enumerate(imbsc):
                if imb > umax:
                    umax  = imb
                    cumax = c
                    pumax = p
        return umax, cumax, pumax, imbs

    def find_move(self):
        """Returns the move that leads to the minimum imbalance, given the
        current partitioning.

        Notes:
        1. We need to reduce the imbalance for the most imbalanced crit
           (cumax), so we need to remove a node from the part that is the
           heaviest for this crit.
        2. For this part, consider one move. If the max imbalance after this
           move is still for cumax, then the next moves in the gain table
           (that has a smaller gain) cannot have a better gain.
           However, if the cumax changes after the move, then it is possible
           that a move of smaller gain for the current cumax leads to a
           greater gain.
        """
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        umax  = self.umax
        cumax = self.cumax
        p_src = self.pumax
        inner = 0
        # Compute imbalances after moves
        computed_uam = [[] for _ in range(nbr_p)] # uam: imbalance after move
        computed_u   = [[] for _ in range(nbr_p)] # u  : umax after move
        computed_icp = [[] for _ in range(nbr_p)] # icp: index and cumax and pumax
        def update_positions(pos_dict, p):
            move_inf = False
            move_sup = False
            l = len(self.gains[p][cumax])
            inf = pos_dict["inf"]
            sup = pos_dict["sup"]
            if pos_dict["inf"] < 0:
                # consider moving towards sup.
                if pos_dict["sup"] < l:
                    index_sup, _ = self.gains[p][cumax][sup]
                    if self.wnorm[index_sup][cumax] < umax:
                        move_sup = True
            elif pos_dict["sup"] > l-1:
                move_inf = True
            else:
                index_inf, gain_inf = self.gains[p][cumax][inf]
                index_sup, gain_sup = self.gains[p][cumax][sup]
                while gain_inf is None:
                    inf -= 1
                    if inf < 0:
                        break
                    index_inf, gain_inf = self.gains[p][cumax][inf]
                while gain_sup is None:
                    sup += 1
                    if sup > l-1:
                        break
                    index_sup, gain_sup = self.gains[p][cumax][sup]
                pos_dict["inf"] = inf
                pos_dict["sup"] = sup
                if gain_inf is not None and gain_sup is not None:
                    if gain_sup > gain_inf:
                        move_sup = True
                    else:
                        move_inf = True
                elif gain_inf is not None:
                    move_inf = True
                elif gain_sup is not None:
                    move_sup = True
            if move_sup:
                pos_dict["best_gain"]  = pos_dict["sup"]
                pos_dict[      "sup"] += 1
            elif move_inf:
                pos_dict["best_gain"]  = pos_dict["inf"]
                pos_dict[      "inf"] -= 1
            else:
                pos_dict["best_gain"] = None
        positions = {
            "best_gain": self.inflx[p_src][cumax],
            "inf"      : self.inflx[p_src][cumax] - 1,
            "sup"      : self.inflx[p_src][cumax] + 1,
        }
        while (positions["best_gain"] is not None):
            index, gumax = self.gains[p_src][cumax][ positions["best_gain"] ]
            if self.parts[index] == p_src and gumax is not None:
                for p_tgt in range(nbr_p):
                    if p_tgt == p_src:
                        continue
                    nwu, nwc, nwp, uam = self.compute_unbal_after_move(index, p_src, p_tgt)
                    computed_uam[p_tgt].append(uam)
                    computed_u  [p_tgt].append(nwu)
                    computed_icp[p_tgt].append((index, nwc, nwp))
                    if cumax == nwc and p_src == nwp:
                        break
                inner += 1
            update_positions(positions, p_src)
        # Among the computed imbalances, find the minimal one.
        best_p    =  0
        best_move =  0
        best_umax = None
        for p, computed_up in enumerate(computed_u):
            nb_moves   = len(computed_up)
            if nb_moves == 0:
                continue
            best_move_p = min(
                range(nb_moves), key=lambda pos: computed_up[pos]
            )
            best_umax_p = computed_up[best_move_p]
            if best_umax is None or best_umax_p < best_umax:
                best_p    = p
                best_move = best_move_p
                best_umax = best_umax_p
        if best_umax is None:
            return None, None, self.umax, self.cumax, self.pumax, self.unbal
        best_index = computed_icp[best_p][best_move][0]
        best_cumax = computed_icp[best_p][best_move][1]
        best_pumax = computed_icp[best_p][best_move][2]
        new_unbals = computed_uam[best_p][best_move]
        self.stats["inner"] += inner
        return best_index, best_p, best_umax, best_cumax, best_pumax, new_unbals

    def move_node(self, index, p_tgt, new_umax, new_cumax, new_pumax, new_unbals):
        nbr_p = self.nbr_p
        self.parts[index] = p_tgt
        # 1- update the imbalances with the given new imbalances
        old_unbals = self.unbal
        self.unbal = new_unbals
        self.umax  = new_umax
        self.cumax = new_cumax
        self.pumax = new_pumax
        for p in range(nbr_p):
            for c, wposnc in enumerate(self.wposn):
                pos  = self.wposnc[index]
                gain = self.compute_gain(index, c, p)
                self.gains[p][c][pos] = (index, gain)
        # 2- update the gains and inflexion points lists
        self.update_gains(old_unbals)

    def update_gains(self, old_unbal):
        """We need to update the gain for nodes of weight from
        min(old_unbal/2, new_unbal/2) to min(old_unbal, new_unbal).
        """
        nbr_n = self.nbr_n
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        umax_old = max(max(l) for l in old_unbal)
        # Update the gains
        for p in range(nbr_p):
            for c in range(nbr_c):
                old_u = old_unbal [p][c]
                new_u = self.unbal[p][c]
                thr   = min(old_u/2, new_u/2)
                if old_u < 0 or new_u < 0:
                    # Update for nodes from old_unbal/2, decreasing to new_unbal/2
                    pos = self.inflx[p][c] - 1
                    while pos >= 0:
                        index, _ = self.gains[p][c][pos]
                        if self.wnorm[index][c] < thr:
                            break
                        gain = self.compute_gain(index, c, p)
                        self.gains[p][c][pos] = (index, gain)
                        pos -= 1
                    # Update for nodes from old_unbal/2, increasing until umax
                pos = self.inflx[p][c]
                while pos < n:
                    index, _ = self.gains[p][c][pos]
                    if self.wnorm[index][c] > umax_old:
                        break
                    gain = self.compute_gain(index, c, p)
                    self.gains[p][c][pos] = (index, gain)
                    pos += 1
                # Update the positions of best gains
                gains = [
                    (pos, gain)
                        for pos, (index, gain) in enumerate(self.gains[p][c])
                        if gain is not None
                ]
                if gains:
                    best_pos, best_gain = max(gains, key=lambda e: e[1])
                else:
                    best_pos = 0
                self.inflx[p][c] = best_pos

    def _print_headcolumns(self):
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        for p in range(nbr_p):
            print(" part {:^43} | |".format(p)),
        print()
        for p in range(nbr_p):
            for c in range(nc):
                print(" crit {:^17} |".format(c)),
            print("|"),
        print()

    def print_gains(self, step):
        nbr_c = self.nbr_c
        nbr_p = self.nbr_p
        print(">>> step {:2d} - normalized gains <<<".format(step))
        print("=" * 34)
        self._print_headcolumns()
        for pos in range(self.nbr_n):
            for p in range(nbr_p):
                for c in range(nbr_c):
                    index, g = self.gains[p][c][pos]
                    w = self.wnorm[index][c]
                    print("{:3d}:"    .format(index)), # index
                    print("({:5.4f}, ".format(w)    ), # relative_wght
                    if g is None:
                        print("{:6})".format(None)), # relative_gain
                    else:
                        print("{:+5.3f})".format(g)), # relative_gain
                    if self.inflx[p][c] == pos:
                        print("x|"),
                    else:
                        print(" |"),
                print("|"),
            print()
        for _ in range(nbr_p):
            for _ in range(nbr_c):
                print("-" * 23 + " |"),
            print("|"),
        print()
        for p in range(nbr_p):
            for c in range(nbr_c):
                print("tot:  {:5.4f}".format(sum(w[c] for index,w in enumerate(self.wnorm) if self.parts[index] == p))),
                print(" ({:+7.1%}) |".format(self.unbal[p][c])),
            print("|"),
        print()
        print("umax: {:5.2%}, cumax: {}, pumax: {}".format(self.umax, self.cumax, self.pumax))
        print()


class GainTableNumbersBipart(GainTableNumbersKPart):
    """A little faster to compute imbalance_after_move and find the best move.

    The gains of node i in part p are None if i is in part p.
    """
    def __init__(self, nweights, partition, targets=None, msg=False, debug=False):
        GainTableNumbersKPart.__init__(self, nweights, partition, targets, msg, debug)

    def init_gains(self):
        nbr_n = self.nbr_n
        nbr_c = self.nbr_c
        self.gains = [
            [
                [None] * nbr_n for _ in range(nbr_c)
            ] for _ in range(2)
        ]
        self.wposn = [[None] * nbr_n for _ in range(nbr_c)]
        wsort = []
        for c in range(nbr_c):
            sort_fct = lambda i: self.wghts[i][c]
            wsort.append(sorted(range(nbr_n), key=sort_fct))
        inflx = [[0] * nbr_c for _ in range(2)]
        bestg = [[0] * nbr_c for _ in range(2)]
        for c in range(nbr_c):
            for pos, index in enumerate(wsort[c]):
                self.wposn[c][index] = pos
                for p in range(2):
                    if self.parts[index] == p:
                        gain = None
                    else:
                        gain = self.compute_gain(index, c, p)
                        if gain is not None and gain >= bestg[p][c]:
                            inflx[p][c] = pos
                            bestg[p][c] = gain
                    self.gains[p][c][pos] = (index, gain)
        self.inflx = inflx

    def compute_gain(self, index, c, p):
        """Returns the gain in imbalance for crit c when moving the [index]
        node. None if one of the weights of the node is greater than umax.
        """
        wghts = self.wnorm[index]
        if max(wghts) < self.umax:
            w = wghts[c]
            u = -self.unbal[p][c]
            if u < 0: # p is already overweighted: gain is < 0.
                return -2*w
            elif 2*w < u:
                return  2*w
            else:
                return  2*(u-w)
        return None

    def compute_unbal_after_move(self, index, p_src, p_tgt):
        """Returns the list of imbalance if node [index] is moved, and
        if cumax changes after this move.

        Argument:
            index: int: index of node.
        """
        nbr_c = self.nbr_c
        unbals = [[None] * nbr_c for _ in range(2)]
        umax  = 0
        cumax = 0
        pumax = 0
        w = self.wnorm[index]
        for c in range(nbr_c):
            u_src = self.unbal[p_src][c]
            u_tgt = self.unbal[p_tgt][c]
            wc = w[c]
            new_u_src = u_src - 2*wc
            new_u_tgt = u_tgt + 2*wc
            unbals[p_src][c] = new_u_src
            unbals[p_tgt][c] = new_u_tgt
            if new_u_src > umax:
                umax  = new_u_src
                cumax = c
                pumax = p_src
            if new_u_tgt > umax:
                umax = new_u_tgt
                cumax = c
                pumax = p_tgt
        if self.options["debug"]:
            self.parts[index] = p_tgt
            unbals_th = [[round(u, 7) for u in l] for l in bal(self.wghts, self.parts)]
            unbals_fd = [[round(u, 7) for u in l] for l in unbals]
            self.parts[index] = p_src
            if unbals_th != unbals_fd:
                print("==Debug== Unbalance_after_move({}) are {} but should be {}".format(index, unbals_fd, unbals_th))
                print("          gains_tgt: {}".format([self.gains[p_tgt][c][self.wposn[c][index]][1] for c in range(nbr_c)]))

        return umax, cumax, pumax, unbals

    def move_node(self, index, p_tgt, new_umax, new_cumax, new_pumax, new_unbals):
        nbr_c = self.nbr_c
        p_src = self.pumax
        self.parts[index] = p_tgt
        # 1- update the imbalances with the given new imbalances
        old_unbals = self.unbal
        self.unbal = new_unbals
        self.umax  = new_umax
        self.cumax = new_cumax
        self.pumax = new_pumax
        for c in range(nbr_c):
            pos  = self.wposn[c][index]
            gain = self.compute_gain(index, c, p_src)
            self.gains[p_tgt][c][pos] = (index, None)
            if gain is not None:
                self.gains[p_src][c][pos] = (index, -gain)
            else:
                self.gains[p_src][c][pos] = (index, None)
        # 2- update the gains and inflexion points lists
        self.update_gains(old_unbals)

    def find_move(self):
        """Returns the move that leads to the minimum imbalance, given the
        current partitioning.

        Notes:
        1. We need to reduce the imbalance for the most imbalanced crit
           (cumax), so we need to remove a node from the part that is the
           heaviest for this crit.
        2. For this part, consider one move. If the max imbalance after this
           move is still for cumax, then the next moves in the gain table
           (that has a smaller gain) cannot have a better gain.
           However, if the cumax changes after the move, then it is possible
           that a move of smaller gain for the current cumax leads to a
           greater gain.
        """
        nbr_c = self.nbr_c
        umax  = self.umax
        cumax = self.cumax
        p_src = self.pumax
        p_tgt = 1 - p_src
        inner = 0
        # Compute imbalances after moves
        computed_uam = [] # uam: imbalance after move
        computed_u   = [] # u  : umax after move
        computed_icp = [] # icp: index and cumax and pumax
        def update_positions (pos_dict):
            move_inf = False
            move_sup = False
            l = len(self.gains[p_tgt][cumax])
            inf = pos_dict["inf"]
            sup = pos_dict["sup"]
            if pos_dict["inf"] < 0:
                # consider moving towards sup.
                if pos_dict["sup"] < l:
                    index_sup, _ = self.gains[p_tgt][cumax][sup]
                    if self.wnorm[index_sup][cumax] < self.umax:
                        move_sup = True
            elif pos_dict["sup"] > l-1:
                move_inf = True
            else:
                index_inf, gain_inf = self.gains[p_tgt][cumax][inf]
                index_sup, gain_sup = self.gains[p_tgt][cumax][sup]
                while gain_inf is None:
                    inf -= 1
                    if inf < 0:
                        break
                    index_inf, gain_inf = self.gains[p_tgt][cumax][inf]
                while gain_sup is None:
                    sup += 1
                    if sup > l-1:
                        break
                    index_sup, gain_sup = self.gains[p_tgt][cumax][sup]
                pos_dict["inf"] = inf
                pos_dict["sup"] = sup
                if gain_inf is not None and gain_sup is not None:
                    if gain_sup > gain_inf:
                        move_sup = True
                    else:
                        move_inf = True
                elif gain_inf is not None:
                    move_inf = True
                elif gain_sup is not None:
                    move_sup = True
            if move_sup:
                pos_dict["best_gain"]  = pos_dict["sup"]
                pos_dict[      "sup"] += 1
            elif move_inf:
                pos_dict["best_gain"]  = pos_dict["inf"]
                pos_dict[      "inf"] -= 1
            else:
                pos_dict["best_gain"] = None
        positions = {
            "best_gain": self.inflx[p_tgt][cumax],
            "inf"      : self.inflx[p_tgt][cumax] - 1,
            "sup"      : self.inflx[p_tgt][cumax] + 1,
        }
        while (positions["best_gain"] is not None):
            index, gumax = self.gains[p_tgt][cumax][ positions["best_gain"] ]
            if gumax is not None:
                nwu, nwc, nwp, uam = self.compute_unbal_after_move(index, p_src, p_tgt)
                computed_uam.append(uam)
                computed_u  .append(nwu)
                computed_icp.append((index, nwc, nwp))
                if self.options["debug"]:
                    fuam = [ ["{:5.2%}".format(m) for m in l] for l in uam ]
                    print("== {:3d} == Positions : (best: {}, inf: {}, sup: {})".format(inner, positions["best_gain"], positions["inf"], positions["sup"]))
                    print("          Consider {} of gain {} (new_u: {}). uam {}: continue {}".format(index, gumax, nwu, fuam, cumax != nwc))
                if cumax == nwc:
                    break
            update_positions(positions)
            inner += 1
        # Among the computed imbalances, find the minimal one.
        nb_moves   = len(computed_u)
        if nb_moves == 0:
            return None, p_tgt, self.umax, self.cumax, self.pumax, self.unbal
        best_move  = min(range(nb_moves), key=lambda pos: computed_u[pos])
        best_umax  = computed_u  [best_move]
        best_index = computed_icp[best_move][0]
        best_cumax = computed_icp[best_move][1]
        best_pumax = computed_icp[best_move][2]
        new_unbals = computed_uam[best_move]
        self.stats["inner"] += inner
        if self.options["debug"]:
            fuam = [ ["{:5.2%}".format(m) for m in l] for l in new_unbals ]
            print("          Selected {}: new_u: {} (new_c: {}, new_unbals: {}, new_p: {})".format(best_index, best_umax, best_cumax, new_unbals, best_pumax))
        return best_index, p_tgt, best_umax, best_cumax, best_pumax, new_unbals

    def update_gains(self, old_unbal):
        """We need to update the gain for nodes of weight from
        min(old_unbal/2, new_unbal/2) to min(old_unbal, new_unbal).
        """
        nbr_n = self.nbr_n
        nbr_c = self.nbr_c
        umax_old = max(max(l) for l in old_unbal)
        def give_gain(index, c, p, pos):
            gain = (self.compute_gain(index, c, p) if self.parts[index] != p else None)
            self.gains[p][c][pos] = (index, gain)
        # Update the gains
        for p in range(2):
            for c in range(nbr_c):
                old_u = old_unbal [p][c]
                new_u = self.unbal[p][c]
                thr   = min(old_u/2, new_u/2)
                if old_u < 0 or new_u < 0: # Update for nodes from old_unbal/2, decreasing to new_unbal/2
                    pos = self.inflx[p][c] - 1
                    while pos >= 0:
                        index, _ = self.gains[p][c][pos]
                        if self.wnorm[index][c] < thr:
                            break
                        give_gain(index, c, p, pos)
                        pos -= 1
                # Update for nodes from old_unbal/2, increasing until umax
                pos = self.inflx[p][c]
                while pos < nbr_n:
                    index, _ = self.gains[p][c][pos]
                    if self.wnorm[index][c] > umax_old:
                        break
                    give_gain(index, c, p, pos)
                    pos += 1
                # Update the positions of best gains
                gains = [
                    (pos, gain)
                        for pos, (index, gain) in enumerate(self.gains[p][c])
                        if gain is not None
                ]
                if gains:
                    best_pos, best_gain = max(gains, key=lambda e: e[1])
                else:
                    best_pos = 0
                self.inflx[p][c] = best_pos


def vn_best_part(
    models, records,
    nbr_p,
    key_nweights="nweights",
    key_partition_in="partition", key_partition_out="partition",
    targets=None,
    msg=False, debug=False,
    **algopt
):
    """From an initial partitioning, successively moves the vector that
    decreases the most the imbalance.

    Uses a gain table to have an immediate access to the best vector.
    There is one gain table per part, registering the gains in balance
    if moving a node in this part.
    """
    ### Options ###
    nweights  = models[key_nweights]
    if key_partition_in != key_partition_out:
        copy_Partition(models, key_partition_in, key_partition_out)
    partition = models[key_partition_out]
    if models[key_partition_out]["nbr_p"] == 2:
        GainTable = GainTableNumbersBipart # Should be faster.
    else:
        GainTable = GainTableNumbersKPart

    start = time()
    gt = GainTable(nweights, partition, targets, msg, debug)

    # Begining of the algorithm
    while(True):

        index, p_tgt, new_umax, new_cumax, new_pumax, new_unbals = gt.find_move()

        if new_umax >= gt.umax:
            break

        if msg:
            gain = gt.umax - new_umax
            print("  |   [vn_best] moved {:3d} of gain {:6.5f}: f = {:6.5f} (inner: {:5d})".format(index, gain, new_umax, gt.stats["inner"]))

        gt.move_node(index, p_tgt, new_umax, new_cumax, new_pumax, new_unbals)

    if msg > 0:
        print("  |   [vn_best] {:3d}/{:5d}: imb = {:6.5f}".format(0, 0, gt.umax))


