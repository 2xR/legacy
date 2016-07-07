from collections import namedtuple
import sys


Field = namedtuple("Field", ["header", "width", "align", "extract"])
Field.Incumbent = Field(header="Incumbent",
                        width=24,
                        align=str.rjust,
                        extract=lambda solver: solver.incumbent)
Field.Bound = Field(header="Bound",
                    width=24,
                    align=str.rjust,
                    extract=lambda solver: solver.bound)
Field.Gap = Field(header="Gap",
                  width=12,
                  align=str.rjust,
                  extract=lambda solver: "{:.3g}%".format(solver.gap * 100))
Field.Iters = Field(header="Iters",
                    width=12,
                    align=str.rjust,
                    extract=lambda solver: solver.iters.total)
Field.Cpu = Field(header="Cpu",
                  width=12,
                  align=str.rjust,
                  extract=lambda solver: "{:.4g}s".format(solver.cpu.total))


def field_format(field, value):
    """This auxiliary function uses the data in 'field' to format 'value', namely the alignment
    function and the field's width. If necessary, 'value' is also automatically converted to a
    string using repr()."""
    if not isinstance(value, str):
        value = repr(value)
    if field.align is not None:
        value = field.align(value, field.width)
    return value


class StatusPrinter(object):
    """
    This class is responsible for creating formatted solver status lines using status fields such
    as IterationField, CpuField, IncumbentField, BoundField, etc. in a modular way.  The objective
    of this class is to create a tabular progress report similar to those found in other solvers
    (e.g. SCIP, Gurobi).
    """
    Field = Field
    default_fields = (Field.Incumbent,
                      Field.Bound,
                      Field.Gap,
                      Field.Iters,
                      Field.Cpu)

    def __init__(self, solver, fields=None, separator=" | ",
                 header_interval=50, ostream=sys.stdout):
        if fields is None:
            fields = type(self).default_fields
        self.solver = solver
        self.fields = list(fields)
        self.separator = separator
        self.header_interval = header_interval
        self.lines_displayed = 0
        self.ostream = ostream

    def clear(self):
        self.lines_displayed = 0

    reset = clear

    def write_line(self):
        if self.lines_displayed % self.header_interval == 0:
            self.write_headers()
        self._output(field_format(field, field.extract(self.solver)) for field in self.fields)
        self.lines_displayed += 1

    write = write_line

    def write_headers(self):
        hsep = ["-" * field.width for field in self.fields]
        self._output(hsep)
        self._output(field_format(field, field.header) for field in self.fields)
        self._output(hsep)

    def _output(self, parts):
        line = self.separator.join(parts)
        self.ostream.write(line)
        self.ostream.write("\n")
        self.ostream.flush()
