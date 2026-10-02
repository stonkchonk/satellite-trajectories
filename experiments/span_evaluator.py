import math
from copy import copy

import matplotlib.pyplot as plt
import numpy as np
from PIL.ImageChops import difference

from algorithms import ParametricTrajectory, GaussAlgorithm, CircularTrajectory, SimplifiedGaussAlgorithm
from common import Code
from earth import UniversalTimeStamp
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from procedures import SingleFrameMeasurementSeries, DualFrameMeasurementSeries, SingleFrameMeasurement
from star_tracker.catalog_parser import UnitVector

class EvaluationResult:

    log_base = 10

    def __init__(self, sma_errors: list[list[float]], ecc_errors: list[list[float]] | None, pln_errors: list[list[float]],
                 x_axis_values: list[float], y_axis_values: list[float],
                 ground_truth_parametric_trajectory: ParametricTrajectory | CircularTrajectory,
                 measured_parametric_trajectories: list[list[ParametricTrajectory | CircularTrajectory]],):
        self.sma_errors = sma_errors
        self.ecc_errors = ecc_errors
        self.pln_errors = pln_errors

        self.ground_truth_parametric_trajectory = ground_truth_parametric_trajectory
        self.measured_parametric_trajectories = measured_parametric_trajectories

        self.x_axis_values = x_axis_values
        self.y_axis_values = y_axis_values

        self._verify_integrity()

    def _verify_integrity(self):
        assert len(self.sma_errors) == len(self.pln_errors) == len(self.y_axis_values)
        if self.ecc_errors is not None:
            assert len(self.sma_errors) == len(self.ecc_errors)
        len_x_axis_values = len(self.x_axis_values)
        for i in self.sma_errors:
            assert len(i) == len_x_axis_values
        if self.ecc_errors is not None:
            for i in self.ecc_errors:
                assert len(i) == len_x_axis_values
        for i in self.pln_errors:
            assert len(i) == len_x_axis_values

    @staticmethod
    def determine_sma_error(ground_truth_sma: float, measured_sma: float) -> float:
        return math.log(abs(ground_truth_sma - abs(measured_sma)) / ground_truth_sma, EvaluationResult.log_base)

    @staticmethod
    def determine_ecc_error(ground_truth_ecc: float, measured_ecc: float) -> float:
        error_value = abs(ground_truth_ecc - abs(measured_ecc))
        if error_value == 0:
            return 0
        else:
            return math.log(error_value, EvaluationResult.log_base)

    @staticmethod
    def plane_normal_deviation_deg(ground_truth_plane_normal: UnitVector, measured_plane_normal: UnitVector) -> float:
        return Code.rad_to_deg(ground_truth_plane_normal.angular_rad_separation(measured_plane_normal))



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


ground_truth_orbit_dict, plane_normal_ground_truth = get_orbit_ground_truth()
gt_pt = ParametricTrajectory.without_valid_init()
gt_pt.semi_major_axis = ground_truth_orbit_dict.get("semi_major_axis_km")
gt_pt.eccentricity = ground_truth_orbit_dict.get("eccentricity")
gt_pt.argument_of_periapsis = Code.deg_to_rad(ground_truth_orbit_dict.get("argument_periapsis_deg"))
gt_pt.plane_normal_vector = UnitVector(plane_normal_ground_truth)


def make_plot(data: list[list[float]], title: str, x_labels: list, y_labels: list) -> None:
    data = np.ma.masked_where(np.equal(data, None), data)

    plt.imshow(data, cmap="viridis", aspect="auto")
    plt.colorbar(label="Wert")
    plt.title(title)

    plt.xlabel("X")
    plt.ylabel("Y")

    plt.xticks(range(len(x_labels)), x_labels)
    plt.yticks(range(len(y_labels)), y_labels)

    plt.show()

def _span_angles(single_frame_measurements: list[SingleFrameMeasurement], default_start_idx: int = 2,
                 deg_or_rad: bool = True) -> list[float]:
    assert len(single_frame_measurements) > default_start_idx
    delta_t = single_frame_measurements[1].time_stamp.determine_ut_s() - single_frame_measurements[0].time_stamp.determine_ut_s()
    delta_arg = (delta_t / Code.orbital_period_s(ground_truth_orbit_dict.get("semi_major_axis_km"))) * 2 * math.pi
    if deg_or_rad:
        delta_arg = Code.rad_to_deg(delta_arg)
    spans: list[float] = []
    for idx in range(0, len(single_frame_measurements[default_start_idx:])):
        spans.append((delta_arg * (idx+default_start_idx)))
    return spans


