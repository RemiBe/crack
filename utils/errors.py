"""Handle errors.
"""

__author__ = "Remi Barat"
__version__ = "1.0"


def crack_error(err_type, fct_name, msg):
    raise err_type("'x|x, Crack Error in {}: {}".format(fct_name, msg))
