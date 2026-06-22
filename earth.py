import math

import numpy as np

from common import Constants, Code

class UniversalTimeStamp:
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int, second: int, restrain: bool = True):
        assert 1901 <= year <= 2099
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        if restrain:
            assert 1 <= hour <= 23
            assert 1 <= minute <= 59
            assert 1 <= second <= 59
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    def __str__(self):
        return (
            f"{self.year:04d}.{self.month:02d}.{self.day:02d} "
            f"{self.hour:02d}:{self.minute:02d}:{self.second}"
        )

    @classmethod
    def from_string(cls, s: str, restrain: bool = True) -> "UniversalTimeStamp":
        try:
            date_part, time_part = s.split(" ")
            year, month, day = map(int, date_part.split("."))

            #time_part = time_part[:-3]
            hour, minute, second = map(int, time_part.split(":"))

            return cls(year, month, day, hour, minute, second, restrain)

        except Exception as e:
            raise ValueError(f"Invalid timestamp format: '{s}'") from e

    def __eq__(self, other: "UniversalTimeStamp"):
        if isinstance(other, UniversalTimeStamp):
            return (self.year == other.year and self.month == other.month and self.day == other.day
                    and self.determine_ut_s() == other.determine_ut_s())
        return False

    def difference_ut_seconds(self, other_time_stamp: "UniversalTimeStamp") -> int:
        """
        Compares UT times (hours, minutes, seconds) and returns difference in seconds (self - other).
        Year, month and day are ignored.
        :return: diffenrece in seconds [int]
        """
        return (3600 * (self.hour - other_time_stamp.hour) + 60 * (self.minute - other_time_stamp.minute) +
                (self.second - other_time_stamp.second))

    def determine_ut_hr(self) -> float:
        return self.hour + self.minute / 60 + self.second / 3600

    def determine_ut_s(self) -> int:
        return self.hour * 3600 + self.minute * 60 + self.second




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
    def determine_theta_g(time_stamp: UniversalTimeStamp, theta_g0_deg: float) -> float:
        """
        Determines theta_g (current greenwich meridian angle) for a certain UT.
        :param theta_g0_deg: in degrees
        :param time_stamp:
        :return: theta_g in degrees
        """
        return theta_g0_deg + 360.98564724 * time_stamp.determine_ut_hr() / 24.0

    @staticmethod
    def determine_angular_drift(time_stamp_1: UniversalTimeStamp, time_stamp_2: UniversalTimeStamp) -> float:
        """
        Determines earth's rotation angle [deg] between two timestamps.
        Time stamps must be on the same day due to simplistic nature of UniversalTimeStamp class.
        :param time_stamp_1: timestamp
        :param time_stamp_2: timestamp
        :return: angle [deg]
        """
        assert time_stamp_1.year == time_stamp_2.year
        assert time_stamp_1.month == time_stamp_2.month
        assert time_stamp_1.day == time_stamp_2.day
        assert time_stamp_2.determine_ut_s() >= time_stamp_1.determine_ut_s()
        return 360.98564724 * (time_stamp_2.determine_ut_s() - time_stamp_1.determine_ut_s()) / 86400

    @staticmethod
    def determine_eci_longitude(ecef_longitude_deg: float, theta_g_deg: float) -> float:
        return (theta_g_deg + ecef_longitude_deg) % 360

    @staticmethod
    def determine_eci_longitude_from_time(ecef_longitude_deg: float, time_stamp: UniversalTimeStamp) -> float:

        j0 = EarthCenteredInertial.determine_j0(time_stamp.year, time_stamp.month, time_stamp.day)
        t0 = EarthCenteredInertial.determine_t0(j0)
        theta_g0_deg = EarthCenteredInertial.determine_theta_g0_deg(t0)
        theta_d_deg = EarthCenteredInertial.determine_theta_g(time_stamp, theta_g0_deg)
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
                                              time_stamp: UniversalTimeStamp):
        eci_longitude_deg = EarthCenteredInertial.determine_eci_longitude_from_time(ecef_longitude_deg, time_stamp)
        return EarthCenteredInertial.determine_vector_from_lat_lon_alt(Code.deg_to_rad(ecef_latitude_deg),
                                                                        Code.deg_to_rad(eci_longitude_deg), altitude_km)

    @staticmethod
    def rotate_eci_vector_around_earth_axis(eci_vector: np.ndarray, angle_deg: float) -> np.ndarray:
        """
        Rotates an eci vector around earth's rotation axis counterclockwise by a given angle.
        :param eci_vector:
        :param angle_deg:
        :return: rotated eci vector
        """
        w = Code.deg_to_rad(angle_deg)
        assert eci_vector.shape == (3,)
        z_rotation_matrix = np.array([[np.cos(w), -np.sin(w), 0], [np.sin(w), np.cos(w), 0], [0, 0, 1]])
        return np.matmul(z_rotation_matrix, eci_vector)



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