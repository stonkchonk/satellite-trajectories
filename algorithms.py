import numpy
import numpy as np
from common import Params

class GaussAlgorithm:
    def __init__(self, t1: float, t2: float, t3: float, R1: numpy.ndarray, R2: numpy.ndarray, R3: numpy.ndarray,
                pd1: numpy.ndarray, pd2: numpy.ndarray, pd3: numpy.ndarray):
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
        b = -2*Params.mu*self.B * (self.A + self.E)
        c = -Params.mu**2 * self.B**2

        # Step 8: Find positive real roots of polynomial.
        coefficients = [1, 0, a, 0, 0, b, 0, 0, c]
        roots = np.roots(coefficients)
        real_roots = roots[np.isclose(roots.imag, 0)].real
        return [r for r in real_roots if r > 0]

    def gauss_algorithm_orbit_from_root(self, r2: float):
        # Step 9: Calculate rho for slant ranges
        rho1 = (1 / self.D0) * ((6 * (self.D31 * self.tau1 / self.tau3 + self.D21 * self.tau / self.tau3) * r2 ** 3 + Params.mu * self.D31 * (self.tau ** 2 - self.tau1 ** 1) * self.tau1 / self.tau3) / (6 * r2 ** 3 + Params.mu * (self.tau ** 2 - self.tau3 ** 2)) - self.D11)
        rho3 = (1 / self.D0) * ((6 * (self.D13 * self.tau3 / self.tau1 + self.D23 * self.tau / self.tau1) * r2 ** 3 + Params.mu * self.D13 * (self.tau ** 2 - self.tau3 ** 1) * self.tau3 / self.tau1) / (6 * r2 ** 3 + Params.mu * (self.tau ** 2 - self.tau1 ** 2)) - self.D33)
        rho2 = self.A + Params.mu * self.B / r2 ** 3

        # Step 10: calculate radii vectors
        self.r1 = self.R1 + rho1 * self.pd1
        self.r2 = self.R2 + rho2 * self.pd2
        self.r3 = self.R3 + rho3 * self.pd3
