
from common import Params, Constants
from earth import UniversalTimeStamp
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from procedures import CameraCalibration, ObserverPosition, SingleFrameMeasurementSeries
from se_automation import WindowController

if __name__ == "__main__":
    ground_truth_orbit_dict, plane_normal_ground_truth = get_orbit_ground_truth()
    altitude = int(ground_truth_orbit_dict["semi_major_axis_km"] - Constants.earth_mean_radius)
    print("altitude km:", altitude)
    measurement_series_name = f"sma_test_{altitude}km"

    WindowController.initial_setup(cleanse_old_screenshots=True)
    calibrator = CameraCalibration(execute_camera_setup=True)
    initial_time_stamp = UniversalTimeStamp.from_string("2000.01.01 20:03:00") #tz

    observer_pos = ObserverPosition(
        (-27.911902, -62.468913), 127 #L5
    )

    calibrator.full_camera_calibration_procedure(override_time_stamp=initial_time_stamp,
                                                 override_lat_lon=observer_pos.coordinates,
                                                 override_sea_altitude=observer_pos.altitude_m)

    series = SingleFrameMeasurementSeries(calibrator)
    series.observer_position = observer_pos
    series.ground_truth_orbit = ground_truth_orbit_dict
    steps = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    series.create_measurement_series(steps)

    try:
        existing_series = SingleFrameMeasurementSeries.from_json(measurement_series_name, directory=Params.single_frame_different_sma_dir)
        series.flush_to_file(measurement_series_name + "_1", directory=Params.single_frame_different_sma_dir)
    except:
        series.flush_to_file(measurement_series_name, directory=Params.single_frame_different_sma_dir)
    print("done")