import numpy as np
from ichor.core.calculators import calculate_alf_features

def C_matrix(atoms_instance, iatm_idx, iatm_alf):

    return atoms_instance[iatm_idx].C(iatm_alf)

def C_1(atoms_instance, iatm_idx, iatm_alf):

    return C_matrix(atoms_instance, iatm_idx, iatm_alf)[0]

def C_2(atoms_instance, iatm_idx, iatm_alf):

    return C_matrix(atoms_instance, iatm_idx, iatm_alf)[1]

def C_3(atoms_instance, iatm_idx, iatm_alf):

    return C_matrix(atoms_instance, iatm_idx, iatm_alf)[2]

def sigma_fflux(x_axis_diff, xy_plane_diff):

    return -np.dot(x_axis_diff, xy_plane_diff) / np.dot(x_axis_diff, x_axis_diff)

def y_vec(atoms_instance, iatm_idx, iatm_alf):

    x_axis_atom_instance = atoms_instance[iatm_alf[1]]
    xy_plane_atom_instance = atoms_instance[iatm_alf[2]]

    x_axis_diff = x_axis_atom_instance.coordinates - atoms_instance[iatm_idx].coordinates
    xy_plane_diff = xy_plane_atom_instance.coordinates - atoms_instance[iatm_idx].coordinates

    s_fflux = sigma_fflux(x_axis_diff, xy_plane_diff)
    y_vec = s_fflux * x_axis_diff + xy_plane_diff

    return y_vec

def delta_Ax(iatm, omega, iatm_alf):

    if omega == iatm:
        return -1.0
    elif omega == iatm_alf[1]:
        return 1.0
    else:
        return 0.0

def delta_Axy(iatm, omega, iatm_alf):

    if omega == iatm:
        return -1.0
    elif omega == iatm_alf[2]:
        return 1.0
    else:
        return 0.0

def delta_An(iatm_idx, jatm_idx, omega):

    if omega == iatm_idx:
        return -1.0
    elif omega == jatm_idx:
        return 1.0
    else:
        return 0.0

def kronecker(i, k):

    if i == k:
        return 1.0
    else:
        return 0.0

def dRaxdotRaxy_da(iatm_idx, iatm_alf, omega, diff1, diff2):

    if omega == iatm_idx:
        res = -1.0 * (diff1 + diff2)
    elif omega == iatm_alf[1]:
        res = diff2
    elif omega == iatm_alf[2]:
        res = diff1
    else:
        res = np.zeros(3)
    
    return res

# d(Rax . Rax) / d(alpha)
def dRaxdotRax_da(iatm_idx, iatm_alf, omega, diff):

    if omega == iatm_idx:
        res = -2.0 * diff
    elif omega == iatm_alf[1]:
        res = 2.0 * diff
    else:
        res = np.zeros(3)

    return res

def dsigma_da(atoms_instance, iatm_idx, iatm_alf, omega):

    diff = atoms_instance[iatm_alf[1]].coordinates - atoms_instance[iatm_idx]
    diff2 = atoms_instance[iatm_alf[2]].coordinates - atoms_instance[iatm_idx]

    RaxdotRax = np.dot(diff, diff)
    RaxdotRaxy = np.dot(diff, diff2)

    res = ((RaxdotRaxy * dRaxdotRax_da(iatm_idx, iatm_alf, omega, diff)) / (RaxdotRax**2)) \
                - (dRaxdotRaxy_da(iatm_idx, iatm_alf, omega, diff, diff2))

    return res


def dyj_da(atoms_instance, iatm_idx, iatm_alf, omega, diff):

    res = np.zeros((3,3))

    dsigma = dsigma_da(atoms_instance, iatm_idx, iatm_alf, omega)
    delta_OmAx = delta_Ax(iatm_idx, omega, iatm_alf)
    delta_OmAxy = delta_Axy(iatm_idx, omega, iatm_alf)

    x_axis_atom_instance = atoms_instance[iatm_alf[1]]
    xy_plane_atom_instance = atoms_instance[iatm_alf[2]]
    x_axis_diff = x_axis_atom_instance.coordinates - atoms_instance[iatm_idx].coordinates
    xy_plane_diff = xy_plane_atom_instance.coordinates - atoms_instance[iatm_idx].coordinates
    s_fflux = sigma_fflux(x_axis_diff, xy_plane_diff)

    for i in range(3):
        for k in range(3):
            res[i, k] = (dsigma[i] * diff[k]) + (s_fflux * kronecker(i,k)*delta_OmAx) + (kronecker(i,k)*delta_OmAxy)

    return res

