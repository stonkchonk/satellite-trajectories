import math

import matplotlib.pyplot as plt

from algorithms import ParametricTrajectory, GaussAlgorithm
from common import Code
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from procedures import SingleFrameMeasurementSeries, DualFrameMeasurementSeries, SingleFrameMeasurement
from star_tracker.catalog_parser import UnitVector

class EvaluationResult:

    log_base = 10

    def __init__(self, sma_errors: list[list[float]], ecc_errors: list[list[float]], pln_errors: list[list[float]],
                 x_axis_values: list[float], y_axis_values: list[float]):
        self.sma_errors = sma_errors
        self.ecc_errors = ecc_errors
        self.pln_errors = pln_errors

        self.x_axis_values = x_axis_values
        self.y_axis_values = y_axis_values

        self._verify_integrity()

    def _verify_integrity(self):
        assert len(self.sma_errors) == len(self.ecc_errors) == len(self.pln_errors) == len(self.y_axis_values)
        len_x_axis_values = len(self.x_axis_values)
        for i in self.sma_errors:
            assert len(i) == len_x_axis_values
        for i in self.ecc_errors:
            assert len(i) == len_x_axis_values
        for i in self.pln_errors:
            assert len(i) == len_x_axis_values

    @staticmethod
    def determine_sma_error(ground_truth_sma: float, measured_sma: float) -> float:
        return math.log(abs(ground_truth_sma - abs(measured_sma)) / ground_truth_sma, EvaluationResult.log_base)

    @staticmethod
    def determine_ecc_error(ground_truth_ecc: float, measured_ecc: float) -> float:
        return math.log(abs(ground_truth_ecc - abs(measured_ecc)), EvaluationResult.log_base)

    @staticmethod
    def plane_normal_deviation_deg(ground_truth_plane_normal: UnitVector, measured_plane_normal: UnitVector) -> float:
        return math.log(Code.rad_to_deg(ground_truth_plane_normal.angular_rad_separation(measured_plane_normal)), EvaluationResult.log_base

                        )



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
ground_truth_orbit_dict, plane_normal_ground_truth = get_orbit_ground_truth()

def determine_sma_error(ground_truth_sma: float, measured_sma: float) -> float:
    return math.log(abs(ground_truth_sma - abs(measured_sma)) / ground_truth_sma, 10)

def determine_ecc_error(ground_truth_ecc: float, measured_ecc: float) -> float:
    return math.log(abs(ground_truth_ecc - abs(measured_ecc)), 10)

def plane_normal_deviation_deg(ground_truth_plane_normal: UnitVector, measured_plane_normal: UnitVector) -> float:
    return math.log(Code.rad_to_deg(ground_truth_plane_normal.angular_rad_separation(measured_plane_normal)), 10)

def make_plot(data: list[list[float]], title: str, x_labels: list, y_labels: list) -> None:
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




