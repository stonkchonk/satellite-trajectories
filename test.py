from common import Code
from earth import EarthCenteredInertial
from procedures import SingleFrameMeasurement, SingleFrameMeasurementSeries, DualFrameMeasurementSeries, \
    ObserverPosition
from experiments.artificial_satellite_setup import get_orbit_ground_truth

series_1 = SingleFrameMeasurementSeries.from_string("{2026.06.19 15:29:11; [-0.08651561261318731, 0.16680037829049002, -0.9821877023137249]; [963.4927582237676, -5543.4551002352, -2993.718114760807]}|{2026.06.19 15:29:36; [-0.03404263959647167, 0.17026876624520848, -0.9848094465076171]; [973.597030777788, -5541.689414351364, -2993.718114760807]}|{2026.06.19 15:29:61; [0.0193038638395505, 0.17444263813859337, -0.9844780987102313]; [983.6980676466454, -5539.905311030284, -2993.718114760807]}")
series_2 = SingleFrameMeasurementSeries.from_string("{2026.06.19 15:29:11; [-0.3121113658618864, 0.13524532577201687, -0.940369713015391]; [1867.9416617218499, -5481.940794697743, -2663.7315448129057]}|{2026.06.19 15:29:36; [-0.2723007497227346, 0.1396787010583595, -0.9520200429460958]; [1877.9322890393673, -5478.526375399763, -2663.7315448129057]}|{2026.06.19 15:29:61; [-0.23109796334574442, 0.14495163721205792, -0.9620721148682113]; [1887.9166751734663, -5475.093748582709, -2663.7315448129057]}")

observer_pos = ObserverPosition(
    (-27.68216667, -68.78558333),
    6460
)

"""
series_1.observer_position = observer_pos
series_1.ground_truth_orbit = get_orbit_ground_truth()[0]
altitude = 3980
series = SingleFrameMeasurementSeries.from_json("ag_an_1_30s")
print(3)
for sfm in series.single_frame_measurements:
    ts = sfm.time_stamp
    alt = series.observer_position.altitude_m
    lat, lon = series.observer_position.coordinates
    new_pos_vector = EarthCenteredInertial.determine_eci_vector_from_lat_lon_alt(lat, lon,altitude/1000, ts)
    print(new_pos_vector, sfm.position_vector)
    sfm.position_vector = new_pos_vector
    print(new_pos_vector, sfm.position_vector, "<--")

for sfm in series.single_frame_measurements:
    print(sfm.position_vector, "<-----")

series.flush_to_file("ag_an_1_30s_zzzzzz")
"""
# Locations in South America
# Mt Pi 1: -27.68216667, -68.78558333, 6460
# Mt Pi 2: -27.7231285,-68.8761221, 5310
# Lag Neg 1: -27.628442, -68.590410, 4710
# Ch An 1: -27.8206424,-69.1635205, 4450
# Ag An 1: -27.3276682,-68.071221, 3980
# Ch An 2: -28.2343585,-70.290287, 1660
# Rio Sm 1: -26.3125282,-65.9406141, 1710

series_names = [
    "mt_pi_1_30s",
    "mt_pi_2_30s",
    "lag_neg_1_30s",
    "ch_an_1_30s",
    "ch_an_2_30s",
    "ag_an_1_30s",
    "lag_sal_1_30s",
    "mt_pi_3_30s",
    "mt_pi_1_1s",
]

view_vectors = []
for name in series_names:
    series = SingleFrameMeasurementSeries.from_json(name)
    view_vectors = []
    for sfm in series.single_frame_measurements:
        view_vectors.append(sfm.view_vector.value)
    gg_str = Code.format_to_geogebra_representation(view_vectors)
    print(name)
    print(f"{gg_str}")
    print("\n")


