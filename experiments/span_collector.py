import numpy as np

from algorithms import SimplifiedGaussAlgorithm, ParametricTrajectory, GaussAlgorithm
from common import Code
from earth import UniversalTimeStamp
from procedures import CameraCalibration, SingleFrameMeasurementSeries, ObserverPosition
from se_automation import WindowController
from artificial_satellite_setup import get_orbit_ground_truth
from star_tracker.catalog_parser import UnitVector

if __name__ == "__main__":
    forward_seconds = 1
    measurement_series_name = f"zenith_failure_{forward_seconds}s"
    ground_truth_orbit_dict, plane_normal_ground_truth = get_orbit_ground_truth()
    perform_measurements = True
    with_recalibration = False
    calculate_orbits = True

    if perform_measurements:
        WindowController.initial_setup(cleanse_old_screenshots=True)
        calibrator = CameraCalibration(execute_camera_setup=True)
        initial_time_stamp = UniversalTimeStamp.from_string("2000.01.01 20:03:00")
        # Observation times
        # start:    "2000.01.01 19:58:00"
        # middle:   "2000.01.01 20:03:00"
        # end:      "2000.01.01 20:08:00"

        observer_pos = ObserverPosition(
            (-27.257356, -64.963269), 313
        )
        # Locations in South America
        # zenith / numeric failure: (-27.257356, -64.963269), 313
        # 0: (-27.301281, -63.939256), 157
        # 1: (-27.339896, -63.847839), 153
        # 2: (-27.378452, -63.756358), 155
        # 3: (-27.455384, -63.573205), 149
        # 4: (-27.608528, -63.206133), 143
        # 5: (-27.911902, -62.468913), 127
        # 6: (-28.506740, -60.982091), 64
        # 7: (-29.646743, -57.958463), 64

        calibrator.full_camera_calibration_procedure(override_time_stamp=initial_time_stamp,
                                                     override_lat_lon=observer_pos.coordinates,
                                                     override_sea_altitude=observer_pos.altitude_m)

        series = SingleFrameMeasurementSeries(calibrator)
        series.observer_position = observer_pos
        series.ground_truth_orbit = ground_truth_orbit_dict
        if with_recalibration:
            series.create_measurement_series_with_camera_recalibration(forward_seconds)
        else:
            steps = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            series.create_measurement_series(steps)

        try:
            existing_series = SingleFrameMeasurementSeries.from_json(measurement_series_name)
            series.flush_to_file(measurement_series_name + "_1")
        except:
            series.flush_to_file(measurement_series_name)

    else:
        series = SingleFrameMeasurementSeries.from_json(measurement_series_name)


    length = len(series.single_frame_measurements)
    print("-->length: ", length)

    position_vectors = [sfm.position_vector for sfm in series.single_frame_measurements]
    view_vectors = [sfm.view_vector.value for sfm in series.single_frame_measurements]
    print(Code.format_to_geogebra_representation_3d(position_vectors))
    print(Code.format_to_geogebra_representation_3d(view_vectors))

    print("\n\n\n\n\n\n\n")


    if calculate_orbits:
        for i in range(1, length):
            first = series.single_frame_measurements[0]
            last = series.single_frame_measurements[i]

            simple_gauss_orbit_model = SimplifiedGaussAlgorithm(
                first.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
                first.position_vector, last.position_vector,
                first.view_vector.value, last.view_vector.value
            )

            r_vectors = simple_gauss_orbit_model.determine_solution()
            plane_vector = ParametricTrajectory.determine_orbital_plane_vector(r_vectors[0], r_vectors[1])

            plane_vectors_angular_separation = plane_vector.angular_rad_separation(UnitVector(plane_normal_ground_truth))
            print(f"--------index: {i}")
            print(f"Measured sma: {np.linalg.norm(r_vectors[0])}km, Ground truth sma: {ground_truth_orbit_dict.get("semi_major_axis_km")}km")
            print(f"Measured plane normal: {plane_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
            print(f"Measured vs ground truth plane angle: {Code.rad_to_deg(plane_vectors_angular_separation)}°")

        """
        print("\n\n\n\n\n\n\n")

        for i in range(2, length):
            first = series.single_frame_measurements[0]
            middle = series.single_frame_measurements[i // 2]
            last = series.single_frame_measurements[i]

            complex_gauss_orbit_model = GaussAlgorithm(
                first.time_stamp.determine_ut_s(), middle.time_stamp.determine_ut_s(), last.time_stamp.determine_ut_s(),
                first.position_vector, middle.position_vector, last.position_vector,
                first.view_vector.value, middle.view_vector.value, last.view_vector.value
            )


            r_vectors = complex_gauss_orbit_model.gauss_algorithm_select_solution()

            pt = ParametricTrajectory.from_eci_measurements(r_vectors)

            plane_vectors_angular_separation = pt.plane_normal_vector.angular_rad_separation(UnitVector(plane_normal_ground_truth))

            print(f"--------index: {i}")
            print(pt.r_1, pt.r_2, pt.r_3, pt.theta_1, pt.theta_2, pt.theta_3)
            print(f"Measured sma: {pt.semi_major_axis}km, Ground truth sma: {ground_truth_orbit_dict.get("semi_major_axis_km")}km")
            print(f"Measured plane normal: {pt.plane_normal_vector.value}, Ground truth plane normal: {plane_normal_ground_truth}")
            print(f"Measured vs ground truth plane angle: {Code.rad_to_deg(plane_vectors_angular_separation)}°")
            print(f"Eccentricity: {pt.eccentricity}, Arg of peri: {pt.argument_of_periapsis}")
        """


        


