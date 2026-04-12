from math import sqrt, cos, sin
from common import Code, Constants

class Geometry:

    @staticmethod
    def radius_relative_to_center(equatorial: float, polar: float, theta: float):
        """
        Calculates radius of ellipse depending on angle theta, as described in
        https://en.wikipedia.org/wiki/Ellipse#Polar_form_relative_to_center.
        :param equatorial: [radius] 1/2 diameter left to right
        :param polar: [radius] 1/2 diameter top to bottom
        :param theta: angle [radians]
        :return: radius of ellipse at that specific angle from center
        """
        return (equatorial * polar) / sqrt( (polar * cos(theta))**2 + (equatorial * sin(theta))**2 )

    @staticmethod
    def earth_radius_from_altitude(altitude_km: float, longitude_deg: float):
        return Geometry.radius_relative_to_center(Constants.earth_equatorial_rad_km, Constants.earth_polar_rad_km,
                                                  Code.deg_to_rad(longitude_deg)) + altitude_km