def EqC12(atoms_instance, iatm_idx, iatm_alf, omega, diff):

    eqC12 = np.zeros(3)

    dyj = dyj_da(atoms_instance, iatm_idx, iatm_alf, omega, diff)
    y_v = y_vec(atoms_instance, iatm_idx, iatm_alf)

    for j in range(3):

        eqC12[0] = eqC12[0] + (y_v[j] * dyj[0, j])
        eqC12[1] = eqC12[1] + (y_v[j] * dyj[1, j])
        eqC12[2] = eqC12[2] + (y_v[j] * dyj[2, j])

    sqrtydoty = np.sqrt(np.dot(y_v, y_v))
    tmp = -1.0 / sqrtydoty**3
    eqC12 = eqC12 * tmp

    return eqC12

def dR_da(atoms_instance, iatm_idx, jatm_idx, feat_idx, iatm_alf, omega):

    iatm_features = atoms_instance[iatm_idx].features(calculate_alf_features, iatm_alf)
    reci_feat = 1 / iatm_features[feat_idx]

    if omega == iatm_idx:
        diff = atoms_instance[iatm_idx].coordinates - atoms_instance[jatm_idx].coordinates
        dR_da = reci_feat * diff
    elif omega == jatm_idx:
        diff = atoms_instance[jatm_idx].coordinates - atoms_instance[iatm_idx].coordinates
        dR_da = reci_feat * diff
    else:
        dR_da = np.zeros([3])

    return dR_da

def dC1k_da(atoms_inst, iatm_idx, iatm_alf, omega):

    invRAx = 1.0 / atoms_inst[iatm_idx].features(calculate_alf_features, iatm_alf)[0]
    inv_RAx3 = invRAx**3

    diff = atoms_inst[iatm_alf[1]].coordinates - atoms_inst[iatm_idx].coordinates
    delta_OmAx = delta_Ax(iatm_idx, omega, iatm_alf)

    for i in range(3):
        for k in range(3):

            dC1k_da =  (invRAx * delta_OmAx * kronecker(i, k)) - (diff(i) * diff(k) * delta_OmAx * inv_RAx3)

    return dC1k_da

def dC2k_da(atoms_inst, iatm_idx, iatm_alf, omega):

    dC2k = np.zeros((3,3))

    C2_row = C_2(atoms_inst, iatm_idx, iatm_alf)
    y_vect = y_vec(atoms_inst, iatm_idx, iatm_alf)
    invsqrt_ydoty = 1.0 / np.sqrt(y_vect)

    diff = atoms_inst[iatm_alf[1]].coordinates - atoms_inst[iatm_idx].coordinates

    eqC12 = EqC12(atoms_inst, iatm_idx, iatm_alf, omega, diff)
    dyj = dyj_da(atoms_inst, iatm_idx, iatm_alf, omega, diff)

    for k in range(3):
        dC2k[0, k] = (dyj[0,k] * invsqrt_ydoty) + y_vect[k] * eqC12[0]
        dC2k[1, k] = (dyj[1,k] * invsqrt_ydoty) + y_vect[k] * eqC12[1]
        dC2k[2, k] = (dyj[2,k] * invsqrt_ydoty) + y_vect[k] * eqC12[2]

    return dC2k

def dC3k_da(atoms_inst, iatm_idx, iatm_alf, omega, c1_vec, c2_vec, dc1_vec, dc2_vec):

    dC3k = np.zeros((3,3))

    for i in range(3):

        dC3k[i, 0] = ( (c1_vec[1] * dc2_vec[i,2]) + (c2_vec[2] * dc1_vec[i,1]) ) \
            - ( (c1_vec[2] * dc2_vec[i,1]) + (c2_vec[1] * dc1_vec[i,2]) )

        dC3k[i, 1] =   ( (c1_vec[2] * dc2_vec[i,0]) + (c2_vec[0] * dc1_vec[i,2]) ) \
                        - ( (c1_vec[0] * dc2_vec[i,2]) + (c2_vec[2] * dc1_vec[i,0]) )

        dC3k[i, 2] =   ( (c1_vec[1] * dc2_vec[i,2]) + (c2_vec[1] * dc1_vec[i,0]) ) \
                        - ( (c1_vec[1] * dc2_vec[i,0]) + (c2_vec[0] * dc1_vec[i,1]) )

    return dC3k


