from physix.common.settings import NumericSetting, BooleanSetting, OptionSetting, TextSetting


def get_physics_attr(obj, attr):
    return obj.physics[attr]


def set_physics_attr(obj, attr, value):
    obj.physics[attr] = value


IDENTIFIER = TextSetting(name="ID", default=None, attr="id")
SENSOR = BooleanSetting(name="Sensor", default=False, attr="sensor",
                        getter=get_physics_attr, setter=set_physics_attr)
DENSITY = NumericSetting(name="Density", default=1.0, min=0.0, max=1e9, attr="density",
                         getter=get_physics_attr, setter=set_physics_attr)
FRICTION = NumericSetting(name="Friction", default=1.0, min=0.0, max=1.0, attr="friction",
                          getter=get_physics_attr, setter=set_physics_attr)
RESTITUTION = NumericSetting(name="Restitution", default=0.0, min=0.0, max=1.0, attr="restitution",
                             getter=get_physics_attr, setter=set_physics_attr)
LINEAR_DAMPING = NumericSetting(name="Linear Damping", default=0.0, min=0.0, max=1.0,
                                attr="linear_damping",
                                getter=get_physics_attr, setter=set_physics_attr)
ANGULAR_DAMPING = NumericSetting(name="Angular Damping", default=0.0, min=0.0, max=1.0,
                                 attr="angular_damping",
                                 getter=get_physics_attr, setter=set_physics_attr)
GRAVITY_SCALE = NumericSetting(name="Gravity Scale", default=0.0, min=0.0, max=1.0,
                               attr="gravity_scale",
                               getter=get_physics_attr, setter=set_physics_attr)
ALLOW_SLEEP = BooleanSetting(name="Allow Sleep", default=False, attr="allow_sleep",
                             getter=get_physics_attr, setter=set_physics_attr)
AWAKE = BooleanSetting(name="Awake", default=True, attr="awake",
                       getter=get_physics_attr, setter=set_physics_attr)
FIXED_ROTATION = BooleanSetting(name="Fixed Rotation", default=False, attr="fixed_rotation",
                                getter=get_physics_attr, setter=set_physics_attr)
BULLET = BooleanSetting(name="Bullet", default=False, attr="bullet",
                        getter=get_physics_attr, setter=set_physics_attr)
ACTIVE = BooleanSetting(name="Active", default=False, attr="active",
                        getter=get_physics_attr, setter=set_physics_attr)
BODY_TYPE = OptionSetting(name="Body Type", default="Static", attr="body_type",
                          options=["Static", "Dynamic", "Kinematic"],
                          getter=get_physics_attr, setter=set_physics_attr)
DO_SLEEP = BooleanSetting(name="Do Sleep", default=True, attr="do_sleep",
                          getter=get_physics_attr, setter=set_physics_attr)
V_GRAVITY = NumericSetting(name="Vertical Gravity", default=-9.8, attr="v_gravity",
                           getter=get_physics_attr, setter=set_physics_attr)
H_GRAVITY = NumericSetting(name="Horizontal Gravity", default=0.0, attr="h_gravity",
                           getter=get_physics_attr, setter=set_physics_attr)
