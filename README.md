### SCV.py:
modifies SCV based on the angle in a turn of the outer wall.
To adjust the SCV values, modify the dictionary `scv_by_angle` and adjust the ranges in `quantize_angle`.

### near_top_wall_accel.py
slows down wall accel near top surfaces:

you need to pass it a config file like this:

[Acceleration]
near_top_surface_accel = 500
default_accel = 3000
layers_below_top = 2