def _propagation_error(gt_pt: ParametricTrajectory, measured_pt: ParametricTrajectory, orbit_propagation: float) -> float:

    progress_s = gt_pt.period_s * orbit_propagation
    start_true_anomaly = measured_pt.theta_1
    propagated_true_anomaly_gt = gt_pt.new_anomaly_from_time_and_current_anomaly(start_true_anomaly, progress_s)
    propagated_true_anomaly_mt = measured_pt.new_anomaly_from_time_and_current_anomaly(start_true_anomaly, progress_s)
    propagated_eci_position_gt = gt_pt.eci_position_from_true_anomaly(propagated_true_anomaly_gt)
    propagated_eci_position_mt = measured_pt.eci_position_from_true_anomaly(propagated_true_anomaly_mt)
    raw_distance = float(np.linalg.norm(propagated_eci_position_gt - propagated_eci_position_mt))
    return raw_distance / gt_pt.semi_major_axis


def dfm_stereo_errors(full_or_circle: bool = True) -> EvaluationResult:#tuple[list[list[float]], list[list[float]], list[list[float]]]:
    sma_errors: list[list[float]] = []
    ecc_errors: list[list[float]] = []
    pln_errors: list[list[float]] = []
    measured_trajectories: list[list[ParametricTrajectory]] = []

    series_dict = captured_30s_series if full_or_circle else captured_1s_series
    s0 = SingleFrameMeasurementSeries.from_json(series_dict.get(0))

    spans = _span_angles(s0.single_frame_measurements)
    avg_angles: list[float] = []

    for i in range(1, 7+1):
        si = SingleFrameMeasurementSeries.from_json(series_dict.get(i))
        d0i = DualFrameMeasurementSeries.create_from_two_single_series(s0, si)
        print(f"\n->s0{i}")
        print(Code.format_to_geogebra_representation_3d(d0i.intersection_vectors))
        avg_angles.append(sum(d0i.intersection_angles_deg) / len(d0i.intersection_angles_deg))

        length = len(d0i.intersection_vectors)
        sma_errors_i: list[float] = []
        ecc_errors_i: list[float] = []
        pln_errors_i: list[float] = []
        measured_trajectories_i: list[ParametricTrajectory] = []


        for j in range(2, length):
            first = d0i.intersection_vectors[0]
            middle = d0i.intersection_vectors[j // 2]
            last = d0i.intersection_vectors[j]


            try:
                if full_or_circle:
                    pt = ParametricTrajectory.from_eci_measurements([first, middle, last])
                else:
                    ct = CircularTrajectory.from_eci_measurements([first, last])
                    pt = ParametricTrajectory.from_circular_trajectory(ct)

                print(f"--------indices: {i} {j}")
                span_deg = Code.rad_to_deg(pt.theta_3 - pt.theta_1)
                print(f"Span deg: {span_deg}°")
                #print(pt.r_1, pt.r_2, pt.r_3, pt.theta_1, pt.theta_2, pt.theta_3)
                sma_error = EvaluationResult.determine_sma_error(ground_truth_orbit_dict.get("semi_major_axis_km"), pt.semi_major_axis)
                print(f"Sma error: {sma_error}")
                #print("Measured sma: {pt.semi_major_axis}km, Ground truth sma: {ground_truth_orbit_dict.get("semi_major_axis_km")}km")
                #print(f"Measured plane normal: {pt.plane_normal_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
                pln_error = EvaluationResult.plane_normal_deviation_deg(UnitVector(plane_normal_ground_truth), pt.plane_normal_vector)
                print(f"Plane angle error: {pln_error}")
                ecc_error = EvaluationResult.determine_ecc_error(ground_truth_orbit_dict.get("eccentricity"), pt.eccentricity)
                print(f"Ecc error: {ecc_error}")

                sma_errors_i.append(sma_error)
                ecc_errors_i.append(ecc_error)
                pln_errors_i.append(pln_error)
                measured_trajectories_i.append(copy(pt))
            except Exception as e:
                print(f"--------indices: {i} {j}")
                print(f"Cannot determine trajectory: {e}")

        pln_errors.append(pln_errors_i)
        ecc_errors.append(ecc_errors_i)
        sma_errors.append(sma_errors_i)
        measured_trajectories.append(measured_trajectories_i)
    return EvaluationResult(sma_errors, ecc_errors, pln_errors, spans, avg_angles, copy(gt_pt), measured_trajectories)#sma_errors, ecc_errors, pln_errors



def sfm_gauss_errors(full_or_circle: bool = True) -> EvaluationResult:
    sma_errors: list[list[float]] = []
    ecc_errors: list[list[float]] = []
    pln_errors: list[list[float]] = []
    measured_trajectories: list[list[ParametricTrajectory]] = []

    series_dict = captured_30s_series if full_or_circle else captured_1s_series
    spans = _span_angles(SingleFrameMeasurementSeries.from_json(series_dict.get(0)).single_frame_measurements,
                         default_start_idx=2 if full_or_circle else 1)
    plane_offset_angles: list[float] = []

    for i in range(-1, 7+1):
        si = SingleFrameMeasurementSeries.from_json(series_dict.get(i))

        length = len(si.single_frame_measurements)
        sma_errors_i: list[float] = []
        ecc_errors_i: list[float] = []
        pln_errors_i: list[float] = []
        measured_trajectories_i: list[ParametricTrajectory] = []

        angle_between_observer_and_plane_mid_measurements = Code.rad_to_deg(
            abs(math.pi / 2 - Code.angular_separation_of_two_vectors_rad(
                plane_normal_ground_truth,
                si.single_frame_measurements[length // 2].position_vector
            ))
        )
        plane_offset_angles.append(angle_between_observer_and_plane_mid_measurements)

        for j in range(2 if full_or_circle else 1, length):
            first = si.single_frame_measurements[0]
            middle = si.single_frame_measurements[j // 2]
            last = si.single_frame_measurements[j]

            if full_or_circle:
                complex_gauss_orbit_model = GaussAlgorithm(
                    first.time_stamp.determine_ut_s(), middle.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
                    first.position_vector, middle.position_vector, last.position_vector,
                    first.view_vector.value, middle.view_vector.value, last.view_vector.value
                )
                r_vectors = complex_gauss_orbit_model.gauss_algorithm_select_solution()
            else:
                simple_gauss_orbit_model = SimplifiedGaussAlgorithm(first.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
                                                                    first.position_vector, last.position_vector,
                                                                    first.view_vector.value, last.view_vector.value)
                r_vectors = simple_gauss_orbit_model.determine_solution()

            try:
                if full_or_circle:
                    pt = ParametricTrajectory.from_eci_measurements(r_vectors)
                else:
                    ct = CircularTrajectory.from_eci_measurements(r_vectors)
                    pt = ParametricTrajectory.from_circular_trajectory(ct)
                print(f"--------indices: {i} {j}")
                span_deg = Code.rad_to_deg(pt.theta_3 - pt.theta_1)
                print(f"Span deg: {span_deg}°")
                # print(pt.r_1, pt.r_2, pt.r_3, pt.theta_1, pt.theta_2, pt.theta_3)
                sma_error = EvaluationResult.determine_sma_error(ground_truth_orbit_dict.get("semi_major_axis_km"), pt.semi_major_axis)
                print(f"Sma error: {sma_error}")
                # print("Measured sma: {pt.semi_major_axis}km, Ground truth sma: {ground_truth_orbit_dict.get("semi_major_axis_km")}km")
                # print(f"Measured plane normal: {pt.plane_normal_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
                pln_error = EvaluationResult.plane_normal_deviation_deg(UnitVector(plane_normal_ground_truth), pt.plane_normal_vector)
                print(f"Plane angle error: {pln_error}")
                ecc_error = EvaluationResult.determine_ecc_error(ground_truth_orbit_dict.get("eccentricity"), pt.eccentricity)
                print(f"Ecc error: {ecc_error}")

                sma_errors_i.append(sma_error)
                ecc_errors_i.append(ecc_error)
                pln_errors_i.append(pln_error)
                measured_trajectories_i.append(copy(pt))
            except Exception as e:
                print(f"--------indices: {i} {j}")
                print(f"Cannot determine trajectory: {e}")

        pln_errors.append(pln_errors_i)
        ecc_errors.append(ecc_errors_i)
        sma_errors.append(sma_errors_i)
        measured_trajectories.append(measured_trajectories_i)
    return EvaluationResult(sma_errors, ecc_errors, pln_errors, spans, plane_offset_angles, copy(gt_pt), measured_trajectories)


def propagation_errors(ground_truth_trajectory: ParametricTrajectory,
                       measured_trajectories: list[list[ParametricTrajectory]]) -> list[list[float]]:
    propagation_errors: list[list[float]] = []
    for measured_trajectories_i in measured_trajectories:
        propagation_errors_i: list[float] = []
        for measured_trajectory in measured_trajectories_i:
            if measured_trajectory.eccentricity < 1:
                propagation_errors_i.append(
                    _propagation_error(ground_truth_trajectory, measured_trajectory, 1)
                )
            else:
                propagation_errors_i.append(-1)
        propagation_errors.append(propagation_errors_i)
    return propagation_errors




evaluator_result = sfm_gauss_errors(full_or_circle=False)
#evaluator_result = dfm_stereo_errors(full_or_circle=False)
#print(evaluator_result.sma_errors)
#print(ecc_errors)
#print(pln_errors)
print("pln gt",plane_normal_ground_truth)


make_plot(evaluator_result.sma_errors, "sma_errors", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
make_plot(evaluator_result.ecc_errors, "ecc_errors", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
make_plot(evaluator_result.pln_errors, "plane normal deviation", evaluator_result.x_axis_values, evaluator_result.y_axis_values)

#propagations = [i/10 for i in range(100)]
#errors = []
#for p in propagations:
#    error = _propagation_error(gt_pt, measured_pt, p)
#    errors.append(np.array([p, error]))

#print(Code.format_to_geogebra_representation_2d(errors))
make_plot(propagation_errors(evaluator_result.ground_truth_parametric_trajectory, evaluator_result.measured_parametric_trajectories), "propagation error", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
#print(propagation_error(evaluator_result.ground_truth_parametric_trajectory, evaluator_result.measured_parametric_trajectories))


