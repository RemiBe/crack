"""Common functions for geometric models (Mesh, GraphGeom).
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import math


def dist_d2(p1, p2):
    """Returns the euclidian distance in a plane between p1 and p2.
    """
    return math.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )


def dist_d3 (p1, p2):
    """Returns the euclidian distance in space between p1 and p2.
    """
    return math.sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)


DIST_FCTS = {
    2: dist_d2,
    3: dist_d3,
}


def translate(geom, delta=None):
    """Translates the coordinates.

    Arguments:
        delta: list of float: Give in delta[d] the translation along
          x, y, z, ... axis. If None, the translation will be
          so that all coordinates become positive.
    """
    dimns = geom["dimns"]
    if delta is None:
        delta = [None for _ in range(dimns)]
    ### Compute the translation when needed.
    max_neg = tuple(0 for _ in delta)
    if [dl for dl in delta if dl is None]:
        coord  = geom["coord"]
        for pt in coord:
            max_neg = tuple(min(max_neg[d], pt[d]) for d in range(dimns))
        max_neg = [0 if dl >= 0 else -dl for dl in max_neg]
        delta = [mn if dl is None else dl for mn,dl in zip(max_neg,delta)]
    ### Translate
    geom["coord"] = tuple(tuple(pt[d]+delta[d] for d in range(dimns)) for pt in geom["coord"])
    if "vcoord" in geom: # Vertices of the Mesh
        geom["vcoord"] = tuple(tuple(pt[d]+delta[d] for d in range(dimns)) for pt in geom["vcoord"])


def homothetic(geom, coefs):
    """Multiply the coordinates by the [coefs] given.

    Arguments:
        delta: list of float: Give in coefs[d] the coefficient along
          x, y, z, ... axis.
    """
    dimns = geom["dimns"]
    geom["coord"] = tuple(tuple(pt[d]*coefs[d] for d in range(dimns)) for pt in geom["coord"])
    if "vcoord" in geom: # Vertices of the Mesh
        geom["vcoord"] = tuple(tuple(pt[d]*coefs[d] for d in range(dimns)) for pt in geom["vcoord"])


