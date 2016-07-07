from utils.misc import INF
from utils.math import clamp
from math import pi

from kivyx.widgets import Stencil, Transform
from kivyx.lib import Vector, Clock


class Camera(Stencil):
    def __init__(self, transform=None, controllers=(), frequency=60):
        Stencil.__init__(self)
        if transform is None:
            transform = Transform()
        self.add_widget(transform)
        self.transform = transform
        self.controllers = list(controllers)
        self.frequency = frequency

        self.viewport_center = Vector(transform.viewport_center)
        self.viewport_vel = Vector(0.0, 0.0)
        self.viewport_acc = Vector(0.0, 0.0)
        self.viewport_max_vel = INF
        self.viewport_max_acc = INF
        self.scale = transform.scale_x
        self.scale_min = 0.01
        self.scale_max = INF
        self.scale_vel = 0.0
        self.scale_acc = 0.0
        self.scale_max_vel = INF
        self.scale_max_acc = INF
        self.rotation = transform.rotation
        self.rotation_vel = 0.0
        self.rotation_acc = 0.0
        self.rotation_max_vel = INF
        self.rotation_max_acc = INF

    def update_attrs_from_transform(self):
        transform = self.transform
        self.viewport_center = Vector(transform.viewport_center)
        self.scale = transform.scale_x
        self.rotation = transform.rotation

    def start(self):
        Clock.schedule_interval(self.step, 1.0 / self.frequency)

    def stop(self):
        Clock.unschedule(self.step)

    def step(self, dt):
        self.update_attrs_from_transform()
        # reset accelerations
        self.viewport_acc = Vector(0.0, 0.0)
        self.scale_acc = 0.0
        self.rotation_acc = 0.0

        # call all controllers on self
        for controller in self.controllers:
            controller.step(self, dt)

        # update position
        limit_vector_length(self.viewport_acc, self.viewport_max_acc)
        self.viewport_vel += self.viewport_acc * dt
        limit_vector_length(self.viewport_vel, self.viewport_max_vel)
        self.viewport_center += self.viewport_vel * dt

        # update scale
        self.scale_acc = limit_abs(self.scale_acc, self.scale_max_acc)
        self.scale_vel = limit_abs(self.scale_vel + self.scale_acc * dt, self.scale_max_vel)
        self.scale = clamp(self.scale + self.scale_vel * dt, self.scale_min, self.scale_max)

        # update rotation
        self.rotation_acc = limit_abs(self.rotation_acc, self.rotation_max_acc)
        self.rotation_vel = limit_abs(self.rotation_vel + self.rotation_acc * dt,
                                      self.rotation_max_vel)
        self.rotation = (self.rotation + self.rotation_vel * dt) % (2.0 * pi)

        # apply pan, zoom, and rotation
        self.transform.viewport_center = self.viewport_center
        self.transform.scale = self.scale
        self.transform.rotation = self.rotation

        # align the center of the viewport with the center of the camera
        viewport_center_x, viewport_center_y = self.viewport_center
        camera_center_x, camera_center_y = self.center
        self.transform.align_local_to_parent(viewport_center_x, viewport_center_y,
                                             camera_center_x, camera_center_y)


def limit_vector_length(vec, max_length):
    """If the norm of 'vec' exceeds 'max_length', the vector is truncated to respect the specified
    limit.
    NOTE: operates in-place on the vector."""
    vec_length = vec.length()
    if vec_length > max_length:
        vec *= float(max_length) / vec_length
    return vec


def limit_abs(x, lim):
    """Returns the value 'x' clamped to the interval '[-lim, +lim]'."""
    return clamp(x, -lim, +lim)
