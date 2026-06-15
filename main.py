import time
import math

import pyautogui
import pyperclip

from calibration import CameraCalibration
from common import Params, Code
from earth import UniversalTimeStamp
from se_automation import WindowController, VirtualCamera, SatelliteController
from earth import EarthCenteredInertial as eci
import numpy as np


WindowController.simple_setup()
calibrator = CameraCalibration(execute_camera_setup=True)
calibrator.position_vector_calibration_procedure()
#calibrator.position_vector_calibration_procedure()#view_vector_calibration_procedure()
#SatelliteController.spawn_satellite(
#    0.01, 8000, 0.02, 51, 0
#)
#ut1 = UniversalTimeStamp(2026, 6, 11, 16, 47, 33)
#ut2 = UniversalTimeStamp(2026, 6, 11, 16, 47, 33)
#ut2.second -= 100
#print(ut1==UniversalTimeStamp.from_string(str(ut2), restrain=False))
#print(ut1==ut2)
#print(ut2)
#print("start")
#pyperclip.copy("test12345 abc")
#pyautogui.hotkey("ctrl", "v")


'''
j0 = eci.determine_j0(2026, 5, 31)
t0 = eci.determine_t0(j0)
theta_g0_deg = eci.determine_theta_g0_deg(t0)

lat_rad = Code.deg_to_rad(51.5)
lon_rad = Code.deg_to_rad(0.1)

vectors = []

for i in range(0, 90):
    vec = eci.determine_eci_vector_from_lat_lon_alt(51.5, 0.1, 0.5, 2026, 6, 4, 20, i*6, 15)
    print(vec, np.linalg.norm(vec))
    vectors.append(vec)

vec_str = "{"
for v in vectors:
    vec_str += f"Vector(({v[0]},{v[1]},{v[2]})), \n"
vec_str = vec_str[:-3]
vec_str += "}"
print(vec_str)
'''

