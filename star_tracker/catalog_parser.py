import math

import numpy as np
from math import sin, cos, pi

from common import Code, Params


class UnitVector:

    def __init__(self, value: np.ndarray):
        self.value = value / np.linalg.norm(value)

    @classmethod
    def from_celestial_radians(cls, right_ascension: float, declination: float):
        vector = np.array([
            cos(right_ascension)*cos(declination),
            sin(right_ascension)*cos(declination),
            sin(declination)
        ])
        return cls(vector)

    @property
    def to_radians(self) -> tuple[float, float]:
        """
        Outputs right ascension and declination as two pi radian values.
        """
        return math.atan2(self.value[1], self.value[0]), math.asin(self.value[2])

    @property
    def to_degrees(self) -> tuple[float, float]:
        r_rad, d_rad = self.to_radians
        factor = 1 / Params.radians_per_degree
        return r_rad * factor, d_rad * factor

    @classmethod
    def from_celestial_coordinate(cls, ra_hours: float, ra_minutes: float, ra_seconds: float,
                                  de_sign: str, de_degrees: float, de_minutes: float, de_seconds: float):
        """
        Creates directional unit vector from right ascension and declination coordinates.
        :param ra_hours: right ascension hours value
        :param ra_minutes: right ascension minutes value
        :param ra_seconds: right ascension seconds value
        :param de_sign: + or -
        :param de_degrees: declination full degrees value
        :param de_minutes: declination minutes value
        :param de_seconds: declination seconds value
        :return: An instance of this class
        """
        de_multiplier = -1 if de_sign == '-' else 1
        ra_radians = (ra_hours * Params.radians_per_hour + ra_minutes * Params.radians_per_minute +
                      ra_seconds * Params.radians_per_second)
        de_radians = (de_degrees * Params.radians_per_degree + de_minutes * Params.radians_per_arcmin +
                      de_seconds * Params.radians_per_arcsec) * de_multiplier
        return cls.from_celestial_radians(ra_radians, de_radians)

    @classmethod
    def from_array(cls, unit_vector_array: list[float]):
        return cls(np.array(unit_vector_array))

    def dot_product(self, other_unit_vector: any) -> np.float64:
        return np.dot(self.value, other_unit_vector.value)

    @classmethod
    def from_cross_product(cls, first_unit_vector: any, second_unit_vector: any):
        return cls(np.cross(first_unit_vector.value, second_unit_vector.value))

    @classmethod
    def from_rodrigues_rotation(cls, axis_unit_vector: any, position_unit_vector: any, rotation_angle_deg: float,
                                invert: bool = False):
        rotation_angle_deg = -rotation_angle_deg if invert else rotation_angle_deg
        theta = Code.deg_to_rad(rotation_angle_deg)
        v: np.ndarray = position_unit_vector.value
        k: np.ndarray = axis_unit_vector.value
        v_rot = v * cos(theta) + np.cross(k, v) * sin(theta) + k * np.dot(k, v) * (1 - cos(theta))
        return cls(v_rot)

    def angular_rad_separation(self, other_unit_vector: any) -> np.float64:
        return np.arccos(self.dot_product(other_unit_vector))

    def __str__(self):
        return f'UnitVector.from_array([{', '.join([str(e) for e in self.value.tolist()])}])'

    def __eq__(self, other: "UnitVector") -> bool:
        return self.value == other.value


class CatalogStar:
    def __init__(self, name: str, position: UnitVector, visual_magnitude: float):
        self.name = name
        self.position = position
        self.visual_magnitude = visual_magnitude

    def __str__(self):
        return f"CatalogStar(\"{self.name}\", {self.position}, {self.visual_magnitude})"


class Parser:
    # define byte indices for parsing relevant data values
    class Indices:
        #id_start = 1
        #id_end = 4
        name_start = 5
        name_end = 14
        hd_num_start = 26
        hd_num_end = 31
        ra_hours_start = 76
        ra_hours_end = 77
        ra_minutes_start = 78
        ra_minutes_end = 79
        ra_seconds_start = 80
        ra_seconds_end = 83
        de_sign = 84
        de_degrees_start = 85
        de_degrees_end = 86
        de_minutes_start = 87
        de_minutes_end = 88
        de_seconds_start = 89
        de_seconds_end = 90
        vmag_start = 103
        vmag_end = 107

    catalog_dict_file = "catalog_dict.py"

    def __init__(self):
        self.catalog_file = "../assets/catalog"
        self.catalog_dict: dict[int, CatalogStar] | None = None

    def parse(self):
        valid_stars = []
        with open(self.catalog_file, 'r') as file:
            for line in file:
                star = self.parse_catalog_line(line)
                if star is not None:
                    valid_stars.append(star)
        catalog_stars = {}
        for idx, star in enumerate(valid_stars):
            catalog_stars[idx] = star
        self.catalog_dict = catalog_stars

    def generate_catalog_dict_file(self):
        file_str = "from star_tracker.catalog_parser import CatalogStar, UnitVector\n\n"
        file_str += "catalog_dict = {\n"
        for idx in self.catalog_dict.keys():
            catalog_star = self.catalog_dict.get(idx)
            file_str += 4*" " + f"{idx}: {str(catalog_star)},\n"
        file_str = file_str[:-2]
        file_str += "\n}\n"
        with open(self.catalog_dict_file, "w") as f:
            f.write(file_str)

    def parse_catalog_line(self, line: str) -> CatalogStar | None:
        try:
            #identifier = int(self.substr(line, self.Indices.id_start, self.Indices.id_end))
            name = self.substr(line, self.Indices.name_start, self.Indices.name_end)
            if len(name) < 1:
                # use HD catalog number as name
                name = "HD" + self.substr(line, self.Indices.hd_num_start, self.Indices.hd_num_end)
            name = name.replace("    ", " ").replace("  ", " ")
            visual_magnitude = float(self.substr(line, self.Indices.vmag_start, self.Indices.vmag_end))

            ra_hours = float(self.substr(line, self.Indices.ra_hours_start, self.Indices.ra_hours_end))
            ra_minutes = float(self.substr(line, self.Indices.ra_minutes_start, self.Indices.ra_minutes_end))
            ra_seconds = float(self.substr(line, self.Indices.ra_seconds_start, self.Indices.ra_seconds_end))
            de_sign = self.substr(line, self.Indices.de_sign, self.Indices.de_sign)
            de_degrees = float(self.substr(line, self.Indices.de_degrees_start, self.Indices.de_degrees_end))
            de_minutes = float(self.substr(line, self.Indices.de_minutes_start, self.Indices.de_minutes_end))
            de_seconds = float(self.substr(line, self.Indices.de_seconds_start, self.Indices.de_seconds_end))
            position_vector = UnitVector.from_celestial_coordinate(ra_hours, ra_minutes, ra_seconds,
                                                                   de_sign, de_degrees, de_minutes, de_seconds)
            return CatalogStar(name, position_vector, visual_magnitude)
        except:
            # exception means that entry does not correspond to a star, rather a nebular, galaxy or cluster
            return None

    @staticmethod
    def substr(line: str, start_byte: int, end_byte: int) -> str:
        return line[start_byte - 1: end_byte].strip()


if __name__ == "__main__":
    parser = Parser()
    parser.parse()
    for star in parser.catalog_dict:
        print(star)
    print(len(parser.catalog_dict))
    parser.generate_catalog_dict_file()