import time

from common import Params
from se_automation import WindowController, VirtualCamera, SatelliteController



#WindowController.simple_setup()
#earth_cam = VirtualCamera("earth_cam", 45, 0)
#earth_cam.set_position(0.1, 0, -89.99) # 51.5 89.99 0.0
SatelliteController.spawn_satellite(
    0.01, 8000, 0.02, 51, 0
)