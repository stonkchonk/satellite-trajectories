import numpy as np

from algorithms import SimplifiedGaussAlgorithm, ParametricTrajectory, GaussAlgorithm
from common import Code
from earth import UniversalTimeStamp
from procedures import CameraCalibration, SingleFrameMeasurementSeries
from se_automation import WindowController
from artificial_satellite_setup import get_orbit_ground_truth
from star_tracker.catalog_parser import UnitVector

if __name__ == "__main__":
    location_mt_pi_measurements = "location_mt_pi_measurements_larger_step.txt"
    perform_measurements = True

    if perform_measurements:
        WindowController.initial_setup(cleanse_old_screenshots=True)
        calibrator = CameraCalibration(execute_camera_setup=True)
        initial_time_stamp = UniversalTimeStamp(2026, 9, 4, 19, 23, 0) #2026, 9, 4, 19, 28, 2

        position_mt_pi = (-27.68216667, -68.78558333)
        altitude_mt_pi = 6460

        calibrator.full_camera_calibration_procedure(override_time_stamp=initial_time_stamp, override_lat_lon=position_mt_pi,
                                                     override_sea_altitude=altitude_mt_pi)

        series_mt_pi = SingleFrameMeasurementSeries(calibrator)
        series_mt_pi.create_measurement_series_with_camera_recalibration(60)

        Code.write_text_file(location_mt_pi_measurements, series_mt_pi.__str__())
    else:
        series_mt_pi = SingleFrameMeasurementSeries.from_string(Code.read_text_file(location_mt_pi_measurements))


    length = len(series_mt_pi.single_frame_measurements)
    print("-->", length)

    for i in range(1, length):
        first = series_mt_pi.single_frame_measurements[0]
        last = series_mt_pi.single_frame_measurements[i]

        simple_gauss_orbit_model = SimplifiedGaussAlgorithm(
            first.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
            first.position_vector, last.position_vector,
            first.view_vector.value, last.view_vector.value
        )

        r_vectors = simple_gauss_orbit_model.determine_solution()
        plane_vector = ParametricTrajectory.determine_orbital_plane_vector(r_vectors[0], r_vectors[1])
        ground_truth_dict, plane_normal_ground_truth = get_orbit_ground_truth()

        plane_vectors_angular_separation = plane_vector.angular_rad_separation(UnitVector(plane_normal_ground_truth))
        print(f"--------index: {i}")
        print(f"Measured sma: {np.linalg.norm(r_vectors[0])}km, Ground truth sma: {ground_truth_dict.get("semi_major_axis_km")}km")
        print(f"Measured plane normal: {plane_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
        print(f"Measured vs ground truth plane angle: {Code.rad_to_deg(plane_vectors_angular_separation)}°")

    print("\n\n\n\n\n\n\n")

    for i in range(2, length):
        first = series_mt_pi.single_frame_measurements[0]
        middle = series_mt_pi.single_frame_measurements[i // 2]
        last = series_mt_pi.single_frame_measurements[i]

        complex_gauss_orbit_model = GaussAlgorithm(
            first.time_stamp.determine_ut_s(), middle.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
            first.position_vector, middle.position_vector, last.position_vector,
            first.view_vector.value, middle.view_vector.value, last.view_vector.value
        )

        r_vectors = complex_gauss_orbit_model.gauss_algorithm_select_solution()

        pt = ParametricTrajectory.from_eci_measurements(r_vectors)

        ground_truth_dict, plane_normal_ground_truth = get_orbit_ground_truth()


        plane_vectors_angular_separation = pt.plane_normal_vector.angular_rad_separation(UnitVector(plane_normal_ground_truth))

        print(f"--------index: {i}")
        print(pt.r_1, pt.r_2, pt.r_3, pt.theta_1, pt.theta_2, pt.theta_3)
        print(f"Measured sma: {pt.semi_major_axis}km, Ground truth sma: {ground_truth_dict.get("semi_major_axis_km")}km")
        print(f"Measured plane normal: {pt.plane_normal_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
        print(f"Measured vs ground truth plane angle: {Code.rad_to_deg(plane_vectors_angular_separation)}°")
        print(f"Eccentricity: {pt.eccentricity}, Arg of peri: {pt.argument_of_periapsis}")




