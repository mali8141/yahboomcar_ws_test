import math

from geometry_msgs.msg import Quaternion

def yaw_to_quaternion(yaw):
    """Create a ROS quaternion for a planar yaw angle (in radians)."""
    return Quaternion(z=math.sin(yaw / 2.0), w=math.cos(yaw / 2.0))


def quaternion_to_yaw(quaternion):
    """Return the planar yaw angle (in radians) of a ROS quaternion."""
    sin_yaw = 2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y)
    cos_yaw = 1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z)
    return math.atan2(sin_yaw, cos_yaw)

