from copy import copy

import numpy as np

from common import Params, Code
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
        print("View vector calibration completed. Do not move camera.")

    def position_vector_calibration_procedure(self, override_time_stamp: UniversalTimeStamp | None = None,
                                              override_lat_lon: tuple[float, float] | None = None,
                                              override_sea_altitude: float | None = None):
        WindowController.run_script(DefaultScripts.default_visibilities_script)
        if override_time_stamp is None:
            print("Enter universal time in the format YYYY.MM.DD HH:MM:SS below:")
            time_input_str = input()
            WindowController.simple_setup()
            time_input_str = time_input_str.strip()
            self.initial_time_stamp = UniversalTimeStamp.from_string(time_input_str)
        else:
            self.initial_time_stamp = override_time_stamp
        self.calibration_cam.set_time(self.initial_time_stamp)
        print(f"Initial time is {self.initial_time_stamp}")

        if override_lat_lon is None:
            print("Enter latitude and longitude in decimal degrees as LAT LON below:")
            lat_lon_input = input()
            WindowController.simple_setup()
            latitude, longitude = self.parse_lat_lon(lat_lon_input)
        else:
            latitude, longitude = override_lat_lon
        self.calibration_cam.touchdown_at_position(longitude, latitude)
        if override_sea_altitude is None:
            print("Enter sea altitude in [m] as seen in the HUD:")
            sea_altitude = float(input())
            #WindowController.simple_setup()
        else:
            sea_altitude = override_sea_altitude
        self.position_vector = EarthCenteredInertial.determine_eci_vector_from_lat_lon_alt(latitude, longitude,
                                                                                           sea_altitude,
                                                                                           self.initial_time_stamp)
        print(f"Position vector calibration completed. Remain steady.")

    def full_camera_calibration_procedure(self, override_time_stamp: UniversalTimeStamp | None = None,
                                        override_lat_lon: tuple[float, float] | None = None,
                                        override_sea_altitude: float | None = None):
        WindowController.simple_setup()
        print("Starting full camera calibration procedure.")
        self.position_vector_calibration_procedure(override_time_stamp, override_lat_lon, override_sea_altitude)
        print("Press enter to continue with view vector calibration.")
        _ = input()
        WindowController.simple_setup()
        self.view_vector_calibration_procedure()
        print(f"Camera calibration completed. {self.center_view_vector}, {self.position_vector}")


    @staticmethod
    def parse_lat_lon(lat_lon_str: str) -> tuple[float, float]:
        lat_lon_str = lat_lon_str.strip()
        lat_str, lon_str = lat_lon_str.split()
        return float(lat_str), float(lon_str)


class SingleFrameMeasurement:
    def __init__(self, time_stamp: UniversalTimeStamp, view_vector: UnitVector, position_vector: np.ndarray):
        self.time_stamp = time_stamp
        self.view_vector = view_vector
        self.position_vector = position_vector

    @classmethod
    def from_e(cls):
        pass


class SingleFrameMeasurementSeriesCreator:
    def __init__(self, calibration_instance: CameraCalibration | None):
        self.calibration = calibration_instance
        self.single_frame_measurements = []
        self.measurement_cam = VirtualCamera("measurement cam", self.calibration.calibration_cam.field_of_view,
                                             self.calibration.calibration_cam.exposure_comp, self.calibration.calibration_cam.exposure_comp)
        self.star_imager = StarImager(self.calibration.calibration_cam.field_of_view, save_debug_images=True)

    def create_measurement_series(self):
        if self.calibration is None:
            self.calibration = CameraCalibration()
            self.calibration.full_camera_calibration_procedure()
        WindowController.simple_setup()
        self.measurement_cam.setup()
        continue_taking_measurements = True
        current_time_tamp = copy(self.calibration.initial_time_stamp)
        while continue_taking_measurements:
            print("Enter number to move time in seconds ahead, enter letter to end measurement.")
            input_seconds = self.parse_input_seconds()
            if input_seconds is None:
                continue_taking_measurements = False
                break
            else:
                current_time_tamp.second += input_seconds
                self.single_frame_measurements.append(self.create_single_frame_measurement(current_time_tamp))
        for m in self.single_frame_measurements:
            print(m.time_stamp)
            print(m.view_vector)
            print(m.position_vector)
            print("-----")





    def create_single_frame_measurement(self, time_stamp: UniversalTimeStamp) -> SingleFrameMeasurement | None:
        drift_angle_deg = EarthCenteredInertial.determine_angular_drift(self.calibration.initial_time_stamp, time_stamp)
        view_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.center_view_vector.value, drift_angle_deg)
        left_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.left_view_vector.value, drift_angle_deg)
        right_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.right_view_vector.value, drift_angle_deg)
        position_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.position_vector, drift_angle_deg)
        WindowController.simple_setup()
        WindowController.run_script(DefaultScripts.prepare_tracking_script)
        measurement_image = self.measurement_cam.take_screenshot("measurement")
        observed_dots = self.star_imager.all_observable_stars_of_image(measurement_image)
        assert len(observed_dots) <= 1
        if len(observed_dots) == 1:
            triangulated_view_vector = Code.triangulate_vector_from_image_point(
                [view_vector_drifted, left_vector_drifted, right_vector_drifted],
                [Params.center_point, Params.left_edge_point, Params.right_edge_point],
                observed_dots[0].position, Params.width_height[0], Code.deg_to_rad(self.measurement_cam.field_of_view)
            )
            return SingleFrameMeasurement(time_stamp, UnitVector(triangulated_view_vector), position_vector_drifted)
        else:
            return None






    @staticmethod
    def parse_input_seconds() -> int | None:
        try:
            input_seconds = int(input())
            assert input_seconds >= 0
            return input_seconds
        except (ValueError, AssertionError):
            return None




