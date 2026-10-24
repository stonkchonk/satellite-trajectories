from copy import copy
from math import cos, sin, pi
from pathlib import Path

import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from algorithms import ParametricTrajectory, GaussAlgorithm
from common import Constants
from experiments.artificial_satellite_setup import get_orbit_parametric_trajectory_from_dict, get_orbit_ground_truth
from procedures import SingleFrameMeasurementSeries, DualFrameMeasurementSeries

captured_30s_series = {
    -1: "zenith_failure_30s",
    0: "0_30s",
    1: "1_30s",
    2: "2_30s",
    3: "3_30s",
    4: "4_30s",
    5: "5_30s",
    6: "6_30s",
    7: "7_30s",
}

captured_1s_series = {
    -1: "zenith_failure_1s",
    0: "0_1s",
    1: "1_1s",
    2: "2_1s",
    3: "3_1s",
    4: "4_1s",
    5: "5_1s",
    6: "6_1s",
    7: "7_1s",
}

def create_gif(
    image_series_directory: str,
    duration: int = 500) -> None:
    image_file_names = _sort_img_filenames([f for f in os.listdir(image_series_directory) if f.endswith(".png")])
    print(image_file_names)
    image_files = [Image.open(os.path.join(image_series_directory, f)).convert("RGB") for f in image_file_names]
    image_files[0].save(
        image_series_directory + "/animated.gif",
        save_all=True,
        append_images=image_files[1:],
        duration=duration,
        loop=0,
    )
    for image in image_files:
        image.close()

def _sort_img_filenames(image_file_names: list[str]) -> list[str]:
    sorted_image_file_names = []
    image_name_indices = {}
    for image_file_name in image_file_names:
        underscore_idx = image_file_name.rindex("_")
        dot_idx = image_file_name.index(".")
        name_idx = int(image_file_name[underscore_idx + 1:dot_idx])
        image_name_indices[name_idx] = image_file_name
    for image_name_index in sorted(image_name_indices.keys()):
        sorted_image_file_names.append(image_name_indices[image_name_index])
    return sorted_image_file_names

def orbit_parametric_curve(
    theta: float,
    pt: ParametricTrajectory,
    x_or_y_value: bool,
) -> float:
    a = pt.semi_major_axis
    e = pt.eccentricity
    omega = pt.argument_of_periapsis

    denominator = 1 + e * cos(theta - omega)

    if e > 1 and denominator <= 0:
        return float("nan")

    r = a * (1 - e**2) / denominator

    return r * (cos(theta) if x_or_y_value else sin(theta))


def plot_parametric_2d(
    gt_pt: ParametricTrajectory,
    m_pt: ParametricTrajectory,
    theta_start: float=0,
    theta_end: float=2*pi,
    num_points: int = 1000,
    plt_prefix: str = "orbit_plt",
    plt_name: str = "orbit_plot",
    show: bool = True
) -> None:
    theta_values = np.linspace(theta_start, theta_end, num_points)

    # Ground truth orbit
    gt_x = np.array([
        orbit_parametric_curve(t, gt_pt, True)
        for t in theta_values
    ])
    gt_y = np.array([
        orbit_parametric_curve(t, gt_pt, False)
        for t in theta_values
    ])

    # Measured orbit
    m_x = np.array([
        orbit_parametric_curve(t, m_pt, True)
        for t in theta_values
    ])
    m_y = np.array([
        orbit_parametric_curve(t, m_pt, False)
        for t in theta_values
    ])

    plt.figure(figsize=(8, 6))
    plt.plot(gt_x, gt_y, label="Ground Truth", color="red")
    plt.plot(m_x, m_y, label="Measured", color="black")

    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.title(
        rf"Measured vs. Ground Truth, {plt_prefix}"
    )

    ax = plt.gca()

    limit = 2 * abs(gt_pt.semi_major_axis)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_autoscale_on(False)

    # display earth
    earth = plt.Circle(
        (0, 0),  # Mittelpunkt
        Constants.earth_mean_radius,  # Radius
        color="blue",
        alpha=0.5,
        label="Earth",
    )
    plt.gca().add_patch(earth)

    # display r vectors
    lengths_and_angles = [
        (m_pt.r_1, m_pt.theta_1),
        (m_pt.r_2, m_pt.theta_2),
        (m_pt.r_3, m_pt.theta_3)
    ]
    for i, (length, angle) in enumerate(lengths_and_angles):
        x = length * np.cos(angle)
        y = length * np.sin(angle)
        plt.plot(
            [0, x],
            [0, y],
            color="green",
            label=r"vectors $r_i$" if i == 0 else "_nolegend_",
        )

    plt.grid(True)
    plt.legend()
    plt.legend(loc="upper right")
    plt.tight_layout()

    output_dir = Path(f"orbits_plots/{plt_prefix}")
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.savefig(
        f"orbits_plots/{plt_prefix}/{plt_name}.png",
        dpi=300,
        #bbox_inches="tight"
    )

    if show:
        plt.show()
    plt.close()


