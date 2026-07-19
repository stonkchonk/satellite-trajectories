import numpy as np
from common import Params, Code
from math import sin, cos, sqrt, atan2, atan, pi

from star_tracker.catalog_parser import UnitVector


class ParametricTrajectory:
    def __init__(self, theta_1 : float, r_1: float, theta_2 : float, r_2: float, theta_3 : float, r_3 : float):
        self.theta_1 = theta_1
        self.r_1 = r_1
        self.theta_2 = theta_2
        self.r_2 = r_2
        self.theta_3 = theta_3
        self.r_3 = r_3

        self.argument_of_periapsis = self._determine_argument_of_periapsis() # omega
        self.eccentricity = self._determine_eccentricity(self.argument_of_periapsis) # e
        self.semi_major_axis = self._determine_semi_major_axis(self.argument_of_periapsis, self.eccentricity) # a

        # avoid negative eccentricities as they confuse argument of periapsis
        if self.eccentricity < 0:
            self.eccentricity = -self.eccentricity
            self.argument_of_periapsis = Code.normalize_angle(self.argument_of_periapsis + pi)



    def _determine_argument_of_periapsis(self) -> float:
        # A_12, B_12, C_12, alpha_12
        var_A_12 = cos(self.theta_2) * self.r_2 - cos(self.theta_1) * self.r_1
        var_B_12 = sin(self.theta_2) * self.r_2 - sin(self.theta_1) * self.r_1
        var_C_12 = sqrt(var_A_12 ** 2 + var_B_12 ** 2)
        var_alpha_12 = atan2(var_B_12, var_A_12)

        # A_13, B_13, C_13, alpha_13
        var_A_13 = cos(self.theta_3) * self.r_3 - cos(self.theta_1) * self.r_1
        var_B_13 = sin(self.theta_3) * self.r_3 - sin(self.theta_1) * self.r_1
        var_C_13 = sqrt(var_A_13 ** 2 + var_B_13 ** 2)
        var_alpha_13 = atan2(var_B_13, var_A_13)

        # D, E, F
        var_D = cos(var_alpha_12 - var_alpha_13)
        var_E = -sin(var_alpha_12 - var_alpha_13)
        var_F = (var_C_13 * (self.r_1 - self.r_2)) / (
                var_C_12 * (self.r_1 - self.r_3)
        )

        return Code.normalize_angle(var_alpha_13 - atan((var_F - var_D) / var_E))

    def _determine_eccentricity(self, argument_of_periapsis: float) -> float:
        # A_12, B_12, C_12, alpha_12
        var_A_12 = cos(self.theta_2) * self.r_2 - cos(self.theta_1) * self.r_1
        var_B_12 = sin(self.theta_2) * self.r_2 - sin(self.theta_1) * self.r_1
        var_C_12 = sqrt(var_A_12 ** 2 + var_B_12 ** 2)
        var_alpha_12 = atan2(var_B_12, var_A_12)

        return (self.r_1 - self.r_2) / (var_C_12 * cos(var_alpha_12 - argument_of_periapsis))


    def _determine_semi_major_axis(self, argument_of_periapsis: float, eccentricity: float) -> float:
        return self.r_1 * (1+ eccentricity * cos(self.theta_1 - argument_of_periapsis)) / (1 - eccentricity ** 2)

    @staticmethod
    def determine_orbital_plane_vector(first_eci_vector: np.ndarray, last_eci_vector: np.ndarray) -> UnitVector:
        """
        Determines the orbital plane vector which is perpendicular to two measurement vectors.
        :param first_eci_vector: measured eci vector
        :param last_eci_vector: measured eci vector
        :return: orbital plane described by perpendicular unit vector
        """
        assert first_eci_vector.shape == (3,)
        assert last_eci_vector.shape == (3,)
        return UnitVector.from_cross_product(UnitVector(first_eci_vector), UnitVector(last_eci_vector))

    @staticmethod
    def _orbital_plane_deviations(eci_vectors: list[np.ndarray], plane_vector: UnitVector) -> list[float]:
        """

        :param eci_vectors:
        :return:
        """
        for v in eci_vectors:
            assert v.shape == (3,)
        deviations_deg = []
        for v in eci_vectors:
            deviations_deg.append(abs(Code.rad_to_deg(Code.angular_separation_of_two_vectors_rad(plane_vector.value, v) - pi / 2)))
        return deviations_deg

    @staticmethod
    def verify_orbital_planar_integrity(eci_vectors: list[np.ndarray], plane_vector: UnitVector,
                                        max_deviation_deg: float = 0.2) -> bool:
        """
        Checks that all vectors are located within the same plane, tolerating some deviation.
        :param eci_vectors: list of vectors
        :param max_deviation_deg: maximum allowed deviation in degrees
        :return: true or false
        """
        return all([deviation <= max_deviation_deg for deviation in ParametricTrajectory._orbital_plane_deviations(eci_vectors, plane_vector)])

    @staticmethod
    def _select_middle_vector(eci_vectors: list[np.ndarray], plane_vector: UnitVector) -> int:
        """
        Returns index of middle vector in list of vectors.
        :param eci_vectors: list of vectors in orbital plane
        :return: index
        """
        first, last = eci_vectors[0], eci_vectors[-1]
        deviation_differences = []
        for idx, v in enumerate(eci_vectors):
            first_deviation = Code.angular_separation_of_two_vectors_rad(v, first)
            last_deviation = Code.angular_separation_of_two_vectors_rad(v, last)
            deviation_differences.append(abs(first_deviation - last_deviation))
        return deviation_differences.index(min(deviation_differences))

    @staticmethod
    def _determine_eci_theta_origin_vector(orbital_plane_vector: UnitVector) -> UnitVector:
        """
        Determines the origin vector for the orbital plane from where we determine the theta angles.
        This vector is basically located at theta = 0.
        :return:
        """

    @classmethod
    def from_eci_measurements(cls, measured_eci_vectors: list[np.ndarray]) -> "ParametricTrajectory":
        assert len(measured_eci_vectors) >= 3

        first_vector = measured_eci_vectors[0]
        last_vector = measured_eci_vectors[-1]
        plane_vector = cls.determine_orbital_plane_vector(first_vector, last_vector)

        assert cls.verify_orbital_planar_integrity(measured_eci_vectors, plane_vector)

        middle_vector = measured_eci_vectors[cls._select_middle_vector(measured_eci_vectors, plane_vector)]
        theta_1 = Code.full_circle_theta_angle_of_vector_rad(first_vector, plane_vector.value)
        theta_2 = Code.full_circle_theta_angle_of_vector_rad(middle_vector, plane_vector.value)
        theta_3 = Code.full_circle_theta_angle_of_vector_rad(last_vector, plane_vector.value)
        r_1 = np.sqrt(first_vector.dot(first_vector))
        r_2 = np.sqrt(middle_vector.dot(middle_vector))
        r_3 = np.sqrt(last_vector.dot(last_vector))
        print(plane_vector, r_1/8000, r_2/8000, r_3/8000, theta_1, theta_2, theta_3)
        return cls(theta_1, r_1, theta_2, r_2, theta_3, r_3)







