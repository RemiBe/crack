"""Functions to name repositories/files, for example depending on the
current time.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import datetime   as dt


def get_time():
    """Returns the date in a string of the form: `yyyy_mm_dd-hh_mm'.

    Exemple :
        `2015_03_17-14_04' is the kind of output.
    """
    return dt.datetime.now().strftime("%Y_%m_%d-%H_%M")


def get_basename(path, extension):
    """Returns the filename (without its whole path) without its
    extension.

    Argument:
        path: str
        extension: str: The extension (with a dot if there is one).

    Example:
        >>> print get_basename("~/Meshes/my_mesh.mesh", ".mesh")
        ... my_mesh
    """
    return path.split("/")[-1][:-len(extension)]