def dfm_stereo_errors() -> EvaluationResult:#tuple[list[list[float]], list[list[float]], list[list[float]]]:
    sma_errors: list[list[float]] = []
    ecc_errors: list[list[float]] = []
    pln_errors: list[list[float]] = []

    s0 = SingleFrameMeasurementSeries.from_json(captured_30s_series.get(0))

    spans = _span_angles(s0.single_frame_measurements)
    avg_angles: list[float] = []

    for i in range(1, 7+1):
        si = SingleFrameMeasurementSeries.from_json(captured_30s_series.get(i))
        d0i = DualFrameMeasurementSeries.create_from_two_single_series(s0, si)
        print(f"\n->s0{i}")
        print(Code.format_to_geogebra_representation_3d(d0i.intersection_vectors))
        avg_angles.append(sum(d0i.intersection_angles_deg) / len(d0i.intersection_angles_deg))

        length = len(d0i.intersection_vectors)
        sma_errors_i: list[float] = []
        ecc_errors_i: list[float] = []
        pln_errors_i: list[float] = []

        for j in range(2, length):
            first = d0i.intersection_vectors[0]
            middle = d0i.intersection_vectors[j // 2]
            last = d0i.intersection_vectors[j]


            try:
                pt = ParametricTrajectory.from_eci_measurements([first, middle, last])

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
            except Exception as e:
                print(f"--------indices: {i} {j}")
                print(f"Cannot determine trajectory: {e}")

        pln_errors.append(pln_errors_i)
        ecc_errors.append(ecc_errors_i)
        sma_errors.append(sma_errors_i)
    return EvaluationResult(sma_errors, ecc_errors, pln_errors, spans, avg_angles)#sma_errors, ecc_errors, pln_errors



def sfm_gauss_errors() -> EvaluationResult:
    sma_errors: list[list[float]] = []
    ecc_errors: list[list[float]] = []
    pln_errors: list[list[float]] = []

    spans = _span_angles(SingleFrameMeasurementSeries.from_json(captured_30s_series.get(0)).single_frame_measurements)
    plane_offset_angles: list[float] = []

    for i in range(-1, 7+1):
        si = SingleFrameMeasurementSeries.from_json(captured_30s_series.get(i))

        length = len(si.single_frame_measurements)
        sma_errors_i: list[float] = []
        ecc_errors_i: list[float] = []
        pln_errors_i: list[float] = []

        angle_between_observer_and_plane_mid_measurements = Code.rad_to_deg(
            abs(math.pi / 2 - Code.angular_separation_of_two_vectors_rad(
                plane_normal_ground_truth,
                si.single_frame_measurements[length // 2].position_vector
            ))
        )
        plane_offset_angles.append(angle_between_observer_and_plane_mid_measurements)

        for j in range(2, length):
            first = si.single_frame_measurements[0]
            middle = si.single_frame_measurements[j // 2]
            last = si.single_frame_measurements[j]

            complex_gauss_orbit_model = GaussAlgorithm(
                first.time_stamp.determine_ut_s(), middle.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
                first.position_vector, middle.position_vector, last.position_vector,
                first.view_vector.value, middle.view_vector.value, last.view_vector.value
            )

            r_vectors = complex_gauss_orbit_model.gauss_algorithm_select_solution()
            try:
                pt = ParametricTrajectory.from_eci_measurements(r_vectors)
                print(f"--------indices: {i} {j}")
                span_deg = Code.rad_to_deg(pt.theta_3 - pt.theta_1)
                print(f"Span deg: {span_deg}°")
                # print(pt.r_1, pt.r_2, pt.r_3, pt.theta_1, pt.theta_2, pt.theta_3)
                sma_error = determine_sma_error(ground_truth_orbit_dict.get("semi_major_axis_km"), pt.semi_major_axis)
                print(f"Sma error: {sma_error}")
                # print("Measured sma: {pt.semi_major_axis}km, Ground truth sma: {ground_truth_orbit_dict.get("semi_major_axis_km")}km")
                # print(f"Measured plane normal: {pt.plane_normal_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
                pln_error = plane_normal_deviation_deg(UnitVector(plane_normal_ground_truth), pt.plane_normal_vector)
                print(f"Plane angle error: {pln_error}")
                ecc_error = determine_ecc_error(ground_truth_orbit_dict.get("eccentricity"), pt.eccentricity)
                print(f"Ecc error: {ecc_error}")

                sma_errors_i.append(sma_error)
                ecc_errors_i.append(ecc_error)
                pln_errors_i.append(pln_error)
            except Exception as e:
                print(f"--------indices: {i} {j}")
                print(f"Cannot determine trajectory: {e}")

        pln_errors.append(pln_errors_i)
        ecc_errors.append(ecc_errors_i)
        sma_errors.append(sma_errors_i)
    return EvaluationResult(sma_errors, ecc_errors, pln_errors, spans, plane_offset_angles)



evaluator_result = sfm_gauss_errors()
#evaluator_result = dfm_stereo_errors()
#print(evaluator_result.sma_errors)
#print(ecc_errors)
#print(pln_errors)
make_plot(evaluator_result.sma_errors, "sma_errors", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
make_plot(evaluator_result.ecc_errors, "ecc_errors", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
make_plot(evaluator_result.pln_errors, "plane normal deviation", evaluator_result.x_axis_values, evaluator_result.y_axis_values)
