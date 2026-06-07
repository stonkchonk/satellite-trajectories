import math

import cv2
import numpy as np

from common import Code, Params
from se_automation import WindowController, VirtualCamera
from star_tracker.star_pairing import CatalogStarPair
from star_tracker.pairings import pairings
from star_tracker.star_imager import ObservedStarPair, StarImager, ObservedStar, ObservedQuadruple
from star_tracker.catalog_dict import catalog_dict
from star_tracker.neighbors import neighbors


class StarMatcher:

    def __init__(self, observed_quadruple: ObservedQuadruple):
        self.observed_stars = observed_quadruple.observed_stars_dict
        self.observed_pairings = observed_quadruple.observed_pairings_dict
        assert len(self.observed_stars) == 4
        assert len(self.observed_pairings) == 6
        # immediately draw candidate quadruple after creating instance of this
        self.draw_candidate_quadruple_into_capture()


    @staticmethod
    def _row_match(input_row: any, match_relevant_indices: list[int]) -> bool:
        assert len(match_relevant_indices) == 3
        for idx in match_relevant_indices:
            if input_row[idx] == 0:
                return False
        return True

    @staticmethod
    def first_star_candidate(input_row: any) -> bool:
        return StarMatcher._row_match(input_row, StarImager.pairing_ids_of_a_star.get(0))

    @staticmethod
    def second_star_candidate(input_row: any) -> bool:
        return StarMatcher._row_match(input_row, StarImager.pairing_ids_of_a_star.get(1))

    @staticmethod
    def third_star_candidate(input_row: any) -> bool:
        return StarMatcher._row_match(input_row, StarImager.pairing_ids_of_a_star.get(2))

    @staticmethod
    def fourth_star_candidate(input_row: any) -> bool:
        return StarMatcher._row_match(input_row, StarImager.pairing_ids_of_a_star.get(3))

    @staticmethod
    def cosine_separation_in_bounds(measured_cosine_separation: float, supposed_cosine_separation: float, delta_angular_separation_deg: float = 0.1) -> bool:
        measured_angular_separation = Code.cosine_separation_to_angle_deg(measured_cosine_separation)
        min_angular_separation = max(measured_angular_separation - delta_angular_separation_deg, 0)
        max_angular_separation = min(measured_angular_separation + delta_angular_separation_deg, 90)
        supposed_angular_separation = Code.cosine_separation_to_angle_deg(supposed_cosine_separation)
        return min_angular_separation <= supposed_angular_separation <= max_angular_separation

    def determine_candidate_pair_array(self, observed_star_pair: ObservedStarPair) -> list[CatalogStarPair]:
        candidate_catalog_pairs = list(filter(lambda pair: self.cosine_separation_in_bounds(observed_star_pair.cosine_separation, pair.cosine_separation), pairings))
        return candidate_catalog_pairs

    def matcher_matrix(self) -> np.ndarray:
        candidate_pair_array_dict = {}
        for identifier in self.observed_pairings.keys():
            observed_star_pair = self.observed_pairings.get(identifier)
            candidate_pair_array = self.determine_candidate_pair_array(observed_star_pair)
            candidate_pair_array_dict[identifier] = candidate_pair_array

        match_matrix = np.zeros((len(catalog_dict), 6))

        for star_id in catalog_dict.keys():
            for observed_pair_id in self.observed_pairings.keys():
                candidate_pair_array = candidate_pair_array_dict.get(observed_pair_id)

                star_id_in_candidate_pairs = False
                for candidate_pair in candidate_pair_array:
                    contains_star_id = candidate_pair.star_id_contained(star_id)
                    if contains_star_id:
                        star_id_in_candidate_pairs = True
                        break
                if star_id_in_candidate_pairs:
                    match_matrix[star_id][observed_pair_id] = 1
        return match_matrix

    def _candidate_has_valid_neighbors(self, candidate_star_id: int, observed_star_id: int, match_sets: list[set[int]]) -> bool:
        assert len(match_sets) == 4
        assert candidate_star_id in match_sets[observed_star_id]
        assert 0 <= observed_star_id <= 3

        other_sets = Code.list_exclude_element(match_sets, observed_star_id)
        other_observed_star_ids = Code.list_exclude_element(StarImager.matching_candidate_ids, observed_star_id)
        candidate_star = catalog_dict.get(candidate_star_id)
        neighbor_set = neighbors.get(candidate_star_id)
        has_neighbor_in_bounds_in_other_sets = [False for other_set in other_sets]
        for other_set_idx, other_set in enumerate(other_sets):
            other_observed_star_id = other_observed_star_ids[other_set_idx]
            common_star_ids = neighbor_set.intersection(other_set)
            if len(common_star_ids) < 1:
                return False
            has_neighbor_in_bounds = False
            measured_cosine_separation = self.observed_pairings.get(StarImager.pairing_id_by_pair.get((observed_star_id, other_observed_star_id))).cosine_separation
            for common_star_id in common_star_ids:
                common_star = catalog_dict.get(common_star_id)
                supposed_cosine_separation = common_star.position.dot_product(candidate_star.position)
                if StarMatcher.cosine_separation_in_bounds(measured_cosine_separation, supposed_cosine_separation):
                    has_neighbor_in_bounds = True
            has_neighbor_in_bounds_in_other_sets[other_set_idx] = has_neighbor_in_bounds
        return all(has_neighbor_in_bounds_in_other_sets)

    @staticmethod
    def _count_match_sets_members(match_sets: list[set[int]]) -> int:
        return sum([len(ms) for ms in match_sets])

    def _clear_match_sets(self, match_sets: list[set[int]]) -> list[set[int]]:
        cleared_match_sets = []
        for set_idx, match_set in enumerate(match_sets):
            stars_to_eliminate_from_match_set = set()
            for star_id in match_set:
                has_valid_neighborhood = self._candidate_has_valid_neighbors(star_id, set_idx, match_sets)
                if not has_valid_neighborhood:
                    stars_to_eliminate_from_match_set.add(star_id)
            cleared_match_set = match_set.difference(stars_to_eliminate_from_match_set)
            cleared_match_sets.append(cleared_match_set)
        return cleared_match_sets

    def determine_matching_quadruple_from_matrix(self, matcher_matrix: np.ndarray) -> dict[int, int] | None:
        first_matches: set[int] = set()
        second_matches: set[int] = set()
        third_matches: set[int] = set()
        fourth_matches: set[int] = set()
        match_sets = [first_matches, second_matches, third_matches, fourth_matches]

        # put all candidate stars into set of corresponding observed star
        for row_idx, row_entries in enumerate(matcher_matrix):
            if self.first_star_candidate(row_entries):
                first_matches.add(row_idx)
            if self.second_star_candidate(row_entries):
                second_matches.add(row_idx)
            if self.third_star_candidate(row_entries):
                third_matches.add(row_idx)
            if self.fourth_star_candidate(row_entries):
                fourth_matches.add(row_idx)

        current_match_sets_size = self._count_match_sets_members(match_sets)
        new_match_sets_size = math.inf
        while current_match_sets_size != new_match_sets_size and new_match_sets_size > 0:
            current_match_sets_size = self._count_match_sets_members(match_sets)
            match_sets = self._clear_match_sets(match_sets)
            new_match_sets_size = self._count_match_sets_members(match_sets)


        print("\n\n\n")
        for cleared in match_sets:
            for identifier in cleared:
                print(f"{identifier}: {catalog_dict.get(identifier).name}")
            print("---")
        print("-----------")
        matching_quadruple = self._reduce_cleared_match_sets_to_dict(match_sets)
        if matching_quadruple is None:
            raise Exception("Could not match stars with given observed quadruple.")
        self.draw_matched_stars_into_capture(matching_quadruple)
        return matching_quadruple

    @staticmethod
    def _reduce_cleared_match_sets_to_dict(cleared_match_sets: list[set[int]]) -> dict[int, int] | None:
        assert len(cleared_match_sets) == 4
        min_elements = 2
        for match_set in cleared_match_sets:
            min_elements = min(min_elements, len(match_set))
        if min_elements != 1:
            # there must be at least a single non-binary star to rule out misidentification because binaries are unknown
            return None
        else:
            quadruple_dict = {}
            for idx, identifier in enumerate(StarImager.matching_candidate_ids):
                quadruple_dict[identifier] = cleared_match_sets[idx].pop()
            return quadruple_dict

    def determine_matching_quadruple(self) -> dict[int, int] | None:
        return self.determine_matching_quadruple_from_matrix(self.matcher_matrix())

    def draw_matched_stars_into_capture(self, matched_ids_dict: dict[int, int]):
        assert len(matched_ids_dict) == 4
        gray_img = Code.read_debug_image(Params.debug_gray_img)
        for idx in self.observed_stars.keys():
            observed = self.observed_stars.get(idx)
            float_pos = observed.position
            int_x, int_y = int(float_pos[0]), int(float_pos[1])
            cv2.circle(gray_img, (int_x, int_y), radius=10, color=(0, 0, 255), thickness=1)
            cv2.putText(
                gray_img,
                catalog_dict.get(matched_ids_dict[idx]).name, (int_x + 15, int_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA
            )
        Code.save_debug_image(Params.debug_matched_img, gray_img)

    def draw_candidate_quadruple_into_capture(self):
        gray_img = Code.read_debug_image(Params.debug_gray_img)
        for idx in self.observed_stars.keys():
            observed = self.observed_stars.get(idx)
            float_pos = observed.position
            int_x, int_y = int(float_pos[0]), int(float_pos[1])
            cv2.circle(gray_img, (int_x, int_y), radius=10, color=(0, 128, 255), thickness=1)
            cv2.putText(
                gray_img,
                str(idx), (int_x + 15, int_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1, cv2.LINE_AA
            )
        Code.save_debug_image(Params.debug_candidates_img, gray_img)


class MultiMatcher:
    """
    Like StarMatcher but can take a list of quadruples for match making.
    """
    def __init__(self, observed_quadruples: list[ObservedQuadruple]):
        self.observed_quadruples = observed_quadruples

    def determine_match_from_multiple_quadruples(self) -> tuple[dict[int, int], dict[int, ObservedStar]] | None:
        """
        Returns matched star ids as dictionary as well as the corresponding observed stars.
        :return:
        """
        num_of_quadruples = len(self.observed_quadruples)
        for idx, observed_quadruple in enumerate(self.observed_quadruples):
            try:
                print(f"Try with quadruple {idx + 1 } of {num_of_quadruples}.")
                matcher = StarMatcher(observed_quadruple)
                matching_quadruple_ids = matcher.determine_matching_quadruple()
                return matching_quadruple_ids, observed_quadruple.observed_stars_dict
            except:
                print(f"Could not match with quadruple {idx+1} of {num_of_quadruples}.")
        return None





if __name__ == "__main__":
    WindowController.initial_setup()
    field_of_view = 17
    exposure_comp = 1.5
    star_magnitude_limit = 4.5
    tracker_cam = VirtualCamera("Star Tracker Camera", field_of_view, exposure_comp, star_magnitude_limit)
    tracker_cam.setup()

    night_sky_image = tracker_cam.take_screenshot("nightsky")
    star_imager = StarImager(field_of_view, True)
    observed_viable_quadruples = star_imager.determine_viable_quadruples(night_sky_image)

    # not enough stars in frame
    if observed_viable_quadruples is None:
        print("Could not match any stars within this frame.")
        exit(1)

    print(f"Number of Quadruples in frame: {len(observed_viable_quadruples)}")
    multi_matcher = MultiMatcher(observed_viable_quadruples)
    matching_result = multi_matcher.determine_match_from_multiple_quadruples()

    # if no match is possible return None
    if matching_result is None:
        print("Could not match any stars within this frame.")
        exit(1)

    # unpack matched stars and observed stars
    matching_quadruple_ids, observed_stars_dict = matching_result
    print(f"Matched Ids: {matching_quadruple_ids}")