import numpy as np
from matplotlib import pyplot as plt

from algorithms import SimplifiedGaussAlgorithm, CircularTrajectory, ParametricTrajectory
from common import Params
from experiments.artificial_satellite_setup import altitude_mean_anomaly_dict, get_orbit_parametric_trajectory_from_dict
from experiments.span_evaluator import _propagation_error
from procedures import SingleFrameMeasurementSeries


def make_plot(data: list[list[float]], altitudes: list[float], smas: list[float]) -> None:
    plt.figure(figsize=(12, 7))
    data = np.array(data)
    plt.title(
        rf"Propagation Error $f_p$ subject to Semi Major Axis $a$"
    )

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            decimals = max(0, 3 - len(str(int(abs(value)))))

            plt.text(
                j,
                i,
                f"{value:.{decimals}f}",
                ha="center",
                va="center",
                color="white" if value < np.mean(data) else "black"
            )

    plt.imshow(data, cmap="viridis", aspect="auto")

    plt.colorbar(label=r"$f_p\quad[a_g]$")

    y_ticks = []
    for idx, alt in enumerate(altitudes):
        sma = smas[idx]
        y_ticks.append(f"{sma:.2f} ({alt})")

    x_ticks = [i for i in range(0, len(data[0]))]
    plt.xticks(x_ticks, [x_tick + 1 for x_tick in x_ticks])
    plt.yticks([i for i in range(len(altitudes))], y_ticks)
    plt.ylabel(
        f"Semi Major Axis (Altitude) [km]"
    )
    plt.xlabel(r"$\Delta t\quad[s]$")

    filename = Params.thesis_plots_dir + "propagation_error_variable_sma.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()

if __name__ == "__main__":

    altitudes_km = list(altitude_mean_anomaly_dict.keys())
    sfms_list = [SingleFrameMeasurementSeries.from_json(f"sma_test_{alt}km", directory=Params.single_frame_different_sma_dir) for alt in altitudes_km]
    smas_km = []

    propagation_errors = []
    for sfms in sfms_list:
        length = len(sfms.single_frame_measurements)
        gt_pt = get_orbit_parametric_trajectory_from_dict(sfms.ground_truth_orbit)
        smas_km.append(gt_pt.semi_major_axis)
        propagation_errors_i = []
        for i in range(1, length):
            first = sfms.single_frame_measurements[0]
            last = sfms.single_frame_measurements[i]
            simple_gauss_orbit_model = SimplifiedGaussAlgorithm(first.time_stamp.determine_ut_s(),
                                                                last.time_stamp.determine_ut_s(),
                                                                first.position_vector, last.position_vector,
                                                                first.view_vector.value, last.view_vector.value)
            r_vectors = simple_gauss_orbit_model.determine_solution()
            pt = ParametricTrajectory.from_circular_trajectory(CircularTrajectory.from_eci_measurements(r_vectors))
            propagation_error_number = _propagation_error(gt_pt, pt, 1)
            propagation_errors_i.append(propagation_error_number)

        propagation_errors.append(propagation_errors_i)

    print(propagation_errors)
    make_plot(propagation_errors, altitudes_km, smas_km)