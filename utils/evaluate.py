"""Evaluate a string expression.
"""

__author__ = "Remi Barat"
__version__ = "1.0"


import ast
import operator as op


# supported operators #
operators = {
    # Operations on numbers a and b
    ast.Add   : op.add,      # a + b
    ast.Sub   : op.sub,      # a - b
    ast.Mult  : op.mul,      # a * b
    ast.Div   : op.truediv,  # a / b (float division)
    ast.Pow   : op.pow,      # a ** b
    ast.UAdd  : op.pos,      # + a
    ast.USub  : op.neg,      # - a
    ast.Lt    : op.lt,       # a <  b
    ast.LtE   : op.le,       # a <= b
    ast.Eq    : op.eq,       # a == b
    ast.NotEq : op.ne,       # a != b
    ast.GtE   : op.ge,       # a >= b
    ast.Gt    : op.gt,       # a >  b
    # Boolean expressions e and f
    ast.Not   : op.not_,     # not e
    ast.And   : op.and_,     # e and f
    ast.Or    : op.or_,      # e or  f
    ast.BitXor: op.xor,      # e ^ f
    ast.Invert: op.invert,   # ~e
}

# The main function #
def eval_expr(expr, keywords=None, only_keywords=False):
    """Returns the value of an expression given as a string. A value
    in [expr] that is a key in [keywords] will be replaced by its
    value in [keywords].

    Inspirated from:
    http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string

    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    >>> eval_expr("current < 0.5 * original", {"current": 7, "original": 10})
    False
    >>> eval_expr("0 or (1 and 2)", {0: False, 1: True, 2: False}, only_keywords=True)
    False
    """
    if keywords is None:
        kw = {}
    else:
        kw = keywords.copy()
    kw["True" ] = True
    kw["False"] = False
    if only_keywords:
        return _eval_no_numbers(ast.parse(expr, mode='eval').body, kw)
    else:
        return _eval(ast.parse(expr, mode='eval').body, kw)


def _eval(node, keywords):
    if isinstance(node, ast.Num):        # <number>
        return node.n
    elif isinstance(node, ast.Name):     # <id> (should be a keywords key)
        return keywords[node.id]
    elif isinstance(node, ast.BinOp):    # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left, keywords), _eval(node.right, keywords))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand, keywords))
    elif isinstance(node, ast.Compare):
        return operators[type(node.ops[0])](_eval(node.left, keywords), _eval(node.comparators[0], keywords))
    elif isinstance(node, ast.BoolOp):  # Boolean operator: either "and" or "or" with two or more values
        if type(node.op) == ast.And:
            return all(_eval(val, keywords) for val in node.values)
        else:  # Or:
            for val in node.values:
                result = _eval(val, keywords)
                if result:
                    return result
            return result
    else:
        raise TypeError(node)


def _eval_no_numbers(node, keywords):
    if isinstance(node, ast.Num):        # <number>
        return keywords[node.n]
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., ~1
        return operators[type(node.op)](_eval_no_numbers(node.operand, keywords))
    elif isinstance(node, ast.Compare):
        return operators[type(node.ops[0])](_eval_no_numbers(node.left, keywords), _eval_no_numbers(node.comparators[0], keywords))
    elif isinstance(node, ast.BoolOp):  # Boolean operator: either "and" or "or" with two or more values
        if type(node.op) == ast.And:
            return all(_eval_no_numbers(val, keywords) for val in node.values)
        else:  # Or:
            for val in node.values:
                result = _eval_no_numbers(val, keywords)
                if result:
                    return result
            return result
    else:
        raise TypeError(node)


