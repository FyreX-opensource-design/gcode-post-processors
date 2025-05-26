import math
import re
import configparser

CONFIG_FILE = "curve_speed_config.cfg"

def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    curve_cfg = config["CurveBoost"]
    return {
        "HIGH_ACCEL": float(curve_cfg.get("high_accel", 4000)),
        "HIGH_SCV": float(curve_cfg.get("high_scv", 10.0)),
        "ANGLE_THRESHOLD_DEG": float(curve_cfg.get("angle_threshold_deg", 5)),
        "MIN_SEGMENT_LENGTH": float(curve_cfg.get("min_segment_length", 0.5)),
        "MIN_CURVE_LENGTH": int(curve_cfg.get("min_curve_length", 3)),
    }

def parse_position(line, prev_pos):
    coords = dict(prev_pos)
    for axis in "XYZE":
        match = re.search(rf'{axis}(-?\d+\.?\d*)', line, re.IGNORECASE)
        if match:
            coords[axis] = float(match.group(1))
    return coords

def vector(p1, p2):
    return (p2['X'] - p1['X'], p2['Y'] - p1['Y'])

def angle_between(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return 0
    cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))

def process_gcode(lines, cfg):
    output = []
    prev_pos = {'X': 0, 'Y': 0, 'Z': 0, 'E': 0}
    prev_vec = None
    smooth_curve_buffer = []
    in_curve_mode = False
    normal_accel = None
    normal_scv = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("SET_VELOCITY_LIMIT") and 'ACCEL=' in stripped and 'SQUARE_CORNER_VELOCITY=' in stripped:
            if ';' not in stripped:
                accel_match = re.search(r'ACCEL=(\d+\.?\d*)', stripped)
                scv_match = re.search(r'SQUARE_CORNER_VELOCITY=(\d+\.?\d*)', stripped)
                if accel_match and scv_match and normal_accel is None:
                    normal_accel = float(accel_match.group(1))
                    normal_scv = float(scv_match.group(1))

        if stripped.startswith(('G2', 'G3')):
            if not in_curve_mode and normal_accel:
                output.append(f'SET_VELOCITY_LIMIT ACCEL={cfg["HIGH_ACCEL"]} SQUARE_CORNER_VELOCITY={cfg["HIGH_SCV"]} ; post-curve-boost')
                in_curve_mode = True
        elif in_curve_mode and not stripped.startswith(('G1', 'G2', 'G3')):
            if normal_accel:
                output.append(f'SET_VELOCITY_LIMIT ACCEL={normal_accel} SQUARE_CORNER_VELOCITY={normal_scv} ; reset after curve')
                in_curve_mode = False

        if stripped.startswith('G1') and ('X' in stripped or 'Y' in stripped):
            cur_pos = parse_position(stripped, prev_pos)
            vec = vector(prev_pos, cur_pos)
            seg_length = math.hypot(*vec)

            if prev_vec and seg_length > cfg["MIN_SEGMENT_LENGTH"]:
                angle = angle_between(prev_vec, vec)
                if angle < cfg["ANGLE_THRESHOLD_DEG"]:
                    smooth_curve_buffer.append((line, cur_pos))
                else:
                    if len(smooth_curve_buffer) >= cfg["MIN_CURVE_LENGTH"] and normal_accel:
                        if not in_curve_mode:
                            output.append(f'SET_VELOCITY_LIMIT ACCEL={cfg["HIGH_ACCEL"]} SQUARE_CORNER_VELOCITY={cfg["HIGH_SCV"]} ; post-curve-boost')
                            in_curve_mode = True
                    elif in_curve_mode:
                        output.append(f'SET_VELOCITY_LIMIT ACCEL={normal_accel} SQUARE_CORNER_VELOCITY={normal_scv} ; reset after curve')
                        in_curve_mode = False
                    smooth_curve_buffer.clear()
            prev_vec = vec
            prev_pos = cur_pos
        else:
            prev_vec = None

        output.append(line.rstrip())

    if in_curve_mode and normal_accel:
        output.append(f'SET_VELOCITY_LIMIT ACCEL={normal_accel} SQUARE_CORNER_VELOCITY={normal_scv} ; final reset after curve')

    return output

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python speed_up_large_curves.py input.gcode")
        sys.exit(1)

    config = load_config()

    input_path = sys.argv[1]
    with open(input_path, 'r') as f:
        lines = f.readlines()

    processed = process_gcode(lines, config)

    with open(input_path, 'w') as f:
        f.write('\n'.join(processed))

    print(f"✔ Curve speedup post-processing complete: {input_path}")

