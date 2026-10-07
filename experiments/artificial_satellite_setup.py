import json

import numpy as np
from math import sin, cos

from algorithms import ParametricTrajectory
from se_automation import SatelliteController
from common import Constants, Params, Code
from star_tracker.catalog_parser import UnitVector
from star_tracker.precession import Precession

# mean anomaly at specific altitude will make satellite appear in zenith at 2000.01.01 20:03:00 at (-27.257356, -64.963269)
default_altitude = 700
altitude_mean_anomaly_dict = {
    300: 198.864713,
    500: 282.364949,
    700: 0.0,
    900: 72.330856,
    1100: 139.851359,
    1300: 202.997767,
    1500: 262.156756,
    1700: 317.672136,
    1900: 9.850521,
    2100: 58.966128
}

def _plane_normal_from(inclination_deg: float, arg_ascending_deg: float) -> np.ndarray:
    inclination_rad = Code.deg_to_rad(inclination_deg)
    arg_ascending_rad = Code.deg_to_rad(arg_ascending_deg)
    normal_vector = np.array([
        sin(inclination_rad) * sin(arg_ascending_rad),
        -sin(inclination_rad) * cos(arg_ascending_rad),
        cos(inclination_rad)
    ])
    precession = Precession(Constants.julian_centuries_since_j2000)
    return precession.precess_vector_since_j2000(normal_vector)

def get_orbit_ground_truth() -> tuple[dict[str, float], np.ndarray]:
    ground_truth_dict = Code.load_json_content(Params.orbit_ground_truth)
    return ground_truth_dict, _plane_normal_from(ground_truth_dict[Params.argument_inclination_deg],
                                                 ground_truth_dict[Params.argument_ascension_deg])

def get_orbit_parametric_trajectory_from_dict(ground_truth_dict: dict[str, float]) -> ParametricTrajectory:
    plane_normal_vector = UnitVector(_plane_normal_from(ground_truth_dict[Params.argument_inclination_deg],
                                    ground_truth_dict[Params.argument_ascension_deg]))
    gt_pt = ParametricTrajectory.without_valid_init()
    gt_pt.semi_major_axis = ground_truth_dict.get("semi_major_axis_km")
    gt_pt.eccentricity = ground_truth_dict.get("eccentricity")
    gt_pt.argument_of_periapsis = Code.deg_to_rad(ground_truth_dict.get("argument_periapsis_deg"))
    gt_pt.plane_normal_vector = plane_normal_vector
    return gt_pt


if __name__ == "__main__":
    altitude_km = default_altitude
    semi_major_axis_km = Constants.earth_mean_radius + altitude_km
    eccentricity =  0
    argument_periapsis_deg = 0
    argument_inclination_deg = 52
    argument_ascension_deg = 0
    mean_anomaly = altitude_mean_anomaly_dict.get(altitude_km, 0)

    # fixed parameters for all arbits which must not be changed in order to maintain reproducibility
    pericenter_epoch = 2451545.0 #J2000 -> 2000.01.01 12:00:00
    SatelliteController.spawn_satellite(0.01, semi_major_axis_km, eccentricity, argument_periapsis_deg,
                                        argument_inclination_deg, argument_ascension_deg, mean_anomaly_deg=mean_anomaly)

    ground_truth_dict = {
        Params.semi_major_axis_km: semi_major_axis_km,
        Params.eccentricity: eccentricity,
        Params.argument_periapsis_deg: argument_periapsis_deg,
        Params.argument_inclination_deg: argument_inclination_deg,
        Params.argument_ascension_deg: argument_ascension_deg,
        Params.pericenter_epoch: pericenter_epoch,
        Params.mean_anomaly: mean_anomaly
    }

    Code.write_text_file(Params.orbit_ground_truth, json.dumps(ground_truth_dict, indent=4))


    test = get_orbit_ground_truth()
    print(test)
    print("done")