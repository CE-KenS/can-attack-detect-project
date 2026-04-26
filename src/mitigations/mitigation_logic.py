def mitigate_speed(speed, flood_detected, last_good_speed, max_speed):
    if speed > max_speed:
        return last_good_speed

    if flood_detected:
        return last_good_speed

    return speed


def mitigate_rpm(rpm, last_good_rpm, max_rpm_jump, max_rpm):
    if rpm > max_rpm:
        return last_good_rpm

    if last_good_rpm is not None:
        if abs(rpm - last_good_rpm) > max_rpm_jump:
            return last_good_rpm

    return rpm


def mitigate_brake(brake, last_good_brake, time_diff, min_toggle_time=0.1):
    if last_good_brake is not None:
        if brake != last_good_brake and time_diff < min_toggle_time:
            return last_good_brake

    return brake