def gauss_full_plots(gt_pt: ParametricTrajectory, series_id: int) -> None:
    measured_trajectories: list[ParametricTrajectory] = []
    series_dict = captured_30s_series
    si = SingleFrameMeasurementSeries.from_json(series_dict.get(series_id))

    for j in range(2 , len(si.single_frame_measurements)):
        first = si.single_frame_measurements[0]
        middle = si.single_frame_measurements[j // 2]
        last = si.single_frame_measurements[j]
        complex_gauss_orbit_model = GaussAlgorithm(
            first.time_stamp.determine_ut_s(), middle.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
            first.position_vector, middle.position_vector, last.position_vector,
            first.view_vector.value, middle.view_vector.value, last.view_vector.value
        )
        r_vectors = complex_gauss_orbit_model.gauss_algorithm_select_solution()
        m_pt = ParametricTrajectory.from_eci_measurements(r_vectors)
        measured_trajectories.append(m_pt)

    plot_many_measured(gt_pt, measured_trajectories, rf"gauss_L{series_id}")

def stereo_full_plots(gt_pt: ParametricTrajectory, series_id: int) -> None:
    measured_trajectories: list[ParametricTrajectory] = []
    series_dict = captured_30s_series
    s0 = SingleFrameMeasurementSeries.from_json(series_dict.get(0))
    si = SingleFrameMeasurementSeries.from_json(series_dict.get(series_id))
    d0i = DualFrameMeasurementSeries.create_from_two_single_series(s0, si)

    for j in range(2 , len(d0i.intersection_vectors)):
        first = d0i.intersection_vectors[0]
        middle = d0i.intersection_vectors[j // 2]
        last = d0i.intersection_vectors[j]
        m_pt = ParametricTrajectory.from_eci_measurements([first, middle, last])
        measured_trajectories.append(m_pt)

    plot_many_measured(gt_pt, measured_trajectories, rf"stereo_L0L{series_id}")

def plot_many_measured(gt_pt: ParametricTrajectory, measured_trajectories: list[ParametricTrajectory], plot_prefix: str) -> None:
    for idx, m in enumerate(measured_trajectories):
        plot_parametric_2d(gt_pt, m, plt_prefix=plot_prefix, plt_name= f"{plot_prefix}_{idx}", show=False)
    create_gif(f"orbits_plots/{plot_prefix}")

if __name__ == "__main__":
    ground_truth_dict, plane_normal_vector = get_orbit_ground_truth()
    gt_pt = get_orbit_parametric_trajectory_from_dict(ground_truth_dict)

    #"""
    gauss_full_plots(gt_pt, 7)
    gauss_full_plots(gt_pt, 4)
    gauss_full_plots(gt_pt, -1)
    stereo_full_plots(gt_pt, 1)
    stereo_full_plots(gt_pt, 4)
    stereo_full_plots(gt_pt, 7)
    #create_gif("orbits_plots/gauss_L7")
    #"""
    #print(_sort_img_filenames(["bild_1", "bild_eee_2", "bild_rrr_33", "bild_4"]))

    #m_pt = copy(gt_pt)
    #m_pt.semi_major_axis = 6371
    #m_pt.eccentricity = 1.9
    #m_pt.argument_of_periapsis = pi/2

    #plot_parametric_2d(gt_pt, m_pt)


