"""The GainTables used for easy access to the gain of a node. The
gain of a node is here the decrease in cut when switching the part
of this node.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import bisect
from   collections import defaultdict
import copy   as cp
import random as rd

from crack.models.models_fcts import CONSTRAINTS_OBJ
from crack.models.cut         import cut_lambda_minus_one, gain__cut_lambda_minus_one__graph, gain__cut_lambda_minus_one__hypergraph
from crack.models.eweights    import init_EWeights_unit
from crack.models.hweights    import init_HWeights_unit
from crack.models.partition   import copy_Partition


CLEAN_GAINS = True
SORT_GAINS = False


class GainTableFMCut(object):
    """Records the gains in cut of all nodes, to be able to:
    - find the move of best/worst/... gain quickly
    - after moving a node, update the gains only for its neighbors.

    NB: The eweights have to be integers.
        For more efficiency, GainTables can specialize their behavior
        depending of the number of parts (Bipart/Kpart) and the
        topologic entity (Graph/Hypergraph).

    Attributes:
        - gain_nodes: list: In cell i: the gain when moving
            the ith node (for k-partititioning, depends on the part)
        - gain_table: dict: Key g stores the nodes of gain g.
        - gain_values: list: Sorted list of the gain values: enables
            easy access to the best/worse gains.
        - models: dict: Easy access to the models.
        - records: dict: Easy access to the records.
        - constraints: An object that needs methods:
            - can_move(i, p_src, p_tgt, stats): Return a bool,
                indicating if node i can move from p_src to p_tgt.
            - moved(i, p_src, p_tgt, stats): Inform the object that
                node i has moved.
            - copy: Enables to recover the same status to avoid
                recomputing data.
    """
    _KEY_GAIN_FCT = "_gt_gain_fct"  # Depends on graph/hypergraph
    _KEY_HEWGTS   = "_gt_heweights" # idem
    _KEY_TOPOLOGY = "_gt_topology"  # idem
    _KEY_PARTS_RE = "_gt_partition_recovery"

    @classmethod
    def init(cls, models, records, algopt, stats):
        """This method should be called instead of __init__, for it
        calls __init__ from the right subclass (Bipart or KPart).
        """
        nbr_p = algopt["nbr_p"]
        key_topology = algopt.get("key_topology", "graph")
        entity = models[key_topology]["entity"]
        if nbr_p == 2:
            gt_cls = GainTableFMCutBipart
        else:
            gt_cls = GainTableFMCutKPart
        GAIN_CUT_FCTS = {
            "graph"     : gain__cut_lambda_minus_one__graph,
            "hypergraph": gain__cut_lambda_minus_one__hypergraph,
        }
        KEYS = {
            "graph"     : ("key_eweights", "eweights", init_EWeights_unit),
            "hypergraph": ("key_hweights", "hweights", init_HWeights_unit),
        }
        algopt[GainTableFMCut._KEY_GAIN_FCT] = GAIN_CUT_FCTS[entity]
        algopt[GainTableFMCut._KEY_HEWGTS  ] = KEYS[entity]
        algopt[GainTableFMCut._KEY_TOPOLOGY] = algopt.get("key_topology", entity)
        return gt_cls(models, records, algopt, stats)


    def __init__(self, models=None, records=None, algopt=None, stats=None):
        """Common code for the Bipart/KPart subclass __init__. The
        parts that are special (initialization of the gains) are
        handled by the [init_gains] methods in each subclass.

        Options (given in the [algopt] dict):
        """
        self.gain_nodes  = None
        self.gain_table  = None
        self.gain_values = None
        self.constraints = None
        self.models      = models
        self.records     = records
        self.opts        = None
        self.topo        = None
        self.parts       = None
        self.hewgts      = None
        self.recovery    = None
        if models is not None:
            ### Arguments ###
            key_topo   = algopt[GainTableFMCut._KEY_TOPOLOGY]
            spec_he    = algopt[GainTableFMCut._KEY_HEWGTS]
            key_hewgts = algopt.get(spec_he[0], spec_he[1])
            def_hewgts = spec_he[2]
            key_parts  = algopt.get("key_partition_out", "partition")
            # topology #
            topology   = models[key_topo]
            self.topo  = topology
            # heweights #
            if key_hewgts not in models:
                def_hewgts(models, records, key_in=key_topo)
            heweights = models[key_hewgts]
            self.hewgts = heweights["weights"]
            # partition #
            partition = models[key_parts]
            self.parts = partition
            # gain function #
            gain_fct = algopt[GainTableFMCut._KEY_GAIN_FCT]
            # constraints #
            key_cnstr = algopt["constraints_fct"]
            self.constraints = CONSTRAINTS_OBJ[key_cnstr](
                models, records, algopt, stats
            )
            ### Compute the gains ###
            self.init_gains(topology, heweights, partition, gain_fct)
            ### Init the opts ###
            self.opts = {
                "select": algopt.get("select", {"algo": "best_valid"}),
                "ties"  : algopt.get("break_ties", {"algo": "last"}),
                "msg"   : algopt["msg"],
                "key_partition": key_parts,
            }
            ### Init the stats ###
            stats["obj_value"] = cut_lambda_minus_one(
                models, records,
                key_topology=key_topo,
                key_eweights=key_hewgts,
                key_partition=key_parts
            )
            stats["best_obj_value"] = stats["obj_value"]


    ###########################
    ### BREAKTIES FUNCTIONS ###
    ###########################

    def break_ties__first(self, moves, stats):
        return moves[0]

    def break_ties__last(self, moves, stats):
        return moves[-1]

    def break_ties__random(self, moves, stats):
        return rd.choice(moves)

    ################
    ### Recovery ###
    ################

    def recover_best(self, stats):
        if CLEAN_GAINS:
            self.clean_gains()
        if stats["obj_value"] > stats["best_obj_value"]:
            key_partition = self.opts["key_partition"]
            if self.recovery is not None:
                self.models[key_partition] = self.models[GainTableFMCut._KEY_PARTS_RE]
                del self.models[GainTableFMCut._KEY_PARTS_RE]
            stats["obj_value"] = stats["best_obj_value"]
            best = self.recovery
        else:
            best = self
        stats["inner__moves"        ] = 0
        stats["inner__moves_neg"    ] = 0
        stats["inner__moves_neg_row"] = 0
        return best


class GainTableFMCutBipart(GainTableFMCut):

    def init_gains(self, topology, heweights, partition, gain_fct):
        """Compute the gains.
        """
        nbr_n = topology["nbr_n"]
        parts = partition["parts"]
        gain_nodes = [None] * nbr_n
        gain_table = defaultdict(list)
        for i in range(nbr_n):
            g = gain_fct(topology, heweights, partition, i, 1-parts[i])
            gain_nodes[i] = g
            gain_table[g].append(i)
        self.gain_nodes = gain_nodes
        self.gain_table = gain_table
        if not CLEAN_GAINS:
            self.gain_values = sorted(self.gain_table.keys())

    def clean_gains(self):
        to_del = []
        for gain in self.gain_table:
            if not self.gain_table[gain]:
                to_del.append(gain)
        for gain in to_del:
            del self.gain_table[gain]

    def change_gain(self, i, new_gain):
        """Change the value of the gain for node [i] to [new_gain].
        """
        old_gain = self.gain_nodes[i]
        if old_gain == new_gain:
            return
        # Gains per nodes #
        self.gain_nodes[i] = new_gain
        # Gain table and gain values #
        self.gain_table[old_gain].remove(i)
        if not CLEAN_GAINS and not self.gain_table[old_gain]:
                del self.gain_table[old_gain]
                self.gain_values.remove(old_gain)
        if SORT_GAINS and new_gain not in self.gain_table:
            bisect.insort(self.gain_values, new_gain)
        self.gain_table[new_gain].append(i)

    def move(self, locks, stats):
        """Move a node. The node is choose depending on the 'select',
        'tie-break', 'constraints_fct' and 'constraints_args' functions.
        """
        SELECT_FCTS = {
            "best_valid": self.select__best_valid,
        }
        BREAK_TIES = {
            "first": self.break_ties__first,
            "last" : self.break_ties__last,
            "random": self.break_ties__random,
        }
        ### Select the move ###
        select_algo = self.opts["select"]["algo"]
        select_args = self.opts["select"].get("args", {})
        g, l = SELECT_FCTS[select_algo](locks, stats, **select_args)
        if not l: # No more possible moves
            return False
        i, p_src, p_tgt = BREAK_TIES[self.opts["ties"]["algo"]](l, stats)
        ### Save structure before performing a move of negative gain ###
        ### for the first time                                       ###
        new_obj = stats["obj_value"] - g
        rec = False
        if (g < 0 and new_obj < stats["best_obj_value"]):
                self.recovery = self.copy()
                stats["best_obj_value"] = stats["obj_value"]
                rec = True
        ### Perform the move ###
        parts = self.parts["parts"]
        parts[i] = p_tgt
        locks[i] = True
        ### Update gains ###
        nodes = self.topo["nodes"]
        ewgts = self.hewgts
        new_gains = {i: -g}
        for j, e in zip(nodes[i][0], nodes[i][1]):
            if j in new_gains:
                continue
            if parts[j] == p_tgt:
                new_gains[j] = self.gain_nodes[j] - 2*ewgts[e][0]
            else:
                new_gains[j] = self.gain_nodes[j] + 2*ewgts[e][0]
        for j, new_gain in new_gains.items():
            self.change_gain(j, new_gain)
        ### Inform Constraints object of the move ###
        self.constraints.moved(i, p_src, p_tgt, stats)
        ### Record statistics ###
        stats["obj_value"] = new_obj
        stats["moves_done"] += 1
        stats["inner__moves_done"] += 1
        if g <= 0:
            stats["inner__moves_neg"] += 1
            stats["inner__moves_neg_row"] += 1
        else:
            stats["inner__moves_neg_row"] = 0
        ### Msg ###
        if self.opts["msg"] > 1:
            print("  |   [FM] Moved {:9d} (gain: {:6d} | obj: {:9}, | cnstr: {:9} | cng: {:4d})".format(i, g, stats["obj_value"], stats["cnstr_value"], stats["inner__moves_neg_row"]), "(Saved)" if rec else "")
        return True

    ########################
    ### SELECT FUNCTIONS ###
    ########################

    def select__best_valid(self, locks, stats):
        if SORT_GAINS:
            l  = []
            ig = len(self.gain_values) - 1
            can_move = self.constraints.can_move
            parts    = self.parts["parts"]
            while not l and ig > 0:
                g = self.gain_values[ig]
                l = [
                    (i, parts[i], 1-parts[i])
                        for i in self.gain_table[g]
                        if (not locks[i] and
                            can_move(i, parts[i], 1-parts[i], stats))
                ]
                ig -= 1
        else:
            l  = []
            lg = list(self.gain_table.keys())
            can_move = self.constraints.can_move
            parts    = self.parts["parts"]
            while not l and lg:
                g = max(lg)
                lg.remove(g)
                l = [
                    (i, parts[i], 1-parts[i])
                        for i in self.gain_table[g]
                        if (not locks[i] and
                            can_move(i, parts[i], 1-parts[i], stats))
                ]
        return g, l

    ################
    ### Recovery ###
    ################

    def copy(self):
        dup = GainTableFMCutBipart()
        dup.gain_nodes  = self.gain_nodes[:]
        dup.gain_table  = cp.deepcopy(self.gain_table)
        if not CLEAN_GAINS:
            dup.gain_values = self.gain_values[:]
        else:
            dup.gain_values = None
        dup.constraints = self.constraints.copy()
        dup.models      = self.models
        dup.records     = self.records
        dup.opts        = self.opts
        dup.topo        = self.topo
        copy_Partition(
            self.models,
            self.opts["key_partition"],
            GainTableFMCut._KEY_PARTS_RE
        )
        dup.parts       = self.models[GainTableFMCut._KEY_PARTS_RE]
        dup.hewgts      = self.hewgts
        dup.recovery    = None
        return dup

    #############
    ### Print ###
    #############

    def __str__(self):
        gt = self.gain_table
        s = []
        s.append("Gain values: {}")
        s.append("    {}".format(self.gain_values))
        s.append("Gains per nodes:")
        s.append("    {}".format(self.gain_nodes))
        s.append("Gain Table: {")
        for g in self.gain_values:
            s.append("    {}: {}".format(g, gt[g]))
        s.append("}")
        return "\n".join(s)


class GainTableFMCutKPart(object):

    # TODO

    def init_gains(self, topology, heweights, partition, gain_fct):
        nbr_n = topology ["nbr_n"]
        nbr_p = topology ["nbr_p"]
        parts = partition["parts"]
        gain_nodes = [[None] * nbr_n for _ in range(nbr_p)]
        gain_table = defaultdict(list)
        for i in range(nbr_n):
            for p in range(nbr_p):
                if p == parts[i]:
                    gain_nodes[p][i] = None
                else:
                    g = gain_fct(topology, heweights, partition, i, p)
                    gain_nodes[p][i] = g
                    gain_table[g].append((i, p))
        self.gain_nodes = gain_nodes
        self.gain_table = gain_table


