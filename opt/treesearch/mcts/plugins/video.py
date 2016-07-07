from utils.video import assemble_video
from opt.solver import Plugin, signals


class VideoRecorder(Plugin):
    signal_map = {signals.ITERATION_FINISHED: "check",
                  signals.SOLVER_FINISHED: "assemble"}
    iters_between_frames = []

    def __init__(self):
        Plugin.__init__(self)
        # self.

    def make_video(self, iterations_between_frames=([1] * 100),
                   frame_no=1, frame_time=0.25,
                   output_fps=None, output_file="mcts"):
        frame_pattern = output_file + "_frame%05d.png"
        self.record_frames(iterations_between_frames=iterations_between_frames,
                           frame_pattern=frame_pattern,
                           frame_no=frame_no)
        assemble_video(frame_pattern=frame_pattern,
                       frame_no=frame_no,
                       frame_time=frame_time,
                       output_fps=output_fps,
                       output_file=output_file)

    def record_frames(self, iterations_between_frames=([1] * 100),
                      frame_pattern="frame%05d.png", frame_no=1):
        from matplotlib import pyplot
        figure = pyplot.figure(1, figsize=(10, 10), dpi=100, frameon=False)
        axes = pyplot.subplot(1, 1, 1)
        info = pyplot.Text(x=0.02, y=0.86)
        for iterations in iterations_between_frames:
            axes.clear()
            axes.add_artist(info)
            self.run(iterations=iterations)
            path = self.selected_path
            path = [path[0]] + [m for m in path[1:] if m.parent is not None]
            self.root.draw(highlight_paths=[path], axes=axes, show=False)
            tree_size, tree_height = self.root.dimensions
            info.set_text("Iterations: %d\nNodes: %d\nHeight: %d\nz*: %.03f\nw*: %.03f" %
                          (self.iterations.total, tree_size, tree_height,
                           self.upper_bound, self.worst_value))
            figure.savefig(frame_pattern % frame_no)
            frame_no += 1
            # if self.state == TreeSearch.STATE.FINISHED:
            #     break
