import json

import numpy as np
from math import sin, cos

from se_scripting import Script
from se_automation import SatelliteController
from common import Constants, Params, Code

def _plane_normal_from(inclination_deg: float, arg_ascending_deg: float) -> np.ndarray:
    inclination_rad = Code.deg_to_rad(inclination_deg)
    arg_ascending_rad = Code.deg_to_rad(arg_ascending_deg)
    return np.array([
        sin(inclination_rad) * sin(arg_ascending_rad),
        -sin(inclination_rad) * cos(arg_ascending_rad),
        cos(inclination_rad)
    ])

def get_orbit_ground_truth() -> tuple[dict[str, float], np.ndarray]:
    ground_truth_dict = Code.load_json_content(Params.orbit_ground_truth)
    return ground_truth_dict, _plane_normal_from(ground_truth_dict[Params.argument_inclination_deg],
                                                 ground_truth_dict[Params.argument_ascension_deg])

if __name__ == "__main__":
    semi_major_axis_km = Constants.earth_mean_radius + 700
    eccentricity =  0
    argument_periapsis_deg = 0
    argument_inclination_deg = 52
    argument_ascension_deg = 0
    SatelliteController.spawn_satellite(0.01, semi_major_axis_km, eccentricity, argument_periapsis_deg,
                                        argument_inclination_deg, argument_ascension_deg)

    ground_truth_dict = {
        Params.semi_major_axis_km: semi_major_axis_km,
        Params.eccentricity: eccentricity,
        Params.argument_periapsis_deg: argument_periapsis_deg,
        Params.argument_inclination_deg: argument_inclination_deg,
        Params.argument_ascension_deg: argument_ascension_deg
    }

    Code.write_text_file(Params.orbit_ground_truth, json.dumps(ground_truth_dict, indent=4))


    test = get_orbit_ground_truth()
    print(test)
    print("done")