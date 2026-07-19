from copy import copy

import numpy as np

from algorithms import ParametricTrajectory, GaussAlgorithm
from common import Code, Params
from procedures import SingleFrameMeasurement, SingleFrameMeasurementSeries, DualFrameMeasurementSeries


series_1 = SingleFrameMeasurementSeries.from_string("{2026.06.19 15:29:11; [-0.08651561261318731, 0.16680037829049002, -0.9821877023137249]; [963.4927582237676, -5543.4551002352, -2993.718114760807]}|{2026.06.19 15:29:36; [-0.03404263959647167, 0.17026876624520848, -0.9848094465076171]; [973.597030777788, -5541.689414351364, -2993.718114760807]}|{2026.06.19 15:29:61; [0.0193038638395505, 0.17444263813859337, -0.9844780987102313]; [983.6980676466454, -5539.905311030284, -2993.718114760807]}")
series_2 = SingleFrameMeasurementSeries.from_string("{2026.06.19 15:29:11; [-0.3121113658618864, 0.13524532577201687, -0.940369713015391]; [1867.9416617218499, -5481.940794697743, -2663.7315448129057]}|{2026.06.19 15:29:36; [-0.2723007497227346, 0.1396787010583595, -0.9520200429460958]; [1877.9322890393673, -5478.526375399763, -2663.7315448129057]}|{2026.06.19 15:29:61; [-0.23109796334574442, 0.14495163721205792, -0.9620721148682113]; [1887.9166751734663, -5475.093748582709, -2663.7315448129057]}")
#dfms = DualFrameMeasurementSeries.create_from_two_single_series(series_1, series_2)
#for v in dfms.intersection_vectors:
#    print(np.linalg.norm(v))
#measured_eci_vectors = dfms.intersection_vectors
#print(Code.format_to_geogebra_representation(measured_eci_vectors))
#trajectory = ParametricTrajectory.from_eci_measurements(measured_eci_vectors)
#print(f"arg peri: {trajectory.argument_of_periapsis}, sma: {trajectory.semi_major_axis}, ecc: {trajectory.eccentricity}")

sfm = series_1.single_frame_measurements

t = []#[0, 118.1, 237.58]
R = []#[np.array([3489.8, 3430.2, 4078.5]), np.array([3460.1, 3460.1, 4078.5]), np.array([3429.9, 3490.1, 4078.5])]
pd = []#[np.array([0.71643, 0.68074, -0.15270]), np.array([0.56897, 0.79531, -0.20917]), np.array([0.41841, 0.87007, -0.26059])]

for i in [0, 1, 2]:
    print(sfm[i].time_stamp)
    t.append(copy(sfm[i].time_stamp).determine_ut_s())
    R.append(sfm[i].position_vector)
    pd.append(sfm[i].view_vector.value)

gauss_algo = GaussAlgorithm(t[0], t[1], t[2], R[0], R[1], R[2], pd[0], pd[1], pd[2])
measured_eci_vectors = gauss_algo.gauss_algorithm_select_solution()
gauss_trajectory = ParametricTrajectory.from_eci_measurements(measured_eci_vectors)
print(f"Gauss: arg peri: {gauss_trajectory.argument_of_periapsis}, sma: {gauss_trajectory.semi_major_axis}, ecc: {gauss_trajectory.eccentricity}")
