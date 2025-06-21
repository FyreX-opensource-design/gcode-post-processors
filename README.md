### SCV.py:
modifies SCV based on the angle in a turn of the outer wall.
To adjust the SCV values, modify the dictionary `scv_by_angle` and adjust the ranges in `quantize_angle`.

### near_top_wall_accel.py
slows down wall accel near top surfaces:

you need to pass it a config file like this:
```cfg
[Acceleration]
near_top_surface_accel = 500
default_accel = 3000
layers_below_top = 2
```
### fast_curves.py
speeds up accels and SCV on the curves of prints

you need a config file called curve_speed_config.cfg with this in it:
```cfg
[CurveBoost]
high_accel = 4000
high_scv = 10.0
angle_threshold_deg = 5
min_segment_length = 0.5
min_curve_length = 3
```
