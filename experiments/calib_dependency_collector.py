from algorithms import SimplifiedGaussAlgorithm, CircularTrajectory, ParametricTrajectory
from common import Code
from earth import UniversalTimeStamp
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from procedures import SingleFrameMeasurementSeriesMultiCalib, ObserverPosition
from star_tracker.catalog_parser import UnitVector

observer_pos = ObserverPosition(
    (-27.911902, -62.468913), 127
)

# Observation times
# start:    "2000.01.01 19:58:00"
# middle:   "2000.01.01 20:03:00"
# end:      "2000.01.01 20:08:00"
# t2        "2000.01.01 20:03:42"
# t3        "2000.01.01 20:04:20"
# t3        "2000.01.01 20:05:41"

# 0: (-27.301281, -63.939256), 157
# 1: (-27.339896, -63.847839), 153
# 2: (-27.378452, -63.756358), 155
# 3: (-27.455384, -63.573205), 149
# 4: (-27.608528, -63.206133), 143
# 5: (-27.911902, -62.468913), 127
# 6: (-28.506740, -60.982091), 64
# 7: (-29.646743, -57.958463), 64
time_stamp = UniversalTimeStamp.from_string("2000.01.01 20:05:41")
sfms_mc = SingleFrameMeasurementSeriesMultiCalib(initial_time_stamp=time_stamp, observer_pos=observer_pos, max_num_of_calibs=100)
sfms_mc.create_measurement_series([0, 7])

sfms_mc.flush_to_file("L5_20-05-41")

#loaded_sfms_mc = SingleFrameMeasurementSeriesMultiCalib.from_json("L5_20-03-00")



"""
for idx, series in sfms_mc.measurement_series.items():
    first = series[0]
    last = series[-1]
    simple_gauss_orbit_model = SimplifiedGaussAlgorithm(first.time_stamp.determine_ut_s(),
                                                        last.time_stamp.determine_ut_s(),
                                                        first.position_vector, last.position_vector,
                                                        first.view_vector.value, last.view_vector.value)
    r_vectors = simple_gauss_orbit_model.determine_solution()
    if r_vectors is not None:
        ct = CircularTrajectory.from_eci_measurements(r_vectors)
        pt = ParametricTrajectory.from_circular_trajectory(ct)
        angle_deg = Code.rad_to_deg(pt.plane_normal_vector.angular_rad_separation(UnitVector(plane_normal_ground_truth)))
        print(pt.semi_major_axis, pt.plane_normal_vector, angle_deg)
    else:
        print("unable to determine solution")
        print("->", first.time_stamp, first.position_vector, first.view_vector.value,
              last.time_stamp, last.position_vector, last.view_vector.value)
print("stopp")
"""

