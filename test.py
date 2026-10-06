import math

import numpy as np

from algorithms import TrueAnomalyAndTime, ParametricTrajectory
from common import Code, Params, Constants
from earth import EarthCenteredInertial
from procedures import SingleFrameMeasurement, SingleFrameMeasurementSeries, DualFrameMeasurementSeries, \
    ObserverPosition
from experiments.artificial_satellite_setup import get_orbit_ground_truth
from star_tracker.catalog_parser import UnitVector
from star_tracker.precession import Precession

l1 = [1,2,3]
l2 = [1,2,4]
l3 = [1,2,5]
l4 = [1,2,3]
s=[l1, l2]
print(l1 in s)
print(l2 in s)
print(l3 in s)
print(l4 in s)