def dZj_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, omega, j):

    diff = atoms_instance[jatm_idx].coordinates - atoms_instance[iatm_idx].coordinates

    dzj_da = np.zeros(3)
    zeta = np.zeros(3)

    c = C_matrix(atoms_instance, iatm_idx, iatm_alf)
    C1_vec = c[0]
    C2_vec = c[1]
    C3_vec = c[2]

    if j == 1:
        Cjk = C1_vec
        dCjk = dC1k_da(atoms_instance, iatm_idx, iatm_alf, omega)
    elif j == 2:
        Cjk = C2_vec
        dCjk = dC2k_da(atoms_instance, iatm_idx, iatm_alf, omega)
    elif j == 3:
        Cjk = C3_vec

        dC1k = dC1k_da(atoms_instance, iatm_idx, iatm_alf, omega)
        dC2k = dC2k_da(atoms_instance, iatm_idx, iatm_alf, omega)

        dCjk = dC3k_da(atoms_instance, iatm_idx, iatm_alf, omega, C1_vec, C2_vec, dC1k, dC2k)

    for i in range(3):
        for k in range(3):

            dzj_da[i] = dzj_da + dCjk[i,k] * diff[k] + Cjk[k] * kronecker(i,k) * delta_An(iatm_idx, jatm_idx, omega)

    # zeta[0] = C1_vec[0] * diff[0] + C1_vec[1] * diff[1] + C1_vec[2] * diff[2]
    # zeta[1] = C2_vec[0] * diff[0] + C2_vec[1] * diff[1] + C2_vec[2] * diff[2]
    # zeta[2] = C3_vec[0] * diff[0] + C3_vec[1] * diff[1] + C3_vec[2] * diff[2]

    # return dzj_da, zeta

    return dzj_da

def dChi_da(atoms_instance, iatm_idx, iatm_alf, omega):

    res = np.zeros(3)

    iatm_features = atoms_instance[iatm_idx].features(calculate_alf_features, iatm_alf)

    R_Ax = iatm_features[0]
    R_Axy = iatm_features[1]

    diff1 = atoms_instance[iatm_alf[1]].coordinates - atoms_instance[iatm_idx].coordinates
    diff2 = atoms_instance[iatm_alf[2]].coordinates - atoms_instance[iatm_idx].coordinates

    RxdotRxy = np.dot(diff1, diff2)

    invsin_Chi = -1.0 / np.sin(iatm_features[2])

    res[:] = ( -1.0 * dR_da(atoms_instance, iatm_idx, iatm_alf[1], 0, iatm_alf, omega) * RxdotRxy / (R_Ax**2 * R_Axy) )\
            + ( dRaxdotRaxy_da(iatm_idx, iatm_alf, omega, diff1, diff2) / (R_Ax * R_Axy) ) \
            + ( -1.0 * dR_da(atoms_instance, iatm_idx, iatm_alf[2], 1, iatm_alf, omega) * RxdotRxy / (R_Ax * R_Axy**2))

    res[:] = res * invsin_Chi

    return res

def dTheta_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, theta_feat_idx, zeta3, omega):

    dTheta = np.zeros(3)

    iatm_features = atoms_instance[iatm_idx].features(calculate_alf_features, iatm_alf)
    R_An = iatm_features[theta_feat_idx-1]
    Theta = iatm_features[theta_feat_idx]
    inv_RAn = 1.0 / R_An
    invSinTheta = -1.0 / np.sin(Theta)
    dInvR = -1.0 * inv_RAn**2 * dR_da(atoms_instance, iatm_idx, jatm_idx, theta_feat_idx-1, iatm_alf, omega)

    dzj = dZj_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, omega, 3)

    dTheta[0] = invSinTheta * (zeta3 * dInvR[0] + inv_RAn * dzj[0])
    dTheta[1] = invSinTheta * (zeta3 * dInvR[1] + inv_RAn * dzj[1])
    dTheta[2] = invSinTheta * (zeta3 * dInvR[2] + inv_RAn * dzj[2])

    return dTheta

def dPhi_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, zeta1, zeta2, phi_feat_idx, omega):

    dPhi = np.zeros(3)

    iatm_features = atoms_instance[iatm_idx].features(calculate_alf_features, iatm_alf)

    cos2phi = np.cos(iatm_features[phi_feat_idx])

    dz1 = dZj_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, omega, 1)
    dz2 = dZj_da(atoms_instance, iatm_idx, jatm_idx, iatm_alf, omega, 2)

    dPhi[0] = cos2phi * ( ((-1.0 * zeta2 * dz1[0]) / (zeta1**2)) + dz2[0]/zeta1)
    dPhi[1] = cos2phi * ( ((-1.0 * zeta2 * dz1[1]) / (zeta1**2)) + dz2[1]/zeta1)
    dPhi[2] = cos2phi * ( ((-1.0 * zeta2 * dz1[2]) / (zeta1**2)) + dz2[2]/zeta1)

    return dPhi