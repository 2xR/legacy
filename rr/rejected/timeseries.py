from bisect import bisect_right
from itertools import izip


class TimeSeries(object):
    def __init__(self, initial_time=None, initial_value=None):
        self.times = []
        self.values = []
        if initial_time is not None:
            self.append(initial_time, initial_value)

    @classmethod
    def from_iterable(cls, points):
        tseries = cls()
        tseries.clear()
        tseries.extend(points)
        return tseries

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return izip(self.times, self.values)

    @property
    def time(self):
        """Returns the last time registered in the time series."""
        return self.times[-1]

    @property
    def value(self):
        """Returns the last value registered in the time series."""
        return self.values[-1]

    def value_at(self, time):
        index = bisect_right(self.times, time) - 1
        return self.values[index]

    __getitem__ = value_at

    def __setitem__(self, time, value):
        index = bisect_right(self.times, time)
        self.times.insert(index, time)
        self.values.insert(index, value)

    def append(self, time, value):
        if len(self.times) > 0 and time < self.times[-1]:
            raise ValueError("argument time is smaller than last registered time")
        self.times.append(time)
        self.values.append(value)

    def extend(self, points):
        for time, value in points:
            self.append(time, value)

    def pop(self):
        return self.times.pop(), self.values.pop()

    def clear(self):
        del self.times[:]
        del self.values[:]

    def weighted_mean(self):
        """Compute the weighted mean of the time series."""
        if len(self.times) == 0:
            raise ValueError("unable to compute weighted mean of empty time series")
        times = iter(self.times)
        values = iter(self.values)
        t0 = next(times)
        v = next(values)
        total = 0
        for t1 in times:
            total += (t1 - t0) * v
            t0 = t1
            v = next(values)
        return total / float(self.times[-1] - self.times[0])

    def plot(self, axes=None, xlabel="Time", ylabel="Value", filename=None, dpi=300, **kwargs):
        """Build and display (or save) a plot showing the time series. If 'filename' is None, the
        plot is displayed on the screen, otherwise it is saved to the specified file. The filename
        extension will determine the format of the output file (e.g. pdf, eps, png, jpg)."""
        try:
            from matplotlib.pyplot import figure
        except ImportError:
            from warnings import warn
            warn("matplotlib not found: plotting unavailable")
            return None

        if len(self) == 0:
            raise ValueError("empty time series")
        # create figure and axes if necessary
        if axes is None:
            fig = figure()
            axes = fig.add_subplot(1, 1, 1)
        else:
            fig = axes.figure
        # default arguments to plot()
        kwargs.setdefault("linewidth", 2)
        kwargs.setdefault("marker", "o")
        kwargs.setdefault("color", "blue")
        kwargs.setdefault("markeredgecolor", kwargs["color"])
        kwargs.setdefault("drawstyle", "steps-post")
        # plot and display grid
        axes.plot(self.times, self.values, **kwargs)
        axes.grid(True)
        # set axes labels
        if xlabel is not None:
            axes.set_xlabel(xlabel)
        if ylabel is not None:
            axes.set_ylabel(ylabel)
        # save figure to file or show on screen
        if filename is None:
            fig.show()
        else:
            fig.savefig(filename, dpi=dpi)
        return axes
