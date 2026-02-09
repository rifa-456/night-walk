import math

PI = math.pi
TAU = math.pi * 2
half_PI = math.pi / 2
EPSILON = 0.00001


def deg_to_rad(deg: float) -> float:
    return deg * (PI / 180.0)


def rad_to_deg(rad: float) -> float:
    return rad * (180.0 / PI)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, value: float) -> float:
    if a == b:
        return 0.0
    return (value - a) / (b - a)


def is_equal_approx(a: float, b: float, epsilon: float = EPSILON) -> bool:
    return abs(a - b) < epsilon


def lerp_angle(from_rad: float, to_rad: float, weight: float) -> float:
    """
    Linearly interpolates between two angles (in radians) taking the shortest path.
    """
    diff = (to_rad - from_rad) % TAU
    distance = (2.0 * diff) % TAU - diff
    return from_rad + distance * weight


def move_toward(from_val: float, to_val: float, delta: float) -> float:
    """
    Moves from_val toward to_val by a maximum of delta.
    """
    if abs(to_val - from_val) <= delta:
        return to_val
    return from_val + math.copysign(delta, to_val - from_val)


def smooth_damp(
        current: float,
        target: float,
        current_velocity: float,
        smooth_time: float,
        max_speed: float,
        delta: float
) -> tuple[float, float]:
    """
    Gradually changes a value toward a target with velocity-based smoothing.

    Returns:
        (new_value, new_velocity)
    """
    smooth_time = max(0.0001, smooth_time)
    omega = 2.0 / smooth_time
    x = omega * delta
    exp = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)

    change = current - target
    original_to = target

    max_change = max_speed * smooth_time
    change = clamp(change, -max_change, max_change)
    target = current - change

    temp = (current_velocity + omega * change) * delta
    new_velocity = (current_velocity - omega * temp) * exp
    output = target + (change + temp) * exp

    if (original_to - current > 0.0) == (output > original_to):
        output = original_to
        new_velocity = (output - original_to) / delta

    return output, new_velocity