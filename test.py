import math

import numpy as np

from algorithms import TrueAnomalyAndTime, ParametricTrajectory
from common import Code, Params, Constants
from earth import EarthCenteredInertial
from procedures import SingleFrameMeasurement, SingleFrameMeasurementSeries, DualFrameMeasurementSeries, \
    ObserverPosition
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from star_tracker.catalog_parser import UnitVector
from star_tracker.precession import Precession



series_names = [
    "mt_pi_1_30s",
    "mt_pi_2_30s",
    "lag_neg_1_30s",
    "ch_an_1_30s",
    "ch_an_2_30s",
    "ag_an_1_30s",
    "lag_sal_1_30s",
    "mt_pi_3_30s",
    "mt_pi_1_1s",
]
theta_1 = Code.deg_to_rad(50)
theta_2 = Code.deg_to_rad(70)
theta_3 = Code.deg_to_rad(90)
r_1 = 7067
r_2 = 7087
r_3 = 7107
plane_normal = UnitVector(np.array([0, 0, 1]))

pt = ParametricTrajectory(theta_1, r_1, theta_2, r_2, theta_3, r_3, plane_normal)

pt.semi_major_axis = 7100
pt.eccentricity = 0.3
pt.argument_of_periapsis = Code.deg_to_rad(220)

print(pt.semi_major_axis, pt.eccentricity, Code.rad_to_deg(pt.argument_of_periapsis))
print(pt.period_s)
print(pt._time_from_periapsis_to_origin())

for w in range(36):
    pt.argument_of_periapsis = Code.deg_to_rad(w*10)
    times_since_origin = []
    for i in range(36):
        arr = np.array([i*10, pt.time_since_origin(Code.deg_to_rad(i*10))])
        times_since_origin.append(arr)
    print("\n----", w)
    print(Code.format_to_geogebra_representation_2d(times_since_origin))

print("------------------")
for w in range(36):
    pt.argument_of_periapsis = Code.deg_to_rad(w * 10)
    args_since_origin = []
    for t in [(j/36) * pt.period_s for j in range(36)]:
        arr = np.array([t, Code.rad_to_deg(pt.true_anomaly_since_origin(t))])
        args_since_origin.append(arr)
    print("\n----", w)
    print(Code.format_to_geogebra_representation_2d(args_since_origin))

pt.plane_normal_vector = UnitVector.from_array([0.0, -0.78801075, 0.61566148])
pt.argument_of_periapsis = Code.deg_to_rad(90)
pt.semi_major_axis = 7100
pt.eccentricity = 0.2

eci_positions = []
for true_anomaly in range(72):
    eci_positions.append(pt.eci_position_from_true_anomaly(Code.deg_to_rad(true_anomaly*5)))
print("\n\n\n\n---------")
print(Code.format_to_geogebra_representation_3d(eci_positions))