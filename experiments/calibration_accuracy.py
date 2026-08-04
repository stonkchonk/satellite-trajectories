import math

import numpy as np
from matplotlib import pyplot as plt
from numpy.f2py.auxfuncs import throw_error

from common import Code
from procedures import CameraCalibration
from se_automation import WindowController
from star_tracker.catalog_dict import catalog_dict
from star_tracker.catalog_parser import UnitVector


def combined_calibration_error(calculated_center: UnitVector, calculated_top: UnitVector, calculated_left: UnitVector, fov_deg: float) -> float:
    fov_rad = Code.deg_to_rad(fov_deg)
    supposed_separation_center_top = fov_rad / 2
    supposed_separation_center_left = fov_rad / 2
    supposed_separation_top_left = math.acos(math.cos(fov_rad / 2) ** 2)
    center_top_error = relative_angular_error(supposed_separation_center_top, calculated_center.value, calculated_top.value)
    center_left_error = relative_angular_error(supposed_separation_center_left, calculated_center.value, calculated_left.value)
    top_left_error = relative_angular_error(supposed_separation_top_left, calculated_top.value, calculated_left.value)
    return center_top_error + center_left_error + top_left_error

def relative_angular_error(supposed_angular_separation_rad: float, v1: np.ndarray, v2: np.ndarray) -> float:
    return abs(Code.angular_separation_of_two_vectors_rad(v1, v2) - supposed_angular_separation_rad)/ supposed_angular_separation_rad

def condition_number(matrix: np.ndarray) -> float:
    assert matrix.shape == (3, 3)
    return float(np.linalg.norm(matrix, 2) * np.linalg.norm(np.linalg.inv(matrix), 2))

def plot_measurements(x_values: list[float], y_values: list[float]) -> None:
    plt.figure(figsize=(8, 5))
    plt.scatter(x_values, y_values)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)

    plt.show()




if __name__ == "__main__":
    measure_or_plot = False
    if measure_or_plot:
        WindowController.initial_setup()
        calib = CameraCalibration()
        matchable_quadruples = calib.determine_matchable_quadruples(50)
        error_measurements: list[tuple[float, float, float]] = []
        for entry in matchable_quadruples:
            matched_dict, observed_dict = entry
            print(matched_dict)
            for key in observed_dict.keys():
                print(key, observed_dict[key].position)
            print("---")
            three_star_ids = list(matched_dict.values())[:-1]
            three_observed = list(observed_dict.values())[:-1]
            fixed_point_vectors = calib.determine_fixed_point_view_vectors(three_observed, three_star_ids, calib.calibration_cam.field_of_view)
            center_view_vector, top_view_vector, left_view_vector = fixed_point_vectors
            combined_error = combined_calibration_error(center_view_vector, top_view_vector, left_view_vector, calib.calibration_cam.field_of_view)

            star_vectors = [catalog_dict.get(star_id).position.value for star_id in three_star_ids]
            vector_matrix = np.array(star_vectors)
            print(f"error: {combined_error},\n"
                  f" star ids: {three_star_ids},\n"
                  f"condition number: {condition_number(vector_matrix)},\n"
                  f"determinant: {np.linalg.det(vector_matrix)}")
            print(combined_error, three_star_ids, vector_matrix, condition_number(vector_matrix), np.linalg.det(vector_matrix))
            error_measurements.append((combined_error, condition_number(vector_matrix), np.linalg.det(vector_matrix)))
            print('-------------')

        Code.append_measurement_list("calibration_error.json", error_measurements)
        print(len(matchable_quadruples),len(Code.load_measurement_list("calibration_error.json")), "<<len")
    else:
        measurements = Code.load_measurement_list("calibration_error.json")
        combined_errors_percent = [x[0] * 100 for x in measurements]
        conditions = [x[1] for x in measurements]
        abs_determinant = [abs(x[2]) for x in measurements]
        plot_measurements(combined_errors_percent, conditions)
        plot_measurements(combined_errors_percent, abs_determinant)
    #star_vectors = [catalog_dict.get(star_id).position.value for star_id in star_ids]
    #vector_matrix = np.array(star_vectors[:-1])
    #combined_error = combined_calibration_error(calib.center_view_vector, calib.top_view_vector, calib.left_view_vector, calib.calibration_cam.field_of_view)
    #print(combined_error, star_ids, vector_matrix, condition_number(vector_matrix), np.linalg.det(vector_matrix))