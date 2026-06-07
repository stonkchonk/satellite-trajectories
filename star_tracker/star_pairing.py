from math import pi, cos

from star_tracker.catalog_parser import CatalogStar
from star_tracker.catalog_dict import catalog_dict


class CatalogStarPair:
    def __init__(self, first_id: int, second_id: int, cosine_separation: float):
        assert first_id != second_id
        self.first_id = first_id
        self.second_id = second_id
        self.cosine_separation = cosine_separation

    def star_id_contained(self, star_id) -> bool:
        if star_id == self.first_id or star_id == self.second_id:
            return True
        else:
            return False

    @staticmethod
    def sorting_key(star_pair_object: any) -> float:
        return star_pair_object.cosine_separation

    def __str__(self):
        return f"CatalogStarPair({self.first_id}, {self.second_id}, {self.cosine_separation})"


class PairingDeterminer:
    radians_per_degree = pi / 180
    pairings_file = "pairings.py"
    neighbors_file = "neighbors.py"

    def __init__(self, max_viable_angle_deg: float, min_viable_angle_deg: float, max_magnitude: float,
                 catalog_stars: dict[int, CatalogStar]):
        max_viable_angle_rad = max_viable_angle_deg * self.radians_per_degree
        min_viable_angle_rad = min_viable_angle_deg * self.radians_per_degree
        self.min_viable_cosine = cos(min_viable_angle_rad)
        self.max_viable_cosine = cos(max_viable_angle_rad)
        self.filtered_catalog_dict = self._filter_by_magnitude(catalog_stars, max_magnitude)

    @staticmethod
    def _filter_by_magnitude(catalog_stars: dict[int, CatalogStar], max_magnitude: float) -> dict[int, CatalogStar]:
        stars_to_remove = []
        for identifier in catalog_stars.keys():
            star = catalog_stars.get(identifier)
            if star.visual_magnitude > max_magnitude:
                stars_to_remove.append(identifier)
        for identifier in stars_to_remove:
            del catalog_stars[identifier]
        return catalog_stars

    def determine_viable_pairings(self) -> list[CatalogStarPair]:
        viable_star_pairs = []
        star_ids = set(self.filtered_catalog_dict.keys())
        #print("determine all possible pairing tuples")
        pairing_tuples = self.pairing_tuples(star_ids)
        #print("determine viable pairs")
        for pairing_tuple in pairing_tuples:
            first_id, second_id = pairing_tuple
            first_star, second_star = self.filtered_catalog_dict.get(first_id), self.filtered_catalog_dict.get(second_id)
            cosine_separation = first_star.position.dot_product(second_star.position)
            separation_viable = self.min_viable_cosine >= cosine_separation >= self.max_viable_cosine
            if separation_viable:
                viable_star_pairs.append(CatalogStarPair(first_id, second_id, cosine_separation))
        return viable_star_pairs

    def generate_pairing_file(self, visible_star_pairs: list[CatalogStarPair]):
        file_str = "from star_tracker.star_pairing import CatalogStarPair\n\n"
        file_str += "pairings = [\n"
        for idx, star_pair in enumerate(visible_star_pairs):
            file_str += f"\t{str(star_pair)},\n"
        file_str += "]\n"
        with open(self.pairings_file, "w") as f:
            f.write(file_str)

    def generate_neighbors_file(self, visible_star_pairs: list[CatalogStarPair]):
        neighbors_dict: dict[int, set] = {}
        for star_pair in visible_star_pairs:
            first_id = star_pair.first_id
            second_id = star_pair.second_id
            first_entry = neighbors_dict.get(first_id)
            second_entry = neighbors_dict.get(second_id)
            if first_entry is not None:
                first_entry.add(second_id)
            else:
                neighbors_dict[first_id] = {second_id}
            if second_entry is not None:
                second_entry.add(first_id)
            else:
                neighbors_dict[second_id] = {first_id}
        file_str = "neighbors = {\n"
        for star_id in neighbors_dict.keys():
            neighbor_set = neighbors_dict.get(star_id)
            file_str += 4*" " + f"{star_id}: {str(neighbor_set)},\n"
        file_str = file_str[:-2]
        file_str += "\n}\n"
        with open(self.neighbors_file, "w") as f:
            f.write(file_str)

    @staticmethod
    def pairing_tuples(indices: set[int]) -> set[tuple[int, int]]:
        pairs = set()
        for idx in indices:
            indices_without_idx = indices - {idx}
            for jdx in indices_without_idx:
                pair = (idx, jdx)
                flipped = (jdx, idx)
                if pair not in pairs and flipped not in pairs:
                    pairs.add(pair)
                    if len(pairs) % 1000000 == 0:
                        print(f"Current pairing tuples: {len(pairs)}")
        return pairs


if __name__ == "__main__":
    #catalog_stars_dict = catalog_dict
    #stars_to_remove = []
    #for identifier in catalog_stars_dict.keys():
    #    star = catalog_stars_dict.get(identifier)
    #    if star.visual_magnitude > 4.3:
    #        stars_to_remove.append(identifier)
    #for identifier in stars_to_remove:
    #    del catalog_stars_dict[identifier]
    #print(len(catalog_stars_dict))
    max_fov = 17.0
    max_magnitude = 4.9
    pd = PairingDeterminer(max_fov, max_fov / 1000, max_magnitude, catalog_dict)
    pairings = pd.determine_viable_pairings()
    pairings.sort(key=CatalogStarPair.sorting_key)
    print(len(pairings), len(pd.filtered_catalog_dict))
    pd.generate_pairing_file(pairings)
    pd.generate_neighbors_file(pairings)