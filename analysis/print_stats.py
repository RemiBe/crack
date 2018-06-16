"""Function to print various statistics on the graph.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.cut        import cut_lambda_minus_one
from crack.models.imbalance  import imbalance, imbalances


def print_stats(
    models,
    records,
    key_topology="graph",
    key_geometry="mesh",
    key_nweights="nweights",
    key_eweights="eweights",
    key_partition="partition",
    weights_crit=0,
    targets=None,
    **algopt
):
    """
    Print options:
        prefix: str or (None)
        nbr_n: bool (False)
        nbr_e: bool (False)
        cut: bool (False)
        imbalance: bool (False)
        imbalances: bool (False)
    """
    msg = []
    if "prefix" in algopt:
        msg.append(algopt["prefix"])
    if algopt.get("nbr_n", False):
        if key_topology in models:
            nbr_n = models[key_topology]["nbr_n"]
        elif key_geometry in models:
            nbr_n = models[key_geometry]["nbr_n"]
        else:
            nbr_n = models[key_nweights]["nbr_n"]
        msg.append("nbr_n: {}".format(nbr_n))
    if algopt.get("nbr_e", False):
        msg.append("nbr_e: {}".format(models[key_topology]["nbr_e"]))
    if algopt.get("nbr_p", False):
        msg.append("nbr_p: {}".format(models[key_partition]["nbr_p"]))
    if algopt.get("cut", False):
        cut = cut_lambda_minus_one(
            models, records,
            key_topology=key_topology,
            key_eweights=key_eweights,
            key_partition=key_partition,
            weights_crit=weights_crit,
        )
        msg.append("cut {}".format(cut))
    if algopt.get("imbalance", False):
        imb = imbalance(
            models, records, key_nweights, key_partition, targets
        )
        msg.append("imbalance {:.3%}".format(imb))
    if algopt.get("imbalances", False):
        imbs = imbalances(
            models, records, key_nweights, key_partition, targets
        )
        l = ["imbalances"]
        for imbsc in imbs:
            l.append("{:8.3%}".format(max(imbsc)) for imbsc in imbs)
        msg.append(" ".join(l))
    print("  '->", " ".join(msg))


