from __future__ import absolute_import
from math import ceil
import os


def assemble_video(frame_pattern, frame_no=1, frame_time=0.25,
                   output_fps=None, output_file="out.mp4"):
    """Create a video as a slideshow of the images given by 'frame_pattern'. 'frame_pattern' should
    contain a printf-like number format specifier (e.g. %03d) which tells ffmpeg the sequence of
    the frames. This sequence may start at a number other than 1 by passing a 'frame_no' argument.
    'frame_time' specifies how much time each frame should appear in the video.
    'output_fps' specifies the framerate of the created video, and 'output_file' specifies the name
    of the file to be created/overwritten.
    NOTE: the video is created in mp4 format."""
    if not output_file.endswith(".mp4"):
        output_file += ".mp4"
    if output_fps is None:
        output_fps = int(ceil(2.0 / frame_time))
    os.system("ffmpeg -r %s -start_number %d -i %s -c:v libx264 -r %s -pix_fmt yuv444p -y %s"
              % (1.0 / frame_time, frame_no, frame_pattern, output_fps, output_file))
