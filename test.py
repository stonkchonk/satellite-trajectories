import cv2

from se_automation import VirtualCamera, WindowController, DefaultScripts
from star_tracker.attitude_determiner import AttitudeDeterminer


WindowController.simple_setup()

test_cam = VirtualCamera("test cam", field_of_view=17.0, exposure_comp=1.5, star_magnitude_limit=4.6)
test_cam.setup()
WindowController.run_script(DefaultScripts.prepare_calibration_script)
atdt = AttitudeDeterminer(test_cam.field_of_view)
atdt.view_attitude_determination_procedure(test_cam)

img = cv2.imread("./debug/debug_triangulated_img.png")
cv2.imshow("view vector", img)
cv2.waitKey(0)