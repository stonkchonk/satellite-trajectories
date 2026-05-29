from math import sqrt, pi

from fontTools.ttLib.tables.D_S_I_G_ import pem_spam

m_earth_kg = 5.9722e24
g_constant = 6.6743e-11

def vis_viva(r: float, a: float):
    global g_constant
    global m_earth_kg
    return sqrt(g_constant * m_earth_kg * (2/r - 1/a))


def radius_from_angular_velocities(w_1: float, w_2: float):
    global g_constant
    global m_earth_kg
    dividend = 2 * g_constant * m_earth_kg * (1 - sqrt(w_2/w_1))
    divisor = w_1**2 - w_1*w_2
    return (dividend / divisor) ** (1/3)

pe_m = 7000e3
ap_m = 140000e3


a = (pe_m + ap_m) / 2
v_pe = vis_viva(pe_m, a)
v_ap = vis_viva(ap_m, a)
print(v_pe, v_ap)


w_pe = v_pe / pe_m
w_ap = v_ap / ap_m

r_50k = 50000e3
v_50k = vis_viva(r_50k, a)
w_50k = v_50k / r_50k

r_c1 = radius_from_angular_velocities(w_50k, w_pe)
r_c2 = radius_from_angular_velocities(w_50k, w_ap)

print(r_c1, r_c2)

