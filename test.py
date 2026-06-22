import cv2
import numpy as np

from se_automation import VirtualCamera, WindowController, DefaultScripts
from star_tracker.attitude_determiner import AttitudeDeterminer
from common import Code

WindowController.simple_setup()

test_cam = VirtualCamera("test cam", field_of_view=17.0, exposure_comp=1.5, star_magnitude_limit=4.6)
test_cam.setup()
WindowController.run_script(DefaultScripts.prepare_calibration_script)
atdt = AttitudeDeterminer(test_cam.field_of_view)
atdt.view_attitude_determination_procedure(test_cam)

img = cv2.imread("./debug/debug_triangulated_img.png")
cv2.imshow("view vector", img)
cv2.waitKey(0)
#v1 = np.array([0, 1, 2])
#v2 = np.array([3, 4, 5])
#v3 = np.array([6, 7, 8])
#vectors = [v1, v2, v3]
#Code.triangulate_vector_from_image_point(vectors, 1, 1, 1, 1)