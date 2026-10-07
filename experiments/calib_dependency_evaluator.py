import numpy as np
from matplotlib import pyplot as plt

from algorithms import ParametricTrajectory, SimplifiedGaussAlgorithm, CircularTrajectory
from common import Code, Params
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from experiments.span_evaluator import _propagation_error
from procedures import SingleFrameMeasurementSeriesMultiCalib
from star_tracker.catalog_dict import catalog_dict
from star_tracker.catalog_parser import UnitVector


def sort_tuples(data: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return sorted(data, key=lambda x: x[0])

def condition_number(matrix: np.ndarray) -> float:
    assert matrix.shape == (3, 3)
    return float(np.linalg.norm(matrix, 2) * np.linalg.norm(np.linalg.inv(matrix), 2))

def make_plot(num_vs_propagation_error: list[list[tuple[float, float]]], det_or_condition: bool) -> None:
    plt.figure(figsize=(12, 7))

    data = [[value[1] for value in row] for row in num_vs_propagation_error]

    plt.title(
        rf"Propagation Error $f_p$ subject to "
        f"{"Determinant" if det_or_condition else "Condition Number"}"
    )

    plt.imshow(data, cmap="viridis", aspect="auto")

    plt.colorbar(label=r"$f_p\quad[a_g]$")

    x_values = [liste[0] for liste in num_vs_propagation_error[0]]

    print(x_values)
    print(len(x_values))

    x_indices = range(0, len(x_values), 3)

    plt.xticks(
        x_indices,
        [f"{x_values[i]:.3g}" for i in x_indices],
        rotation=90
    )

    plt.xlabel(
        f"{"Determinant" if det_or_condition else "Condition Number"}"
    )

    plt.ylabel(r"$m$ circulations")

    filename = Params.thesis_plots_dir + ("propagation_error_determinant.png" if det_or_condition \
        else "propagation_error_condition_number.png")

    plt.savefig(filename, dpi=300, bbox_inches="tight")

    plt.show()
    plt.close()



if __name__ == "__main__":
    ground_truth_orbit_dict, plane_normal_ground_truth = get_orbit_ground_truth()
    gt_pt = ParametricTrajectory.without_valid_init()
    gt_pt.semi_major_axis = ground_truth_orbit_dict.get("semi_major_axis_km")
    gt_pt.eccentricity = ground_truth_orbit_dict.get("eccentricity")
    gt_pt.argument_of_periapsis = Code.deg_to_rad(ground_truth_orbit_dict.get("argument_periapsis_deg"))
    gt_pt.plane_normal_vector = UnitVector(plane_normal_ground_truth)
    series_names = [
        "L5_20-03-00",
        "L5_20-03-42",
        "L5_20-04-20",
        "L5_20-05-41",
    ]
    series_multi_calib = [SingleFrameMeasurementSeriesMultiCalib.from_json(name) for name in series_names]

    determinant_vs_propagation_error: list[list[tuple[float, float]]] = []
    condition_number_vs_propagation_error: list[list[tuple[float, float]]] = []

    for n_propagations in range(1, 50+1):
        determinant_vs_propagation_error_i: list[tuple[float, float]] = []
        condition_number_vs_propagation_error_i: list[tuple[float, float]] = []

        for series in series_multi_calib:
            for idx, calib_stars in series.calibration_star_ids.items():
                star_vector_matrix = np.array([catalog_dict.get(star_id).position.value for star_id in calib_stars])
                condition_val = condition_number(star_vector_matrix)
                determinant_val = abs(float(np.linalg.det(star_vector_matrix)))

                sfms = series.measurement_series.get(idx)
                first = sfms[0]
                last = sfms[-1]
                simple_gauss_orbit_model = SimplifiedGaussAlgorithm(first.time_stamp.determine_ut_s(),
                                                                    last.time_stamp.determine_ut_s(),
                                                                    first.position_vector, last.position_vector,
                                                                    first.view_vector.value, last.view_vector.value)
                r_vectors = simple_gauss_orbit_model.determine_solution()
                pt = ParametricTrajectory.from_circular_trajectory(CircularTrajectory.from_eci_measurements(r_vectors))

                propagation_error_number = _propagation_error(gt_pt, pt, n_propagations)

                determinant_vs_propagation_error_i.append((determinant_val, propagation_error_number))
                condition_number_vs_propagation_error_i.append((condition_val, propagation_error_number))

        determinant_vs_propagation_error_i = sort_tuples(determinant_vs_propagation_error_i)
        condition_number_vs_propagation_error_i = sort_tuples(condition_number_vs_propagation_error_i)

        determinant_vs_propagation_error.append(determinant_vs_propagation_error_i)
        condition_number_vs_propagation_error.append(condition_number_vs_propagation_error_i)



    print(determinant_vs_propagation_error)
    print(condition_number_vs_propagation_error)
    make_plot(determinant_vs_propagation_error, det_or_condition=True)
    make_plot(condition_number_vs_propagation_error, det_or_condition=False)


