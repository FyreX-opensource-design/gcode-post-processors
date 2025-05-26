import re
import configparser
import sys

def load_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    accel_near_top = int(config['Acceleration'].get('near_top_surface_accel', 500))
    default_accel = int(config['Acceleration'].get('default_accel', 3000))
    near_top_layers = int(config['Acceleration'].get('layers_below_top', 2))
    return accel_near_top, default_accel, near_top_layers

def process_gcode(lines, accel_near_top, default_accel, near_top_layers):
    processed = []
    current_layer = -1
    layer_has_top_surface = set()

    # First pass: Find all top surface layers
    for i, line in enumerate(lines):
        if line.startswith(';LAYER:'):
            current_layer = int(line.strip().split(':')[1])
        elif ';TYPE:Top Surface' in line:
            for offset in range(near_top_layers + 1):
                if current_layer - offset >= 0:
                    layer_has_top_surface.add(current_layer - offset)

    # Second pass: Process and inject accel changes
    current_layer = -1
    accel_active = False
    in_wall = False

    for line in lines:
        if line.startswith(';LAYER:'):
            current_layer = int(line.strip().split(':')[1])
            accel_active = False  # Reset at new layer
            in_wall = False

        # Entering a wall type
        if ';TYPE:Wall-' in line:
            if current_layer in layer_has_top_surface and not accel_active:
                processed.append(f'SET_VELOCITY_LIMIT ACCEL={accel_near_top}')
                accel_active = True
            in_wall = True

        # Leaving wall
        elif line.startswith(';TYPE:') and in_wall:
            if accel_active:
                processed.append(f'SET_VELOCITY_LIMIT ACCEL={default_accel}')
                accel_active = False
            in_wall = False

        processed.append(line)

    # Catch unclosed walls
    if accel_active:
        processed.append(f'SET_VELOCITY_LIMIT ACCEL={default_accel}')

    return processed

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python adjust_top_surface_wall_accel.py input.gcode output.gcode config.cfg")
        sys.exit(1)

    input_file, output_file, config_file = sys.argv[1:]

    accel_near_top, default_accel, near_top_layers = load_config(config_file)

    with open(input_file, 'r') as f:
        lines = f.readlines()

    result = process_gcode(lines, accel_near_top, default_accel, near_top_layers)

    with open(output_file, 'w') as f:
        f.writelines(line if line.endswith('\n') else line + '\n' for line in result)

    print(f"Processed {input_file} and wrote to {output_file}")
