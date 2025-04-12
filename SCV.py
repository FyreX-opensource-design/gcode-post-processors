#!/usr/bin/env python3
import math
import re
import sys
import tempfile
import os

# Square Corner Velocity settings by angle
scv_by_angle = {
    45: 10,
    90: 100,
    135: 200,
    180: 10
}
default_scv = 10

def angle_between(v1, v2):
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return 0
    cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
    angle_rad = math.acos(cos_angle)
    return round(math.degrees(angle_rad))

def quantize_angle(angle):
    if angle <= 67:
        return 45
    elif angle <= 112:
        return 90
    elif angle <= 157:
        return 135
    else:
        return 180

def is_move(line):
    return line.startswith('G1') and ('X' in line or 'Y' in line)

def extract_xy(line):
    x_match = re.search(r'X(-?\d+\.?\d*)', line)
    y_match = re.search(r'Y(-?\d+\.?\d*)', line)
    if x_match and y_match:
        return float(x_match.group(1)), float(y_match.group(1))
    return None

def process_gcode(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    output = []
    in_outer_wall = False
    last_xy = None
    vec1 = None
    current_scv = default_scv

    for line in lines:
        line = line.rstrip()

        if ";TYPE:Outer wall" in line:
            in_outer_wall = True
            output.append(line)
            continue

        if line.startswith(";TYPE:") and ";TYPE:Outer wall" not in line:
            if in_outer_wall and current_scv != default_scv:
                output.append(f"SET_VELOCITY_LIMIT square_corner_velocity={default_scv} ; reset SCV")
                current_scv = default_scv
            in_outer_wall = False
            vec1 = None
            last_xy = None
            output.append(line)
            continue

        if in_outer_wall and is_move(line):
            curr_xy = extract_xy(line)
            if curr_xy:
                if last_xy:
                    vec2 = (curr_xy[0] - last_xy[0], curr_xy[1] - last_xy[1])
                    if vec1:
                        angle = angle_between(vec1, vec2)
                        snapped_angle = quantize_angle(angle)
                        target_scv = scv_by_angle[snapped_angle]
                        if target_scv != current_scv:
                            output.append(
                                f"SET_VELOCITY_LIMIT square_corner_velocity={target_scv} ; ~{snapped_angle}° corner"
                            )
                            current_scv = target_scv
                    vec1 = vec2
                last_xy = curr_xy

        output.append(line)

    if current_scv != default_scv:
        output.append(f"SET_VELOCITY_LIMIT square_corner_velocity={default_scv} ; final reset")

    # Write to a temp file then replace the original
    with tempfile.NamedTemporaryFile('w', delete=False) as temp:
        temp.write("\n".join(output) + "\n")
        temp_path = temp.name

    os.replace(temp_path, filepath)

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 script.py <input_file.gcode>")
    input_file = sys.argv[1]
    process_gcode(input_file)

if __name__ == '__main__':
    main()
