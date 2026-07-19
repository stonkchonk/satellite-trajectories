from copy import copy

from algorithms import ParametricTrajectory, GaussAlgorithm
from procedures import CameraCalibration, SingleFrameMeasurementSeries, DualFrameMeasurementSeries
from common import Params, Code
from earth import UniversalTimeStamp
from se_automation import WindowController, VirtualCamera, SatelliteController
from earth import EarthCenteredInertial as eci
import numpy as np

from star_tracker.catalog_parser import UnitVector

WindowController.initial_setup(cleanse_old_screenshots=True)
calibrator = CameraCalibration(execute_camera_setup=True)
forward_time_steps = [0, 25, 25]
test_time_stamp = UniversalTimeStamp(2026, 6, 19, 15, 29, 11)
position_1 = (-28.17593333, 139.69282500)#(47, 9)
altitude_1 = 26
calibrator.full_camera_calibration_procedure(override_time_stamp=test_time_stamp, override_lat_lon=position_1, override_sea_altitude=altitude_1)

series_1 = SingleFrameMeasurementSeries(calibrator)
series_1.create_measurement_series(forward_time_steps)


position_2 = (-24.84611111, 148.64916667)
altitude_2 = 277
calibrator.full_camera_calibration_procedure(override_time_stamp=test_time_stamp, override_lat_lon=position_2, override_sea_altitude=altitude_2, setup_calibration_camera=True)

series_2 = SingleFrameMeasurementSeries(calibrator)
series_2.create_measurement_series(forward_time_steps)

print(series_1)
print(series_2)
exit(22)
print("determining orbit's parameters")
dual_frame_series = DualFrameMeasurementSeries.create_from_two_single_series(series_1, series_2)
measured_eci_vectors = dual_frame_series.intersection_vectors

trajectory = ParametricTrajectory.from_eci_measurements(measured_eci_vectors)
print(f"arg peri: {trajectory.argument_of_periapsis}, sma: {trajectory.semi_major_axis}, ecc: {trajectory.eccentricity}")


"""
sfm = series_1.single_frame_measurements
t = []
R = []
pd = []
for i in [0, 1, 2]:
    print(sfm[i].time_stamp)
    t.append(copy(sfm[i].time_stamp).determine_ut_s())
    R.append(sfm[i].position_vector)
    pd.append(sfm[i].view_vector.value)

gauss_algo = GaussAlgorithm(t[0], t[1], t[2], R[0], R[1], R[2], pd[0], pd[1], pd[2])
gauss_algo.gauss_algorithm_select_solution()
"""



