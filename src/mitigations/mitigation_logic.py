# Program Name: mitigation_logic
# Author: Kenneth Sutter
# Date: 4/04/26
# Description: This code defines mitigation functions that protect speed, RPM, and brake signals by rejecting unsafe values and holding 
# the last known good value when an attack or suspicious behavior is detected.

# Speed mitigation
# Checks if the incoming speed value should be trusted
def mitigate_speed(speed, flood_detected, last_good_speed, max_speed):
    # If speed is above the allowed max, hold the last good speed
    if speed > max_speed:
        return last_good_speed

    # If a flood attack is detected, hold the last good speed
    if flood_detected:
        return last_good_speed

    # If speed looks safe, allow the new speed value
    return speed


# RPM mitigation
# Checks if the incoming RPM value should be trusted
def mitigate_rpm(rpm, last_good_rpm, max_rpm_jump, max_rpm):
    # If RPM is above the allowed max, hold the last good RPM
    if rpm > max_rpm:
        return last_good_rpm

    # If there is already a trusted RPM value, check for a large jump
    if last_good_rpm is not None:
        # If RPM changes too quickly, hold the last good RPM
        if abs(rpm - last_good_rpm) > max_rpm_jump:
            return last_good_rpm

    # If RPM looks safe, allow the new RPM value
    return rpm


# Brake mitigation
# Checks if the incoming brake value should be trusted
def mitigate_brake(brake, last_good_brake, time_diff, min_toggle_time=0.3):
    # If there is already a trusted brake value, check for rapid toggling
    if last_good_brake is not None:
        # If brake changes too quickly, hold the last good brake value
        if brake != last_good_brake and time_diff < min_toggle_time:
            return last_good_brake

    # If brake behavior looks safe, allow the new brake value
    return brake