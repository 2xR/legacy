"""
{prog} - run {solver} on <instance> with the given configuration parameters.

Usage:
    {prog} [-p <param>]... <instance>
    {prog} (-i | --interactive)
    {prog} (-h | --help | --help-params)
    {prog} (-v | --version)

Arguments:
    <instance>  path to the instance file being solved

Options:
    -h --help                    show help message
    -v --version                 show program version
    -i, --interactive            start an interactive session
    -p <param>, --param=<param>  specify a solver parameter in the format
                                    'name{param_sep}value'
    --help-params                help about solver parameters
"""
from utils.schema import Or, And, Cut, Use, Optional, Schema, SchemaError
from docopt import docopt
import inspect
import sys
import os
import re
import __main__


PARAM_SEP = ":"
PARAM_RE = re.compile(r"""^\s*
                      (?P<quote>['"]?)
                      (?P<name>\S*)
                      \s*{param_sep}\s*
                      (?P<value>\S*)
                      (?P=quote)
                      \s*$""".format(param_sep=PARAM_SEP),
                      re.VERBOSE)
OPTIONS_SCHEMA = Schema({"<instance>": str,
                         "--param": [And(Use(PARAM_RE.match),
                                         Or(lambda match: match is not None,
                                            Cut("Invalid parameter specification: should"
                                                " be 'name{}value'".format(PARAM_SEP))),
                                         Use(lambda match: match.groupdict()))],
                         Optional(str): object})


def solver_cli(solver, argv=None, prog=None):
    if argv is None:
        argv = sys.argv
    if prog is None:
        prog = os.path.basename(inspect.getfile(__main__))
    solver_name = type(solver).__name__
    doc = __doc__.format(prog=prog, solver=solver_name, param_sep=PARAM_SEP)
    version = "{} version {}".format(solver_name, getattr(solver, "version", "???"))
    options = docopt(doc, argv=argv[1:], help=True, version=version, options_first=False)

    # show parameter help message
    if options["--help-params"]:
        solver.params.help()
        return 0

    # start an interactive session
    if options["--interactive"]:
        solver.repl()
        return 0

    # validate the options
    try:
        options = OPTIONS_SCHEMA.validate(options)
    except SchemaError as error:
        print "{}: {}".format(type(error).__name__, error)
        return 1

    instance = options["<instance>"]
    params = {param["name"]: param["value"] for param in options["--param"]}
    params.setdefault("cpu_limit", 60.0)

    # initialize the solver and run the search
    if solver.state != solver.STATE.UNINITIALIZED:
        solver.reset()

    def display_params(listener):
        solver.log.info("")
        solver.log.info("Initial solver parameters")
        solver.params.report(ostream=solver.log.info)
        solver.log.info("")
        listener.stop()

    solver.channel.listen(solver.SIGNALS.SOLVER_INITIALIZED, display_params,
                          callback_mode=solver.channel.CALLBACK_TAKES_LISTENER)
    solver.solve(instance=instance, **params)
    return 0


if __name__ == "__main__":
    print docopt(__doc__.format(prog=os.path.basename(__file__),
                                solver="solver_cli",
                                param_sep=PARAM_SEP))
