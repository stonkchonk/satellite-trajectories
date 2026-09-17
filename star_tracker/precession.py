import numpy as np

from common import Code


class Precession:

    def __init__(self, julian_centuries_since_j2000: float):
        self.years_since_j2000 = julian_centuries_since_j2000

        self.var_T = 0
        self.var_t = julian_centuries_since_j2000

        angle_zeta_arcsec = (2306.2181 + 1.39656 * self.var_T - 0.000139 * self.var_T ** 2) * self.var_t \
                                + (0.30188 - 0.000344 * self.var_T) * self.var_t ** 2 \
                                + 0.017998 * self.var_t ** 3

        angle_z_arcsec = (2306.2181 + 1.39656 * self.var_T - 0.000139 * self.var_T ** 2) * self.var_t \
                            + (1.09468 + 0.000066 * self.var_T) * self.var_t ** 2 \
                            + 0.018203 * self.var_t ** 3

        angle_theta_arcsec = ((2004.3109 - 0.85330 * self.var_T - 0.000217 * self.var_T ** 2) * self.var_t
                              - (0.42665 + 0.000217 * self.var_T) * self.var_t ** 2
                              - 0.041833 * self.var_t ** 3)

        angle_zeta_rad = Code.deg_to_rad(angle_zeta_arcsec / 3600)
        angle_z_rad = Code.deg_to_rad(angle_z_arcsec / 3600)
        angle_theta_rad = Code.deg_to_rad(angle_theta_arcsec / 3600)

        mat_R_z = np.array([
            [np.cos(-angle_z_rad), np.sin(-angle_z_rad), 0],
            [-np.sin(-angle_z_rad), np.cos(-angle_z_rad), 0],
            [0, 0, 1]
        ])

        mat_Q_theta = np.array([
            [np.cos(angle_theta_rad), 0, -np.sin(angle_theta_rad)],
            [0, 1, 0],
            [np.sin(angle_theta_rad), 0, np.cos(angle_theta_rad)]
        ])

        mat_R_zeta = np.array([
            [np.cos(-angle_zeta_rad), np.sin(-angle_zeta_rad), 0],
            [-np.sin(-angle_zeta_rad), np.cos(-angle_zeta_rad), 0],
            [0, 0, 1]
        ])

        self.precession_matrix = np.matmul(mat_R_z, np.matmul(mat_Q_theta, mat_R_zeta))

    def precess_vector_since_j2000(self, vector_at_j2000: np.ndarray) -> np.ndarray:
        return np.matmul(self.precession_matrix, vector_at_j2000)




