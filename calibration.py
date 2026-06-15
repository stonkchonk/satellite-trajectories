import numpy as np

from common import Params
from earth import UniversalTimeStamp, EarthCenteredInertial
from se_automation import VirtualCamera, WindowController, DefaultScripts
from star_tracker.catalog_parser import UnitVector
from star_tracker.star_imager import StarImager
from star_tracker.star_matching import MultiMatcher
from star_tracker.attitude_determiner import AttitudeDeterminer


class CameraCalibration:
    def __init__(self, execute_camera_setup: bool = True):
        self.calibration_cam = VirtualCamera("calibration cam", field_of_view=17.0, exposure_comp=1.5, star_magnitude_limit=4.6)
        if execute_camera_setup:
            self.calibration_cam.setup()
        self.attitude_determiner = AttitudeDeterminer(self.calibration_cam.field_of_view)
        self.position_vector: np.ndarray | None = None
        self.center_view_vector: UnitVector | None = None
        self.left_view_vector: UnitVector | None = None
        self.right_view_vector: UnitVector | None = None
        self.initial_time_stamp: UniversalTimeStamp | None = None

    def view_vector_calibration_procedure(self):
        WindowController.run_script(DefaultScripts.prepare_calibration_script)
        star_calibration_image = self.calibration_cam.take_screenshot("star_calibration")
        star_imager = StarImager(self.calibration_cam.field_of_view, True)
        observed_viable_quadruples = star_imager.determine_viable_quadruples(star_calibration_image)

        # not enough stars in frame
        if observed_viable_quadruples is None:
            raise Exception("Could not match any stars within this frame.")

        print(f"Number of Quadruples in frame: {len(observed_viable_quadruples)}")
        multi_matcher = MultiMatcher(observed_viable_quadruples)
        matching_result = multi_matcher.determine_match_from_multiple_quadruples()

        # if no match is possible return None
        if matching_result is None:
            raise Exception("Could not match any stars within this frame.")

        # unpack matched stars and observed stars
        matching_quadruple_ids, observed_stars_dict = matching_result
        three_observed_stars = list(observed_stars_dict.values())[:-1]
        three_matched_stars = list(matching_quadruple_ids.values())[:-1]

        self.center_view_vector = self.attitude_determiner.triangulate_view_vector(Params.center_point, three_observed_stars, three_matched_stars)
        self.left_view_vector = self.attitude_determiner.triangulate_view_vector(Params.left_edge_point, three_observed_stars, three_matched_stars)
        self.right_view_vector = self.attitude_determiner.triangulate_view_vector(Params.right_edge_point, three_observed_stars, three_matched_stars)
        self.attitude_determiner.draw_view_vector(self.center_view_vector)

    def position_vector_calibration_procedure(self, override_time_stamp: UniversalTimeStamp | None = None,
                                              override_lat_lon: tuple[float, float] | None = None,
                                              override_sea_altitude: float | None = None):
        print("Enter universal time in the format YYYY.MM.DD HH:MM:SS below:")
        if override_time_stamp is None:
            time_input_str = input()
            WindowController.simple_setup()
            time_input_str = time_input_str.strip()
            self.initial_time_stamp = UniversalTimeStamp.from_string(time_input_str)
        else:
            self.initial_time_stamp = override_time_stamp
        self.calibration_cam.set_time(self.initial_time_stamp)
        print(f"Initial time is {self.initial_time_stamp}")
        print("Enter latitude and longitude in decimal degrees as LAT LON below:")
        lat_lon_input = input()
        WindowController.simple_setup()
        latitude, longitude = self.parse_lat_lon(lat_lon_input)
        self.calibration_cam.touchdown_at_position(longitude, latitude)
        print("Enter sea altitude in [m] as seen in the HUD:")
        sea_altitude = float(input())
        WindowController.simple_setup()
        self.position_vector = EarthCenteredInertial.determine_eci_vector_from_lat_lon_alt(latitude, longitude,
                                                                                           sea_altitude,
                                                                                           self.initial_time_stamp)



    @staticmethod
    def parse_lat_lon(lat_lon_str: str) -> tuple[float, float]:
        lat_lon_str = lat_lon_str.strip()
        lat_str, lon_str = lat_lon_str.split()
        return float(lat_str), float(lon_str)



