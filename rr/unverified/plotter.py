from __future__ import absolute_import

from matplotlib.pyplot import figure as Figure, close as close_figure
from contextlib import contextmanager
from math import sqrt, ceil

from utils.namespace import Namespace


class Plotter(object):
    """This class is responsible for managing the layout of a figure, and also implementing
    the plotting commands for simple graphs, hopefully making it even easier than using
    matplotlib directly."""
    ACTIVE_AXES = "active axes"  # A constant used as default target of the plotting methods
    default_hspace = 1.0 / 8.0
    default_vspace = 1.0 / 8.0
    default_hpadding = 0.05
    default_vpadding = 0.05

    def __init__(self, title=None, rows=0, cols=0,
                 hspace=None, vspace=None,
                 hpadding=None, vpadding=None):
        if hspace is None:
            hspace = self.default_hspace
        if vspace is None:
            vspace = self.default_vspace
        if hpadding is None:
            hpadding = self.default_hpadding
        if vpadding is None:
            vpadding = self.default_vpadding
        self.figure = Figure()
        self.figure.plotter = self
        self.title = self.figure.suptitle("" if title is None else title)
        self.rows = rows
        self.cols = cols
        self.hspace = hspace
        self.vspace = vspace
        self.hpadding = hpadding
        self.vpadding = vpadding
        self.active_axes = None

    def update(self):
        """Show changes in the figure."""
        self.figure.show()

    def save(self, *args, **kwargs):
        """Save the figure. Please refer to matplotlib's documentation."""
        self.figure.savefig(*args, **kwargs)

    def close(self):
        close_figure(self.figure)

    def layout(self, rows=None, cols=None, update=True):
        """Change the layout of the figure, i.e. the number of rows and columns."""
        n = len(self.figure.axes)
        if rows is None and cols is None:
            rows = int(round(sqrt(n)))
            cols = rows + (1 if n > rows**2 else 0)
        elif rows is None:
            rows = int(ceil(float(n) / cols))
        elif cols is None:
            cols = int(ceil(float(n) / rows))
        elif rows * cols < n:
            raise ValueError("insufficient cells")
        self.rows = rows
        self.cols = cols
        self.redraw(update)

    def spacing(self, hspace=None, vspace=None, update=True):
        """Change the spacing between axes in the figure."""
        if hspace is None and vspace is None:
            return
        if hspace is not None:
            if not 0.0 <= hspace <= 1.0:
                raise ValueError("illegal horizontal spacing (must be in [0, 1])")
            self.hspace = hspace
        if vspace is not None:
            if not 0.0 <= vspace <= 1.0:
                raise ValueError("illegal vertical spacing (must be in [0, 1])")
            self.vspace = vspace
        self.redraw(update)

    def padding(self, hpadding=None, vpadding=None, update=True):
        if hpadding is None and vpadding is None:
            return
        if hpadding is not None:
            if not 0.0 <= hpadding < 0.5:
                raise ValueError("illegal horizontal spacing (must be in [0, 0.5))")
            self.hpadding = hpadding
        if vpadding is not None:
            if not 0.0 <= vpadding < 0.5:
                raise ValueError("illegal vertical spacing (must be in [0, 0.5))")
            self.vpadding = vpadding
        self.redraw(update)

    def redraw(self, update=True):
        """Redraw the axes in the figure. This is usually used only after changes to layout
        or spacing in the figure."""
        total_width = self.cols * (1.0 + 2.0*self.hspace)
        total_height = self.rows * (1.0 + 2.0*self.vspace)
        plot_width = (1.0 - 2.0*self.hpadding) / total_width
        plot_height = (1.0 - 2.0*self.vpadding) / total_height
        space_width = self.hspace * plot_width
        space_height = self.vspace * plot_height
        # Reposition the axes according to the new dimensions
        n = len(self.figure.axes)
        index = 0
        y_pos = 1.0 - plot_height - space_height - self.vpadding
        for _ in xrange(self.rows):
            x_pos = space_width + self.hpadding
            for x in xrange(self.cols):
                axes = self.figure.axes[index]
                axes.set_position([x_pos, y_pos, plot_width, plot_height])
                index += 1
                x_pos += plot_width + 2 * space_width
                if index == n:
                    break
            y_pos -= plot_height + 2 * space_height
            if index == n:
                break
        if update:
            self.update()

    def set_title(self, title, update=True):
        """Set the title of the figure (not axes!)."""
        self.title.set_text("" if title is None else title)
        if update: self.update()

    def set_size(self, width, height, inches=False):
        """Sets the size of the image in pixels or inches (if 'inches' is true)."""
        dpi = self.figure.get_dpi()
        if not inches:
            width  /= dpi
            height /= dpi
        self.figure.set_size_inches(width, height, forward=True)

    def add_axes(self, make_active=True):
        """Add a new axes to the figure and place it in the right position. If the current
        grid of graphs cannot accommodate the new axes, the figure layout is recalculated."""
        axes = self.figure.add_subplot(1, 1, 1, label=str(len(self.figure.axes)))
        if make_active:
            self.active_axes = axes
        rows, cols = None, None
        if self.rows * self.cols >= len(self.figure.axes):
            rows, cols = self.rows, self.cols
        self.layout(rows, cols, update=False)
        return axes

    def config_axes(self, axes=ACTIVE_AXES, title=None, xlabel=None, ylabel=None,
                    xlimit=None, ylimit=None, legend=None, grid=None, update=True):
        """A many-in-one configuration method. Saves a few boring lines of matplotlib code."""
        axes = self.get_axes(axes)
        if title  is not None: axes.set_title(title)
        if xlabel is not None: axes.set_xlabel(xlabel)
        if ylabel is not None: axes.set_ylabel(ylabel)
        if xlimit is not None: axes.set_xlim(xlimit)
        if ylimit is not None: axes.set_ylim(ylimit)
        if legend is not None: axes.legend(loc=legend)
        if grid   is not None: axes.grid(bool(grid))
        if update:
            self.update()

    def get_axes(self, axes=ACTIVE_AXES):
        """This method can be used to check if a given axes belongs to the figure, retrieve
        the currently active axes, or add new axes to the figure."""
        if axes is Plotter.ACTIVE_AXES:
            if self.active_axes is None:
                self.add_axes(make_active=True)
            return self.active_axes
        if axes is None:
            return self.add_axes(make_active=False)
        if axes in self.figure.axes:
            return axes
        raise Exception("axes does not belong to this Plotter")

    def set_active(self, axes):
        """Set the plotter's active axes, i.e. the default target of plotting commands."""
        if axes not in self.figure.axes:
            raise Exception("axes does not belong to this Plotter")
        self.active_axes = axes

    # -------------------------------------------------
    # Plotting methods
    @contextmanager
    def plotting_on(self, axes, update=True):
        yield self.get_axes(axes)
        if update:
            self.update()

    def legend(self, axes=ACTIVE_AXES, update=True, **kwargs):
        """Add a legend to the given axes."""
        with self.plotting_on(axes, update) as axes:
            axes.legend(**kwargs)
        return axes

    def pie_chart(self, values, freqs, axes=ACTIVE_AXES, update=True, **kwargs):
        with self.plotting_on(axes, update) as axes:
            axes.pie(freqs, labels=values, **kwargs)
        return axes

    def bar_chart(self, values, freqs, axes=ACTIVE_AXES, update=True, **kwargs):
        with self.plotting_on(axes, update) as axes:
            data = self.__prepare_bar_chart(values, freqs)
            axes.xaxis.set_ticks(data.xtick_locs)
            axes.xaxis.set_ticklabels(data.xtick_labels)
            axes.bar(data.left, data.height, width=data.bar_width, **kwargs)
        return axes

    def pareto_chart(self, values, freqs, axes=ACTIVE_AXES, update=True, **kwargs):
        with self.plotting_on(axes, update) as axes:
            data = self.__prepare_pareto_chart(values, freqs)
            axes.xaxis.set_ticks(data.xtick_locs)
            axes.xaxis.set_ticklabels(data.xtick_labels)
            axes.bar(data.left, data.height, width=data.bar_width, **kwargs)
            axes.plot(data.xs, data.ys, "r-", label="Cumulative frequency")
        return axes

    def histogram(self, values, freqs=None, bins=10, axes=ACTIVE_AXES, update=True, **kwargs):
        with self.plotting_on(axes, update) as axes:
            data = self.__prepare_histogram(values, freqs, bins)
            axes.bar(data.left, data.height, width=data.bar_width, **kwargs)
        return axes

    def box_plot(self, values, axes=ACTIVE_AXES, update=True, **kwargs):
        with self.plotting_on(axes, update) as axes:
            axes.boxplot(values, **kwargs)
        return axes

    def run_chart(self, times, values, numeric=True, axes=ACTIVE_AXES, update=True, **kwargs):
        """A run chart of a time series."""
        with self.plotting_on(axes, update) as axes:
            data = self.__prepare_run_chart(list(times), list(values), numeric)
            if not numeric:
                axes.yaxis.set_ticks(data.ytick_locs)
                axes.yaxis.set_ticklabels(data.ytick_labels)
            axes.plot(data.xs, data.ys, **kwargs)
        return axes

    def line_plot(self, xs, ys, axes=ACTIVE_AXES, update=True, **kwargs):
        """A simple 2D line plot."""
        with self.plotting_on(axes, update) as axes:
            axes.plot(list(xs), list(ys), **kwargs)
        return axes

    def function_plot(self, function, start=0, stop=1.0, observations=100,
                      axes=ACTIVE_AXES, update=True, **kwargs):
        """Make a quick plot of a function on a given interval."""
        xs, ys = [], []
        dx = float(stop - start) / (observations - 1)
        x = start
        for i in xrange(observations):
            xs.append(x)
            ys.append(function(x))
            x += dx
        return self.line_plot(xs, ys, axes=axes, update=True, **kwargs)

    # -------------------------------------------------
    # Preparation of data for plotting
    def __prepare_bar_chart(self, values, freqs, bar_width=1.0, bar_space=0.5):
        left = [(bar_width + bar_space) * x for x in xrange(len(freqs))]
        xtick_locs = [l + bar_width / 2.0 for l in left]
        return Namespace(left=left, height=freqs,
                         bar_width=bar_width,
                         xtick_locs=xtick_locs,
                         xtick_labels=values)

    def __prepare_pareto_chart(self, values, freqs, bar_width=1.0):
        total = float(sum(freqs))
        items = sorted([(f / total, v) for f, v in zip(freqs, values)], reverse=True)
        height = []
        left = [bar_width * x for x in xrange(len(items))]
        xtick_locs = [l + bar_width / 2.0 for l in left]
        xtick_labels = []
        xs = [bar_width * x for x in xrange(len(items) + 1)]
        ys = [0.0]
        for f, v in items:
            height.append(f)
            xtick_labels.append(v)
            ys.append(ys[-1] + f)
        return Namespace(left=left, height=height,
                         xs=xs, ys=ys,
                         bar_width=bar_width,
                         xtick_locs=xtick_locs,
                         xtick_labels=xtick_labels)

    def __prepare_histogram(self, values, freqs, bins):
        if freqs is None:
            freqs = [1.0] * len(values)
        items = sorted(zip(values, freqs))
        minimum = items[ 0][0]
        maximum = items[-1][0]
        total_freq = sum(freqs)
        bin_span = float(maximum - minimum) / bins
        bin_end = [minimum + bin_span * (x + 1) for x in xrange(bins)]
        bin_end[-1] = maximum
        bin_freq = [0.0] * bins
        cur_bin = 0
        for v, f in items:
            while v > bin_end[cur_bin]:
                cur_bin += 1
            bin_freq[cur_bin] += f / (bin_span * total_freq)
        return Namespace(left=[end - bin_span for end in bin_end],
                         height=bin_freq,
                         bar_width=bin_span)

    def __prepare_run_chart(self, times, values, numeric):
        xs = []
        ys = []
        prev_y = values[0]
        for y, t in zip(values, times):
            xs.extend((t, t))
            ys.extend((prev_y, y))
            prev_y = y
        ytick_locs = None
        ytick_labels = None
        if not numeric:
            # map objects to integer y values if the tseries is not numeric
            y_set = sorted(set(ys))
            y_mapping = dict(zip(y_set, xrange(len(y_set))))
            ys = [y_mapping[y] for y in ys]
            # prepare y ticks explaining the translation from objects to integers
            yticks = sorted((i, v) for v, i in y_mapping.iteritems())
            ytick_locs   = [i for i, _ in yticks]
            ytick_labels = [v for _, v in yticks]
        return Namespace(xs=xs, ys=ys,
                         ytick_locs=ytick_locs,
                         ytick_labels=ytick_labels)


def get_plot_target(target=None):
    """get_plot_target(target) -> Plotter
    NOTE: a target can be either a Plotter or Axes object."""
    if target is None:
        plotter = Plotter()
        axes = plotter.add_axes()
    elif isinstance(target, Plotter):
        plotter = target
        if plotter.active_axes is None:
            axes = plotter.add_axes()
        else:
            axes = plotter.active_axes
    else:
        plotter = target.figure.plotter
        axes = target
    plotter.set_active(axes)
    return plotter


Plotter.get_plot_target = staticmethod(get_plot_target)
