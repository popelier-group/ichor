import numpy as np
from ichor.core.models.fflux_derivative_helper_functions import *
from ichor.core.models.calculate_fflux_derivatives import fflux_predict_value


def reciprocal_fflux_derivs_da_df(iatm_idx, jatm_idx, atoms_instance, system_alf):
    """Computes the reciprocal fflux derivatives

    :param iatm_idx: _description_
    :type iatm_idx: _type_
    :param jatm_idx: _description_
    :type jatm_idx: _type_
    :param atoms_instance: _description_
    :type atoms_instance: _type_
    :param system_alf: _description_
    :type system_alf: _type_
    :param model_inst: _description_
    :type model_inst: _type_
    :return: _description_
    :rtype: _type_
    """

    # column of da/df_n. So derivative of one coordinate with respect to all features
    n_features_times_3_tmp_matrix = np.zeros(((3 * len(atoms_instance) - 6), 3))

    C = atoms_instance[jatm_idx].C(system_alf)

    # derivative of global cartesian coordinate wrt first feature
    # feature 1, this is a np.ndarray of shape 3, derivative of global coordinate x with respect to first feature,
    # derivative of global coordinate y with r espect to first feature, derivative of global coord z wtr first feature.

    # da1 / df1, da2 / df1, da3 / df1
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][1], 0, iatm_idx, atoms_instance, system_alf)
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)
    n_features_times_3_tmp_matrix[0, 0] = da_df[0]
    n_features_times_3_tmp_matrix[0, 1] = da_df[1]
    n_features_times_3_tmp_matrix[0, 2] = da_df[2]

    # feature 2
    # da1 / df2, da2/ df2, da3 / df2
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][2], 1, iatm_idx, atoms_instance, system_alf)
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)
    n_features_times_3_tmp_matrix[1, 0] = da_df[0]
    n_features_times_3_tmp_matrix[1, 1] = da_df[1]
    n_features_times_3_tmp_matrix[1, 2] = da_df[2]

    # feature 3
    # da1 / df3, da2/ df3, da3 / df3
    df_da = dChi_da(jatm_idx, iatm_idx, atoms_instance, system_alf)
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)
    n_features_times_3_tmp_matrix[2, 0] = da_df[0]
    n_features_times_3_tmp_matrix[2, 1] = da_df[1]
    n_features_times_3_tmp_matrix[2, 2] = da_df[2]

    # non-alf atoms
    local_non_alf_atoms = [i for i in range(len(atoms_instance)) if i not in system_alf[jatm_idx]]

    feat_idx = 3
    for k in range(len(atoms_instance)-3):
        diff = atoms_instance[local_non_alf_atoms[k]].coordinates - atoms_instance[jatm_idx].coordinates

        # R
        df_da = dR_da(jatm_idx, local_non_alf_atoms[k], feat_idx, iatm_idx, atoms_instance, system_alf)

        da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)

        n_features_times_3_tmp_matrix[feat_idx, 0] = da_df[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = da_df[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = da_df[2]

        feat_idx += 1

        zetas = np.dot(C, diff)
        zeta1 = zetas[0]
        zeta2 = zetas[1]
        zeta3 = zetas[2]

        # Theta
        df_da = dTheta_da(jatm_idx, local_non_alf_atoms[k], feat_idx, zeta3, iatm_idx, atoms_instance, system_alf)
        da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)
        n_features_times_3_tmp_matrix[feat_idx, 0] = da_df[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = da_df[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = da_df[2]

        feat_idx += 1

        # Phi
        df_da = dPhi_da(jatm_idx, local_non_alf_atoms[k], zeta1, zeta2, feat_idx, iatm_idx, atoms_instance, system_alf)
        da_df = np.divide(1, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps)
        n_features_times_3_tmp_matrix[feat_idx, 0] = da_df[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = da_df[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = da_df[2]

        feat_idx += 1

    return n_features_times_3_tmp_matrix