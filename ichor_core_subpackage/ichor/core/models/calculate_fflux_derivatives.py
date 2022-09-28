from json import detect_encoding
from os import system
from ichor.core.files import XYZ
from ichor.core.models.model import Model
from ichor.core.calculators import calculate_alf_atom_sequence, default_feature_calculator
import numpy as np
import math
from ichor.core.atoms import ALF
from ichor.core.models.fflux_derivative_helper_functions import *

def fflux_predict_value(model_inst, test_x_features):

    x_train_array = model_inst.x
    y_train_array = model_inst.y.flatten()
    weights = model_inst.weights.flatten()

    kernels = model_inst.kernel
    rbf_thetas = kernels.k1._thetas
    periodic_thetas = kernels.k2._thetas

    thetas = np.concatenate((rbf_thetas, periodic_thetas))

    n_train = x_train_array.shape[0]
    n_features = x_train_array.shape[1]

    Q_est = 0.0
    dQ_df = np.zeros(n_features)
    dQ_df_temp = np.zeros(n_features)

    for j in range(n_train):

        expo = 0.0

        for h in range(n_features):

            fdiff = x_train_array[j, h] - test_x_features[h]

            # if phi dimension, then use periodic kernel
            if ((h+1) % 3) == 0 and h != 2:

                # 2.0 because gpytorch does not multiply periodic kernel lengthscale by 2, i.e. it is 1/lambda
                expo = expo + 2.0 * thetas[h] * math.sin((fdiff/2.0))**2
                dQ_df_temp[h] = weights[j]*(-2.0)*thetas[h]*sign_j(fdiff) * math.sin(abs(fdiff)/2.0) * math.cos(abs(fdiff)/2.0)

            # if not phi dimension, use rbf kernel
            else:

                expo = expo + thetas[h] * fdiff * fdiff

                dQ_df_temp[h] = weights[j] *sign_j(fdiff) * -2.0 * thetas[h] * abs(fdiff)

        expo = math.exp(-expo)

        Q_est = Q_est + weights[j] * expo

        dQ_df_temp = expo * dQ_df_temp

        dQ_df = dQ_df + dQ_df_temp

    Q_est = Q_est + model_inst.mean.value(np.zeros((1,1)))
    Q_est = Q_est.item()

    return Q_est, dQ_df

def fflux_derivs(iatm_idx, jatm_idx, atoms_instance, system_alf, model_inst):

    dQ_dx = 0.0
    dQ_dy = 0.0
    dQ_dz = 0.0

    C = atoms_instance[jatm_idx].C(system_alf)
    jatm_features = atoms_instance[jatm_idx].features(calculate_alf_features, system_alf)

    Q_pred, dQ_df = fflux_predict_value(model_inst, jatm_features)

    # feature 1
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][1], 0, iatm_idx, atoms_instance, system_alf)
    dQ_dx = dQ_dx + dQ_df[0] * df_da[0]
    dQ_dy = dQ_dy + dQ_df[0] * df_da[1]
    dQ_dz = dQ_dz + dQ_df[0] * df_da[2]
    # feature 2
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][2], 1, iatm_idx, atoms_instance, system_alf)
    dQ_dx = dQ_dx + dQ_df[1] * df_da[0]
    dQ_dy = dQ_dy + dQ_df[1] * df_da[1]
    dQ_dz = dQ_dz + dQ_df[1] * df_da[2]
    # feature 3
    df_da = dChi_da(jatm_idx, iatm_idx, atoms_instance, system_alf)
    dQ_dx = dQ_dx + dQ_df[2] * df_da[0]
    dQ_dy = dQ_dy + dQ_df[2] * df_da[1]
    dQ_dz = dQ_dz + dQ_df[2] * df_da[2]

    # non-alf atoms
    local_non_alf_atoms = [i for i in range(len(atoms_instance)) if i not in system_alf[jatm_idx]]

    feat_idx = 3
    for k in range(len(atoms_instance)-3):
        diff = atoms_instance[local_non_alf_atoms[k]].coordinates - atoms_instance[jatm_idx].coordinates

        # R
        df_da = dR_da(jatm_idx, local_non_alf_atoms[k], feat_idx, iatm_idx, atoms_instance, system_alf)
        dQ_dx = dQ_dx + dQ_df[feat_idx] * df_da[0]
        dQ_dy = dQ_dy + dQ_df[feat_idx] * df_da[1]
        dQ_dz = dQ_dz + dQ_df[feat_idx] * df_da[2]

        feat_idx += 1

        zetas = np.dot(C, diff)
        zeta1 = zetas[0]
        zeta2 = zetas[1]
        zeta3 = zetas[2]

        # Theta
        df_da = dTheta_da(jatm_idx, local_non_alf_atoms[k], feat_idx, zeta3, iatm_idx, atoms_instance, system_alf)
        dQ_dx = dQ_dx + dQ_df[feat_idx] * df_da[0]
        dQ_dy = dQ_dy + dQ_df[feat_idx] * df_da[1]
        dQ_dz = dQ_dz + dQ_df[feat_idx] * df_da[2]

        feat_idx += 1

        # Phi
        df_da = dPhi_da(jatm_idx, local_non_alf_atoms[k], zeta1, zeta2, feat_idx, iatm_idx, atoms_instance, system_alf)
        dQ_dx = dQ_dx + dQ_df[feat_idx] * df_da[0]
        dQ_dy = dQ_dy + dQ_df[feat_idx] * df_da[1]
        dQ_dz = dQ_dz + dQ_df[feat_idx] * df_da[2]

        feat_idx += 1

    return np.array([dQ_dx, dQ_dy, dQ_dz])