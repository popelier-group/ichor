import numpy as np
from ichor.core.models.fflux_derivative_helper_functions import *

def fflux_predict_value(model_inst, test_x_features):

    x_train_array = model_inst.x
    weights = model_inst.weights.flatten()

    kernels = model_inst.kernel
    rbf_thetas = kernels.k1._thetas
    periodic_thetas = kernels.k2._thetas

    n_train = x_train_array.shape[0]
    n_features = x_train_array.shape[1]

    # make sure thetas are ordered correctly (cannot concat rbf thetas to periodic thetas because it leads to wrong indexing)
    #  first five thetas are for rbf dimensions (because non cyclic), then 6th (5th index) is a phi dimension, then two rbf, then periodic and so on
    thetas = []
    rbf_idx = 0
    periodic_idx = 0
    for i in range(n_features):
        if ((i+1) % 3) == 0 and i != 2:
            thetas.append(periodic_thetas[periodic_idx])
            periodic_idx += 1
        else:
            thetas.append(rbf_thetas[rbf_idx])
            rbf_idx += 1
    thetas = np.array(thetas)

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
                expo = expo + 2.0 * thetas[h] * np.sin((fdiff/2.0))**2
                dQ_df_temp[h] = weights[j]*(-2.0)*thetas[h]*sign_j(fdiff) * np.sin(abs(fdiff)/2.0) * np.cos(abs(fdiff)/2.0)

            # if not phi dimension, use rbf kernel
            else:

                expo = expo + thetas[h] * fdiff * fdiff

                dQ_df_temp[h] = weights[j] *sign_j(fdiff) * -2.0 * thetas[h] * abs(fdiff)

        expo = np.exp(-expo)

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


def fflux_derivs_da_df_matrix(jatm_idx, iatm_idx, atoms_instance, system_alf):
    """Calculates the """

    natoms = len(atoms_instance)

    # add this in case of two atom systems such as HCl
    if natoms == 2:
        # column of da/df_n. So derivative of one coordinate (of one atom) with respect to all features
        # for two atom systems, there is only 1 feature, the distance between atoms
        n_features_times_3_tmp_matrix = np.zeros((1, 3))
        # derivative of feature 1 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
        # so there is only going to be change if iatm_idx is the A_x atom
        # or if the iatm_idx is the jatm_idx (the central atom)
        # otherwise return 0,0,0
        df_da = dR_da(jatm_idx, system_alf[jatm_idx][1], 0, iatm_idx, atoms_instance, system_alf)
        n_features_times_3_tmp_matrix[0, 0] = df_da[0]
        n_features_times_3_tmp_matrix[0, 1] = df_da[1]
        n_features_times_3_tmp_matrix[0, 2] = df_da[2]

        return n_features_times_3_tmp_matrix

    # use a machine precision an order of magnitude higher to prevent tiny values of da_df from
    # becoming very large when doing 1/df_da. Round down da_df to 0.0 when needed.

    # column of da/df_n. So derivative of one coordinate (of one atom) with respect to all features
    n_features_times_3_tmp_matrix = np.zeros(((3 * len(atoms_instance) - 6), 3))
    C = atoms_instance[jatm_idx].C(system_alf)

    # derivative of feature 1 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
    # so there is only going to be change if iatm_idx is the A_x atom
    # or if the iatm_idx is the jatm_idx (the central atom)
    # otherwise return 0,0,0
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][1], 0, iatm_idx, atoms_instance, system_alf)
    n_features_times_3_tmp_matrix[0, 0] = df_da[0]
    n_features_times_3_tmp_matrix[0, 1] = df_da[1]
    n_features_times_3_tmp_matrix[0, 2] = df_da[2]

    # derivative of feature 2 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
    # so there is only going to be change if iatm_idx is the A_xy atom
    # or if the iatm_idx is the jatm_idx (the central atom) 
    # otherwise return 0,0,0
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][2], 1, iatm_idx, atoms_instance, system_alf)
    n_features_times_3_tmp_matrix[1, 0] = df_da[0]
    n_features_times_3_tmp_matrix[1, 1] = df_da[1]
    n_features_times_3_tmp_matrix[1, 2] = df_da[2]

    # derivative of feature 3 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
    # three atoms are involved in feature 3 as it is the valence angle.
    df_da = dChi_da(jatm_idx, iatm_idx, atoms_instance, system_alf)
    n_features_times_3_tmp_matrix[2, 0] = df_da[0]
    n_features_times_3_tmp_matrix[2, 1] = df_da[1]
    n_features_times_3_tmp_matrix[2, 2] = df_da[2]

    # non-alf atoms
    local_non_alf_atoms = [i for i in range(len(atoms_instance)) if i not in system_alf[jatm_idx]]

    # derivative of non-alf atom w.r.t. feature k of jatm_idx (the atom on which the ALF is centered)
    feat_idx = 3
    for k in range(len(atoms_instance)-3):
        diff = atoms_instance[local_non_alf_atoms[k]].coordinates - atoms_instance[jatm_idx].coordinates

        # R
        df_da = dR_da(jatm_idx, local_non_alf_atoms[k], feat_idx, iatm_idx, atoms_instance, system_alf)

        n_features_times_3_tmp_matrix[feat_idx, 0] = df_da[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = df_da[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = df_da[2]

        feat_idx += 1

        zetas = np.dot(C, diff)
        zeta1 = zetas[0]
        zeta2 = zetas[1]
        zeta3 = zetas[2]

        # Theta
        df_da = dTheta_da(jatm_idx, local_non_alf_atoms[k], feat_idx, zeta3, iatm_idx, atoms_instance, system_alf)
        n_features_times_3_tmp_matrix[feat_idx, 0] = df_da[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = df_da[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = df_da[2]

        feat_idx += 1

        # Phi
        df_da = dPhi_da(jatm_idx, local_non_alf_atoms[k], zeta1, zeta2, feat_idx, iatm_idx, atoms_instance, system_alf)
        n_features_times_3_tmp_matrix[feat_idx, 0] = df_da[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = df_da[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = df_da[2]

        feat_idx += 1

    return n_features_times_3_tmp_matrix