import math

import numpy as np

from common import Constants, Code


class EarthCenteredInertial:
    def __init__(self):
        pass

    @staticmethod
    def determine_j0(year: int, month: int, day: int) -> float:
        """
        :param year: 1901 <= year <= 2099
        :param month: 1<= month <= 12
        :param day: 1 <= day <= 31
        :return: J0
        """
        s1 = 367*year
        s2 = -int(7 * (year + int((month + 9) / 12)) / 4)
        s3 = int((275 * month) / 9)
        s4 = day + 1721013.5
        return s1 + s2 + s3 + s4

    @staticmethod
    def determine_ut_hr(hours: int, minutes: int, seconds: int) -> float:
        """
        :param hours: 0 <= hours <= 23
        :param minutes: 0 <= minutes <= 59
        :param seconds: 0 <= seconds <= 59
        """
        return hours + minutes / 60 + seconds / 3600

    @staticmethod
    def determine_t0(j0: float) -> float:
        """
        Determines T0 for the J2000 epoch.
        :param j0: J0
        :return: T0
        """
        return (j0 - 2451545.0) / 36525.0

    @staticmethod
    def determine_theta_g0_deg(t0: float) -> float:
        """
        Determines theta_g0 (initial greenwich meridian angle) for a certain T0 in the J2000 epoch.
        :param t0: T0
        :return: theta_g0 in degrees
        """
        angle = 100.4606184 + 36000.77004 * t0 + 0.000387933 * t0**2 - 2.583e-8 * t0**3
        return angle % 360

    @staticmethod
    def determine_theta_g(ut_hr: float, theta_g0_deg: float) -> float:
        """
        Determines theta_g (current greenwich meridian angle) for a certain UT.
        :param ut_hr:
        :return: theta_g in degrees
        """
        return theta_g0_deg + 360.98564724 * ut_hr / 24.0

    @staticmethod
    def determine_eci_longitude(ecef_longitude_deg: float, theta_g_deg: float) -> float:
        return (theta_g_deg + ecef_longitude_deg) % 360

    @staticmethod
    def determine_eci_longitude_from_time(ecef_longitude_deg: float, year: int, month: int, day: int, hours: int, minutes: int, seconds: int) -> float:
        j0 = EarthCenteredInertial.determine_j0(year, month, day)
        t0 = EarthCenteredInertial.determine_t0(j0)
        theta_g0_deg = EarthCenteredInertial.determine_theta_g0_deg(t0)
        ut_hr = EarthCenteredInertial.determine_ut_hr(hours, minutes, seconds)
        theta_d_deg = EarthCenteredInertial.determine_theta_g(ut_hr, theta_g0_deg)
        return EarthCenteredInertial.determine_eci_longitude(ecef_longitude_deg, theta_d_deg)

    @staticmethod
    def determine_vector_from_lat_lon_alt(latitude_rad: float, longitude_rad: float, altitude_km: float) -> np.ndarray:
        a = Constants.earth_equatorial_rad_km
        b = Constants.earth_polar_rad_km
        n = (a ** 2) / math.sqrt((a ** 2) * math.cos(latitude_rad) ** 2 + (b ** 2) * math.sin(latitude_rad) ** 2)
        x = (n + altitude_km) * math.cos(latitude_rad) * math.cos(longitude_rad)
        y = (n + altitude_km) * math.cos(latitude_rad) * math.sin(longitude_rad)
        z = (n * (b ** 2) / (a ** 2) + altitude_km) * math.sin(latitude_rad)
        return np.array([x, y, z])

    @staticmethod
    def determine_eci_vector_from_lat_lon_alt(ecef_latitude_deg: float, ecef_longitude_deg: float, altitude_km: float,
                                              year: int, month: int, day: int, hours: int, minutes: int, seconds: int):
        eci_longitude_deg = EarthCenteredInertial.determine_eci_longitude_from_time(ecef_longitude_deg, year,
                                                                                    month, day, hours, minutes, seconds)
        return EarthCenteredInertial.determine_vector_from_lat_lon_alt(Code.deg_to_rad(ecef_latitude_deg),
                                                                        Code.deg_to_rad(eci_longitude_deg), altitude_km)



'''
class EarthCenteredEarthFixed:
    def __init__(self):
        pass

    @staticmethod
    def ecef_vector_from_lat_lon_alt(latitude_rad: float, longitude_rad: float, altitude_km: float) -> np.ndarray:
        a = Constants.earth_equatorial_rad_km
        b = Constants.earth_polar_rad_km
        n = (a ** 2) / math.sqrt((a**2) * math.cos(latitude_rad)**2 + (b**2) * math.sin(latitude_rad)**2)
        x = (n + altitude_km) * math.cos(latitude_rad) * math.cos(longitude_rad)
        y = (n + altitude_km) * math.cos(latitude_rad) * math.sin(longitude_rad)
        z = (n * (b**2) / (a**2) + altitude_km) * math.sin(latitude_rad)
        return np.array([x, y, z])
'''