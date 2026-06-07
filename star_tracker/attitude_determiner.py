import math

import cv2
import numpy as np

from common import Code, Params
from se_automation import WindowController, VirtualCamera
from star_tracker.catalog_dict import catalog_dict
from star_tracker.catalog_parser import UnitVector, CatalogStar
from star_tracker.star_imager import ObservedStar, StarImager
from star_tracker.star_matching import StarMatcher, MultiMatcher


class AttitudeDeterminer:
    def __init__(self, field_of_view_deg: float):
        self.field_of_view_deg = field_of_view_deg

    def triangulate_view_vector(self, target_view_point: tuple[float, float], three_observed: list[ObservedStar], three_matched_ids: list[int]) -> UnitVector:
        assert len(three_observed) == 3
        assert len(three_matched_ids) == 3
        three_matched_catalog_stars = [catalog_dict.get(idx) for idx in three_matched_ids]
        euclidean_distances = [Code.euclidean_distance(target_view_point, observed.position) for observed in three_observed]
        cosine_separations = np.array([math.cos(Code.deg_to_rad(self.field_of_view_deg) * eu_dist/Params.width_height[0]) for eu_dist in euclidean_distances])
        star_position_matrix = np.array([match.position.value for match in three_matched_catalog_stars])
        triangulated_unit_vector = UnitVector(np.linalg.solve(star_position_matrix, cosine_separations))
        return triangulated_unit_vector

    def determine_rotation_axis(self, three_observed: list[ObservedStar], three_matched_ids: list[int]) -> UnitVector:
        left_edge_point = (0, Params.norm_radius)
        right_edge_point = (Params.norm_radius * 2, Params.norm_radius)
        left_edge_vector = self.triangulate_view_vector(left_edge_point, three_observed, three_matched_ids)
        right_edge_vector = self.triangulate_view_vector(right_edge_point, three_observed, three_matched_ids)
        return UnitVector.from_cross_product(right_edge_vector, left_edge_vector)

    def draw_view_vector(self, view_vector: UnitVector):
        cross_size = 5
        color = (0, 255, 0)
        thickness = 2
        int_x, int_y = Params.center_point_as_int
        matched_img = Code.read_debug_image(Params.debug_matched_img)
        ra_text, dec_text = Code.fancy_format_ra_dec(view_vector.to_degrees, True)

        cv2.line(matched_img, (int_x - cross_size, int_y), (int_x + cross_size, int_y), color, thickness)
        cv2.line(matched_img, (int_x, int_y - cross_size), (int_x, int_y + cross_size), color, thickness)

        cv2.putText(
            matched_img,
            ra_text, (int_x + 15, int_y - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA
        )
        cv2.putText(
            matched_img,
            dec_text, (int_x + 15, int_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA
        )
        Code.save_debug_image(Params.debug_triangulated_img, matched_img)

    def view_attitude_determination_procedure(self, virtual_camera: VirtualCamera) -> tuple[UnitVector, UnitVector] | None:
        """
        Virtual camera must be set up and pointing at the sun before running this procedure.
        Returns tuple of view vector and rotation axis vector or None if view vector cannot be determined.
        """
        night_sky_image = virtual_camera.take_screenshot("nightsky")
        star_imager = StarImager(field_of_view, True)
        observed_viable_quadruples = star_imager.determine_viable_quadruples(night_sky_image)

        # not enough stars in frame
        if observed_viable_quadruples is None:
            print("Could not match any stars within this frame.")
            return None

        print(f"Number of Quadruples in frame: {len(observed_viable_quadruples)}")
        multi_matcher = MultiMatcher(observed_viable_quadruples)
        matching_result = multi_matcher.determine_match_from_multiple_quadruples()

        # if no match is possible return None
        if matching_result is None:
            print("Could not match any stars within this frame.")
            return None

        # unpack matched stars and observed stars
        matching_quadruple_ids, observed_stars_dict = matching_result
        three_observed_stars = list(observed_stars_dict.values())[:-1]
        three_matched_stars = list(matching_quadruple_ids.values())[:-1]

        # triangulate view vector and rotation axis
        view_vector = self.triangulate_view_vector(Params.center_point, three_observed_stars, three_matched_stars)
        self.draw_view_vector(view_vector)
        axis_vector = self.determine_rotation_axis(three_observed_stars, three_matched_stars)
        print(f"Looking at: {Code.fancy_format_ra_dec(view_vector.to_degrees)}")
        return view_vector, axis_vector

    def full_attitude_determination_procedure(self, virtual_camera: VirtualCamera) -> UnitVector:
        """
        Virtual camera must be set up and pointing at the sun before running this procedure.
        Determines attitude relative to the sun by moving the camera frame.
        """
        # predefine camera turning angles
        turn_angles = [90]
        for num_of_angles in range(0, int(Params.degrees_per_half_circle // virtual_camera.field_of_view)):
            turn_angles.append(virtual_camera.field_of_view)

        for idx, turn_angle in enumerate(turn_angles):
            # turn camera, determine quadruples of current frame
            print(f"Attitude determination attempt {idx + 1} out of {len(turn_angles)} attempts.")
            virtual_camera.turn_precisely('y', turn_angle, turn_duration=5)

            view_attitude_vectors = self.view_attitude_determination_procedure(virtual_camera)
            if view_attitude_vectors is None:
                print("Continue turning camera to next frame.")
                continue
            view_vector, axis_vector = view_attitude_vectors

            # Calculate attitude relative to the sun from current turning angle, axis vector and view vector.
            current_turn_angle = sum(turn_angles[:idx+1])
            remaining_angle_until_half_turn = Params.degrees_per_half_circle - current_turn_angle

            attitude_unit_vector: UnitVector = UnitVector.from_rodrigues_rotation(axis_vector, view_vector,
                                                                                  remaining_angle_until_half_turn)
            return attitude_unit_vector


if __name__ == "__main__":
    WindowController.initial_setup()
    field_of_view = 17
    exposure_comp = 1.5
    star_magnitude_limit = 4.5
    tracker_cam = VirtualCamera("Star Tracker Camera", field_of_view, exposure_comp, star_magnitude_limit)
    tracker_cam.setup()
    #tracker_cam.set_position_celestial_coordinates(3, 14, 39, 36.494, '-', 60, 50, 15.0992) # alpha centauri

    # distance
    dist_au = 3.0
    # right ascension
    ra_h, ra_m, ra_s = 15, 31, 49.09
    # declination
    de_sign, de_d, de_m, de_s = '-', 39, 15, 50.8

    # schaut auf eta carina nebula: 2, 31, 49.09    '-', 39, 15, 50.8

    initial_position_vector = UnitVector.from_celestial_coordinate(ra_h, ra_m, ra_s, de_sign, de_d, de_m, de_s)

    tracker_cam.set_position_celestial_coordinates(dist_au, ra_h, ra_m, ra_s, de_sign, de_d, de_m, de_s)  # polaris

    atdt = AttitudeDeterminer(field_of_view)

    calculated_position_vector = atdt.full_attitude_determination_procedure(tracker_cam)
    print(f"Positioned at: {Code.fancy_format_ra_dec(calculated_position_vector.to_degrees)}")

    angular_separation_deg = Code.rad_to_deg(initial_position_vector.angular_rad_separation(calculated_position_vector))
    print(f"Angular separation between initial and calculated position: {angular_separation_deg}°.")