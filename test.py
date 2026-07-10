import cv2
import numpy as np

from se_automation import VirtualCamera, WindowController, DefaultScripts
from star_tracker.attitude_determiner import AttitudeDeterminer
from common import Code
from star_tracker.catalog_parser import UnitVector

#WindowController.simple_setup()

#test_cam = VirtualCamera("test cam", field_of_view=17.0, exposure_comp=1.5, star_magnitude_limit=4.6)
#test_cam.setup()
#WindowController.run_script(DefaultScripts.prepare_calibration_script)
#atdt = AttitudeDeterminer(test_cam.field_of_view)
#atdt.view_attitude_determination_procedure(test_cam)

#img = cv2.imread("./debug/debug_triangulated_img.png")
#cv2.imshow("view vector", img)
#cv2.waitKey(0)
vectors = [UnitVector.from_array([-0.06764052986002245, 0.1884931773206721, -0.9797423543074031]),
           UnitVector.from_array([-0.20666946, 0.14390246, -0.96777054]),
           UnitVector.from_array([0.07138309, 0.22829231, -0.97097223])]
w1 = Code.rad_to_deg(Code.angular_separation_of_two_vector_rad(vectors[0].value, vectors[1].value))
w2 = Code.rad_to_deg(Code.angular_separation_of_two_vector_rad(vectors[0].value, vectors[2].value))
w3 = Code.rad_to_deg(Code.angular_separation_of_two_vector_rad(vectors[1].value, vectors[2].value))
print(w1, w2, w3)
a = [1,2,3,4,5]
print(a[1:-1])
