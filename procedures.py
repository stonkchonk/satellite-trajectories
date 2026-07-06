import time
from copy import copy

import numpy as np
from fontTools.subset import intersect

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
        self.top_view_vector: UnitVector | None = None
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
        self.top_view_vector = self.attitude_determiner.triangulate_view_vector(Params.top_edge_point, three_observed_stars, three_matched_stars)
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
        print("Point camera towards satellite then press enter.")
        _ = input()
        time.sleep(Params.sleep_quick)
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


class SingleFrameMeasurementSeries:
    def __init__(self, calibration_instance: CameraCalibration | None):
        self.calibration = calibration_instance
        self.single_frame_measurements: list[SingleFrameMeasurement] = []
        self.measurement_cam = VirtualCamera("measurement cam", self.calibration.calibration_cam.field_of_view,
                                             self.calibration.calibration_cam.exposure_comp, self.calibration.calibration_cam.exposure_comp)
        self.star_imager = StarImager(self.calibration.calibration_cam.field_of_view, save_debug_images=True)

    def create_measurement_series(self):
        if self.calibration is None:
            self.calibration = CameraCalibration()
            self.calibration.full_camera_calibration_procedure()
        WindowController.simple_setup()
        WindowController.run_script(DefaultScripts.prepare_tracking_script)
        self.measurement_cam.setup()
        self.measurement_cam.update_star_magnitude_limit(7.0)
        continue_taking_measurements = True
        current_time_tamp = copy(self.calibration.initial_time_stamp)
        while continue_taking_measurements:
            print("Enter number to move time in seconds ahead, enter letter to end measurement.")
            input_seconds = self.parse_input_seconds()
            if input_seconds is None:
                continue_taking_measurements = False
                break
            else:
                WindowController.simple_setup()
                current_time_tamp.second += input_seconds
                self.measurement_cam.set_time(current_time_tamp)
                self.single_frame_measurements.append(self.create_single_frame_measurement(current_time_tamp))
        for m in self.single_frame_measurements:
            print(m.time_stamp)
            print(m.view_vector)
            print(m.position_vector)
            ra_rad, dec_rad = m.view_vector.to_radians
            print(Code.fancy_format_ra_dec((Code.rad_to_deg(ra_rad), Code.rad_to_deg(dec_rad))))
            print("-----")
        vectors = [m.view_vector.value for m in self.single_frame_measurements]
        print(Code.format_to_geogebra_representation(vectors))


    def create_single_frame_measurement(self, time_stamp: UniversalTimeStamp) -> SingleFrameMeasurement | None:
        drift_angle_deg = EarthCenteredInertial.determine_angular_drift(self.calibration.initial_time_stamp, time_stamp)
        view_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.center_view_vector.value, drift_angle_deg)
        left_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.left_view_vector.value, drift_angle_deg)
        top_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.top_view_vector.value, drift_angle_deg)
        position_vector_drifted = EarthCenteredInertial.rotate_eci_vector_around_earth_axis(
            self.calibration.position_vector, drift_angle_deg)
        WindowController.simple_setup()
        measurement_image = self.measurement_cam.take_screenshot("measurement")
        Code.save_debug_image(f"measurement_{len(self.single_frame_measurements)}.png", measurement_image)
        observed_dots = self.star_imager.all_observable_stars_of_image(measurement_image)
        if len(observed_dots) >= 1:
            triangulated_view_vector = Code.triangulate_vector_from_image_point(
                [view_vector_drifted, left_vector_drifted, top_vector_drifted],
                [Params.center_point, Params.left_edge_point, Params.top_edge_point],
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


class DualFrameMeasurementSeries:
    def __init__(self, dual_frame_measurements: list[tuple[SingleFrameMeasurement, SingleFrameMeasurement]]):
        self.dual_frame_measurements = dual_frame_measurements

    @classmethod
    def create_from_two_single_series(cls, first_series: SingleFrameMeasurementSeries, second_series: SingleFrameMeasurementSeries):
        assert len(first_series.single_frame_measurements) == len(second_series.single_frame_measurements)
        dual_frame_measurements = []
        for idx, single_frame_measurement in enumerate(first_series.single_frame_measurements):
            assert single_frame_measurement is not None
            assert second_series.single_frame_measurements[idx] is not None
            dual_frame_measurements.append(
                (copy(single_frame_measurement), copy(second_series.single_frame_measurements[idx]))
            )
        return DualFrameMeasurementSeries(dual_frame_measurements)

    @property
    def intersection_vectors(self) -> list[np.ndarray]:
        intersection_vectors = []
        for dual_frame_measurement in self.dual_frame_measurements:
            first, second = dual_frame_measurement
            p1 = first.position_vector
            v1 = first.view_vector.value
            p2 = second.position_vector
            v2 = second.view_vector.value
            intersection_vectors.append(self.intersection_center_point(p1, v1, p2, v2))
        return intersection_vectors

    @staticmethod
    def closest_approach_two_lines(p1: np.ndarray, v1: np.ndarray, p2: np.ndarray, v2: np.ndarray) -> tuple[float, float]:
        """
        Solution from: https://math.stackexchange.com/questions/1993953/closest-points-between-two-lines
        Determines closest approach between two lines L1 and L2 with L1 = p1 + t*v1 and L2 = p2 + s*v2
        :param p1: position vector of line 1
        :param v1: direction vector of line 1
        :param p2: position vector of line 2
        :param v2: direction vector of line 2
        :return: (t, s)
        """
        # determine matrix parameters
        m11 = np.dot(v2, v1)
        m12 = -np.dot(v1, v1)
        m21 = np.dot(v2, v2)
        m22 = -np.dot(v1, v2)
        n1 = np.dot(p1, v1) - np.dot(p2, v1)
        n2 = np.dot(p1, v2) - np.dot(p2, v2)
        # determine parameter solutions
        m = np.array([[m11, m12], [m21, m22]])
        n = np.array([n1, n2])
        solutions = np.linalg.solve(m, n)
        return solutions[0], solutions[1]

    @staticmethod
    def intersection_center_point(p1: np.ndarray, v1: np.ndarray, p2: np.ndarray, v2: np.ndarray) -> np.ndarray:
        """
        Determines center point of closest approach between two lines L1 and L2 with L1 = p1 + t*v1 and L2 = p2 + s*v2
        :param p1: position vector of line 1
        :param v1: direction vector of line 1
        :param p2: position vector of line 2
        :param v2: direction vector of line 2
        :return: point vector which somewhat resembles an intersection between two lines which do not intersect
        """
        t, s = DualFrameMeasurementSeries.closest_approach_two_lines(p1, v1, p2, v2)
        l1 = p1 + t*v1
        l2 = p2 + s*v2
        l1_l2 = l2 - l1
        return l1 + 0.5 * l1_l2



class OrbitalParameterDeterminer:

    def __init__(self):
