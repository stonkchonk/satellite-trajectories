from copy import copy

from procedures import CameraCalibration
from common import Params, Code
from earth import UniversalTimeStamp
from se_automation import WindowController, VirtualCamera, SatelliteController
from earth import EarthCenteredInertial as eci
import numpy as np

from star_tracker.catalog_parser import UnitVector

#WindowController.initial_setup(cleanse_old_screenshots=True)
#calibrator = CameraCalibration(execute_camera_setup=True)
#test_time_stamp = UniversalTimeStamp(2026, 6, 19, 15, 29, 11)
#test_lat_lon = (47, 9)
#test_altitude = 1330
#calibrator.full_camera_calibration_procedure(override_time_stamp=test_time_stamp, override_lat_lon=test_lat_lon, override_sea_altitude=test_altitude)

ts1 = UniversalTimeStamp(2026, 6, 20, 14, 4, 55)
ts2 = UniversalTimeStamp(2026, 6, 20, 14, 3, 115, restrain=False)
ts3 = copy(ts2)
ts3.hour += 1
print(ts1 == ts2)
print(ts1)
print(ts2)
print(ts3)
drift = eci.determine_angular_drift(ts1, ts3)
print(drift)

w = 0.5

matrix = np.array([[np.cos(w), -np.sin(w), 0], [np.sin(w), np.cos(w), 0], [0, 0, 1]])
test_arr = np.array([1,0,0])
test_unit = UnitVector(test_arr)
rotated = np.matmul(matrix, test_arr)
print(rotated)