class GaussAlgorithm:
    def __init__(self, t1: float, t2: float, t3: float, R1: np.ndarray, R2: np.ndarray, R3: np.ndarray,
                 pd1: np.ndarray, pd2: np.ndarray, pd3: np.ndarray):
        """
        Performs Gauss orbit determination algorithm.
        :param t1: observation time 1 [s]
        :param t2: observation time 2 [s]
        :param t3: observation time 3 [s]
        :param R1: position vector in ECI coordinate system at t1
        :param R2: position vector in ECI coordinate system at t2
        :param R3: position vector in ECI coordinate system at t3
        :param pd1: observation direction vector in ECI coordinate system at t1
        :param pd2: observation direction vector in ECI coordinate system at t2
        :param pd3: observation direction vector in ECI coordinate system at t3
        """
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.R1 = R1
        self.R2 = R2
        self.R3 = R3
        self.pd1 = pd1
        self.pd2 = pd2
        self.pd3 = pd3

        # member variables
        self.tau1 = 0
        self.tau3 = 0
        self.tau = 0
        self.p1 = np.array([0, 0, 0])
        self.p2 = np.array([0, 0, 0])
        self.p3 = np.array([0, 0, 0])
        self.D0 = 0
        self.D11 = 0
        self.D12 = 0
        self.D13 = 0
        self.D21 = 0
        self.D22 = 0
        self.D23 = 0
        self.D31 = 0
        self.D32 = 0
        self.D33 = 0
        self.A = 0
        self.B = 0
        self.E = 0
        self.R2sq = 0
        self.r1 = np.array([0, 0, 0])
        self.r2 = np.array([0, 0, 0])
        self.r3 = np.array([0, 0, 0])

    def gauss_algorithm_roots(self) -> list[float]:
        """
        Determines candidates for r2 as roots of a polynomial.
        :return: Viable candidates for r2.
        """
        # Step 1: Calculate intervals
        self.tau1 = self.t1 - self.t2
        self.tau3 = self.t3 - self.t2
        self.tau = self.tau3 - self.tau1

        # Step 2: Calculate cross products
        self.p1 = np.cross(self.pd2, self.pd3)
        self.p2 = np.cross(self.pd1, self.pd3)
        self.p3 = np.cross(self.pd1, self.pd2)

        # Step 3: Calculate D0
        self.D0 = np.dot(self.pd1, self.p1)

        # Step 4: Calculate scalar quantities
        self.D11 = np.dot(self.R1, self.p1)
        self.D12 = np.dot(self.R1, self.p2)
        self.D13 = np.dot(self.R1, self.p3)
        self.D21 = np.dot(self.R2, self.p1)
        self.D22 = np.dot(self.R2, self.p2)
        self.D23 = np.dot(self.R2, self.p3)
        self.D31 = np.dot(self.R3, self.p1)
        self.D32 = np.dot(self.R3, self.p2)
        self.D33 = np.dot(self.R3, self.p3)

        # Step 5: Calculate A and B
        self.A = (1/self.D0) * (-self.D12 * (self.tau3 / self.tau) + self.D22 + self.D32 * (self.tau1 / self.tau))
        self.B = (1/(6*self.D0)) * (self.D12 * (self.tau3**2 - self.tau**2) * (self.tau3 / self.tau) + self.D32 * (self.tau**2 - self.tau1**2) * (self.tau1 / self.tau))

        # Step 6: Calculate E and R2sq (R2^2)
        self.E = np.dot(self.R2, self.pd2)
        self.R2sq = np.dot(self.R2, self.R2)

        # Step 7: Calculate a, b, c coefficients
        a = -(self.A**2 +2*self.A*self.E + self.R2sq)
        b = -2 * Params.mu_km * self.B * (self.A + self.E)
        c = -Params.mu_km ** 2 * self.B ** 2

        # Step 8: Find positive real roots of polynomial.
        coefficients = [1, 0, a, 0, 0, b, 0, 0, c]
        roots = np.roots(coefficients)
        real_roots = roots[np.isclose(roots.imag, 0)].real
        return [r for r in real_roots if r > 0]

    def gauss_algorithm_orbit_from_root(self, r2_root: float) -> list[np.ndarray]:
        """
        Determine candidate vectors from one solution of r2
        :param r2_root: solution of Step 8 as root of polynomial.
        :return: list of three candidate vectors
        """
        # Step 9: Calculate rho for slant ranges
        rho1 = (1 / self.D0) * ((6 * (self.D31 * self.tau1 / self.tau3 + self.D21 * self.tau / self.tau3) * r2_root ** 3 + Params.mu_km * self.D31 * (self.tau ** 2 - self.tau1 ** 2) * self.tau1 / self.tau3) / (6 * r2_root ** 3 + Params.mu_km * (self.tau ** 2 - self.tau3 ** 2)) - self.D11)
        rho3 = (1 / self.D0) * ((6 * (self.D13 * self.tau3 / self.tau1 - self.D23 * self.tau / self.tau1) * r2_root ** 3 + Params.mu_km * self.D13 * (self.tau ** 2 - self.tau3 ** 2) * self.tau3 / self.tau1) / (6 * r2_root ** 3 + Params.mu_km * (self.tau ** 2 - self.tau1 ** 2)) - self.D33)
        rho2 = self.A + Params.mu_km * self.B / r2_root ** 3

        # Step 10: calculate radii vectors
        r1 = self.R1 + rho1 * self.pd1
        r2 = self.R2 + rho2 * self.pd2
        r3 = self.R3 + rho3 * self.pd3

        print(np.linalg.norm(r1), np.linalg.norm(r2), np.linalg.norm(r3))
        print(rho1, rho2, rho3, "<<rhos")

        return [r1, r2, r3]

    def gauss_algorithm_select_solution(self):
        r2_roots = self.gauss_algorithm_roots()
        for r2_root in r2_roots:
            r_candidates = self.gauss_algorithm_orbit_from_root(r2_root)
            print(r2_root, r_candidates)
            return r_candidates
