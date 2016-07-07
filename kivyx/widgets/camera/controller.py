from utils.misc import INF
from kivyx.widgets.transform import Transform


def acceleration(dp, dt, v0):
    """Auxiliary function to compute the acceleration necessary to cause the object to move 'dt'
    units in 'dt' time, taking into account the object's current velocity 'v0'."""
    v1 = dp / dt
    dv = v1 - v0
    a = dv / dt
    return a


class CameraController(object):
    """
    Base class for all camera controllers.

    Controllers operate the camera by means of its acceleration attributes *only* (viewport_acc,
    scale_acc, and rotation_acc). Also, controllers must only modify the camera's acceleration
    attributes by adding or subtracting some value, in order to allow multiple controllers to
    operate collaboratively on the same camera. If some controller directly assigns a value to an
    acceleration attribute, the work of any previously executed controllers is undone. Therefore,
    controllers operate only on acceleration attributes by addition and subtraction.
    """
    __slots__ = ()

    def step(self, camera, dt):
        """
        Advance the constraint 'dt' time units on 'camera'.
        """
        raise NotImplementedError()


class ViewportBounds(CameraController):
    def __init__(self, left, bottom, right, top):
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

    def step(self, camera, dt):
        cx, cy = camera.viewport_center
        vx, vy = camera.viewport_vel
        if cx < self.left:
            camera.viewport_acc.x += acceleration(self.left - cx, dt, vx)
        if cx > self.right:
            camera.viewport_acc.x += acceleration(self.right - cx, dt, vx)
        if cy < self.bottom:
            camera.viewport_acc.y += acceleration(self.bottom - cy, dt, vy)
        if cy > self.top:
            camera.viewport_acc.y += acceleration(self.top - cy, dt, vy)


class Follow(CameraController):
    def __init__(self, targets=(), fit_ratio=1.0):
        self.targets = set(targets)
        self.fit_ratio = fit_ratio

    def step(self, camera, dt):
        if len(self.targets) == 0:
            return
        # compute the bounding box of the targets in camera coordinates
        to_camera = camera.transform.to_parent
        left = +INF
        right = -INF
        bottom = +INF
        top = -INF
        for widget in self.targets:
            # find bounding box of this widget
            if isinstance(widget, Transform):
                (l, b), (r, t) = widget.aabb
            else:
                l, b = widget.pos
                w, h = widget.size
                r = l + w
                t = b + h
            # convert to camera coords and update global bounding box
            for x, y in [(l, b), (r, b), (r, t), (l, t)]:
                cam_x, cam_y = to_camera(x, y)
                left = min(left, cam_x)
                right = max(right, cam_x)
                bottom = min(bottom, cam_y)
                top = max(top, cam_y)

        # compute the center of the bounding box and convert it back to transform coordinates
        center_x = (left + right) * 0.5
        center_y = (bottom + top) * 0.5
        center_tx, center_ty = camera.transform.to_local(center_x, center_y)

        # expand the target region by mirroring the "tight"
        # target bbox w.r.t. the camera's center
        cam_center_x, cam_center_y = camera.center
        left = min(left, cam_center_x - (right - cam_center_x))
        right = max(right, cam_center_x + (cam_center_x - left))
        bottom = min(bottom, cam_center_y - (top - cam_center_y))
        top = max(top, cam_center_y + (cam_center_y - bottom))

        # apply acceleration to align the center of the viewport with the center of our bbox
        cx, cy = camera.viewport_center
        vx, vy = camera.viewport_vel
        camera.viewport_acc.x += acceleration(center_tx - cx, dt, vx)
        camera.viewport_acc.y += acceleration(center_ty - cy, dt, vy)

        # compute desired scale and apply scale acceleration to fit the bbox in the camera exactly
        target_width = (right - left) / self.fit_ratio
        target_height = (top - bottom) / self.fit_ratio
        ratio_x = camera.width / target_width
        ratio_y = camera.height / target_height
        tgt_scale = min(ratio_x, ratio_y) * camera.scale
        camera.scale_acc += acceleration(tgt_scale - camera.scale, dt, camera.scale_vel)
