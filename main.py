from copy import copy

from procedures import CameraCalibration, SingleFrameMeasurementSeries
from common import Params, Code
from earth import UniversalTimeStamp
from se_automation import WindowController, VirtualCamera, SatelliteController
from earth import EarthCenteredInertial as eci
import numpy as np

from star_tracker.catalog_parser import UnitVector

WindowController.initial_setup(cleanse_old_screenshots=True)
calibrator = CameraCalibration(execute_camera_setup=True)
test_time_stamp = UniversalTimeStamp(2026, 6, 19, 15, 29, 11)
test_lat_lon = (-28.17593333, 139.69282500)#(47, 9)
test_altitude = 26
calibrator.full_camera_calibration_procedure(override_time_stamp=test_time_stamp, override_lat_lon=test_lat_lon, override_sea_altitude=test_altitude)

dataSetCreator = SingleFrameMeasurementSeries(calibrator)
dataSetCreator.create_measurement_series()




