"""Executes the functions specified in the .yaml files given.

Usage:
    crack_part.py -h | --help
    crack_part.py (<spec_file>)*

Arguments:
    spec_file: You can provide as many specification files as you
        want, and Crack will execute their directives in order.
        These files should be written in yaml. See the crack/docs/
        or the crack/examples/yaml/ files for more details on how
        to write specification files.

Options:
    -h --help  Documentation on usage and file formats.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from   time   import time
import random as rd
import sys
import yaml

from crack.algos.algos_fcts       import ALGOS
from crack.analysis.analysis_fcts import ANALYZE_FCTS
from crack.models.models_fcts     import INIT_FCTS, OUTPUT_FCTS
from crack.operators.coarsen      import COARSEN_FCTS
from crack.operators.prolong      import PROLONG_FCTS
from crack.utils.fork             import FORK_FCTS
from crack.utils.structures       import merge_dicts
from crack.utils.evaluate         import eval_expr
from crack.utils.errors           import crack_error
from crack.utils.algo_utils       import init_algos_stats


NORMAL_FCTS = merge_dicts(ALGOS, ANALYZE_FCTS, INIT_FCTS, OUTPUT_FCTS)

def format_args(args, com_args):
    if "with" in args:
        for com_k, com_v in com_args[args["with"]].items():
            args.setdefault(com_k, com_v)
        del args["with"]
    for k, v in args.items():
        if isinstance(v, dict):
            format_args(v, com_args)


def get_next_phase(l_models, records, tasks, phase_index, next_phase):
    """Analyse the fork conditions and return the next Phase.
    """
    i = 0
    phase_id = None
    if isinstance(next_phase, dict):
        phase = next_phase["phase"]
        while phase_id is None and "alt_{}".format(i) in next_phase:
            endi  = next_phase["alt_{}".format(i)]
            conds = {}
            for j, cond in enumerate(endi["conds"]):
                conds[j] = FORK_FCTS[cond["algo"]](
                    l_models, records, phase, **cond["args"]
                )
            if len(conds) == 1:
                if conds[0]:
                    phase_id = endi["phase"]
                    break
            else:
                if "expr" not in endi:
                    crack_error(ValueError, "get_next_phase",
                        "Specify the 'expr' to chose the phase after {}.".format(phase)
                    )
                if eval_expr(endi["expr"], conds, only_keywords=True):
                    phase_id = endi["phase"]
                    break
            i += 1
        if phase_id is None:
            phase_id = next_phase["next"]
    else:
        phase_id = next_phase
    # Get the corresponding phase in the task list
    return phases_index[phase_id]


def is_end_phase(l_models, phase):
    return False


def format_task(task, phases, phases_index, com_args, i):
    """Get algorithm id, args and next phase.
    """
    if isinstance(task, str):
        if task in phases:
            algo = phases[task]["algo"]
            args = phases[task].get("args", {})
            format_args(args, com_args)
            next_phase = phases[task].get("next")
            phases_index[task] = i
        else:
            algo = task
            args = {}
            next_phase = None
            phases_index[algo] = i
    elif isinstance(task, dict):
        if "phase" in task:
            phase_id = task["phase"]
            if "algo" in task:
                algo = task["algo"]
            else:
                algo = phases[phase_id]["algo"]
            args = task.get("args", {})
            format_args(args, com_args)
            args = merge_dicts(
                phases[phase_id].setdefault("args", {}),
                args
            )
            next_phase = task
            phases_index[phase_id] = i
        else: # task is of type {algo_name: {**args}}
            algo = list(task)[0] # (should only be one key: the algo name)
            args = task[algo]
            format_args(args, com_args)
            next_phase = None
            phases_index[algo] = i
    phase = {
        "algo": algo,
        "args": args,
        "next": next_phase,
    }
    return phase


def read_repeat_stop_cond(l_models, records, conds, expr=None):
    conds_index_to_bool = {}
    if expr is None:
        def stop_cond(l_models, phase):
            return FORK_FCTS[cond["algo"]](
                l_models, records, phase, **cond["args"]
            )
    else:
        def stop_cond(l_models, phase):
            for j, cond in enumerate(conds):
                conds_index_to_bool[j] = FORK_FCTS[cond["algo"]](
                    l_models, records, phase, **cond["args"]
                )
            return eval_expr(expr, conds_index_to_bool, only_keywords=True)
    return stop_cond


def crack_part(
    l_models, l_aggr, records, tasks, phases_index,
    stop_cond=is_end_phase, i=0, msg="",
):
    """Recursive function
    """
    global NORMAL_FCTS
    nbr_tasks = len(tasks)
    random_seed = 1

    while( i >= 0 and i < nbr_tasks and
        not stop_cond(l_models, tasks[i])
    ):
        phase = tasks[i]
        # Get the algo #
        algo = phase["algo"]
        args = phase["args"]
        next_phase = phase["next"]
        # Apply the right algo #
        f_start = time()
        models = l_models[-1]
        if algo == "repeat":
            nbr_tests = args["nbr_tests"]
            stop_cond = read_repeat_stop_cond(
                l_models, records, args["conds"], args.get("expr"))
            tests = []
            models_ori = copy_models(models)
            # Perform several tries
            for repeat_i in range(nbr_tests):
                msg_i = msg + "{} ".format(repeat_i)
                tests.append(
                    crack_part(
                        l_models, l_aggr, records,
                        tasks, phases_index,
                        stop_cond,
                        i, msg_i,
                    )
                )
            # Select the best one
            select = args["select"]
        elif algo == "set_random_seed":
            value = args.get("value", 1)
            if value == "random":
                value = rd.randint(0, 1000000)
            elif value == "increasing":
                value = random_seed
                random_seed += 1
            print("  |   Random seed: {}".format(value))
            rd.seed(a=value)
        elif algo in NORMAL_FCTS:
            NORMAL_FCTS[algo](models, records, **args)
        elif algo in COARSEN_FCTS:
            models = COARSEN_FCTS[algo](l_models, l_aggr, records, **args)
        elif algo in PROLONG_FCTS:
            models = PROLONG_FCTS[algo](l_models, l_aggr, records, **args)
        elif algo == "pass":
            pass
        else:
            crack_error(ValueError, "crack_part",
                "Unknown algorithm (got {}).".format(algo)
            )
        print("'-|-, {}{:16} (took {:.3f}s)".format(msg, algo, time() - f_start))
        # Get the next phase
        if next_phase is None:
            i += 1
        else:
            i = get_next_phase(l_models, records, tasks, phases_index, next_phase)


def crack_init(spec_files):
    com_args = {}
    phases   = {}
    tasks    = []
    for spec_file in spec_files:
        with open(spec_file, "r") as f:
            specs = yaml.load(f)
        if "with" in specs:
            com_args = merge_dicts(com_args, specs["with"])
        if "phases" in specs:
            phases   = merge_dicts(phases, specs["phases"])
            format_args(phases, com_args)
        if "do" in specs:
            tasks.extend(specs["do"])
    phases_index = {}
    for i, task in enumerate(tasks):
        tasks[i] = format_task(task, phases, phases_index, com_args, i)
    phases_index["end"] = -1
    return tasks, phases_index


if __name__ == "__main__":

    spec_files = sys.argv[1:]
    tasks, phases_index = crack_init(spec_files)
    l_models = [{}]
    l_aggr   = []
    records  = init_algos_stats()
    print("'-|-, Crack")
    start = time()
    crack_part(l_models, l_aggr, records, tasks, phases_index)
    print("'-|-, Cracked (took {:.3f}s)".format(time() - start))


