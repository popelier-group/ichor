import numpy as np
from ichor.core.models.fflux_derivative_helper_functions import *
from ichor.core.models.calculate_fflux_derivatives import fflux_predict_value
from typing import List


def reciprocal_fflux_derivs_da_df(jatm_idx: int, iatm_idx: int, atoms_instance: "Atoms", system_alf: List["ALF"]) -> np.ndarray:
    """Computes the reciprocal fflux derivatives. The jatm_idx is the atom on which
    the ALF is centered, while the iatm_idx can be any atom in the system.

    :param jatm_idx: The index of the central atom that the ALF is centered on.
    :param iatm_idx: The index of the atom that is moving (can be any atom in the system.)
    :param atoms_instance: An `Atoms` instance that contains the geometry for which the
        derivatives are calculated.
    :param system_alf: A list of ALF instances for every atom in the system. The ALF instances are just named tuples
        containing the central atom idx, x-axis idx, xy-plane idx.
    :return: A submatrix (shape n_features x 3) which contains the derivatives of
        Cartestian coordinates of atom iatm_idx with respect to features calculated
        with jatm_idx as the central ALF atom.
    :rtype: np.ndarray
    """

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
    # then find the reciprocal, so it will be derivative of Cartesian coord of iatm_idx with respect to first feature (given jatm_idx as central atom)
    # also give back zeroes if difference is very small / when dividing by zero
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)
    n_features_times_3_tmp_matrix[0, 0] = da_df[0]
    n_features_times_3_tmp_matrix[0, 1] = da_df[1]
    n_features_times_3_tmp_matrix[0, 2] = da_df[2]

    # derivative of feature 2 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
    # so there is only going to be change if iatm_idx is the A_xy atom
    # or if the iatm_idx is the jatm_idx (the central atom) 
    # otherwise return 0,0,0
    df_da = dR_da(jatm_idx, system_alf[jatm_idx][2], 1, iatm_idx, atoms_instance, system_alf)
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)
    n_features_times_3_tmp_matrix[1, 0] = da_df[0]
    n_features_times_3_tmp_matrix[1, 1] = da_df[1]
    n_features_times_3_tmp_matrix[1, 2] = da_df[2]

    # derivative of feature 3 of atom jatm da^jatm_dx with respect to change of coordinates of iatm_idx
    # three atoms are involved in feature 3 as it is the valence angle.
    df_da = dChi_da(jatm_idx, iatm_idx, atoms_instance, system_alf)
    da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)
    n_features_times_3_tmp_matrix[2, 0] = da_df[0]
    n_features_times_3_tmp_matrix[2, 1] = da_df[1]
    n_features_times_3_tmp_matrix[2, 2] = da_df[2]

    # non-alf atoms
    local_non_alf_atoms = [i for i in range(len(atoms_instance)) if i not in system_alf[jatm_idx]]

    # derivative of non-alf atom w.r.t. feature k of jatm_idx (the atom on which the ALF is centered)
    feat_idx = 3
    for k in range(len(atoms_instance)-3):
        diff = atoms_instance[local_non_alf_atoms[k]].coordinates - atoms_instance[jatm_idx].coordinates

        # R
        df_da = dR_da(jatm_idx, local_non_alf_atoms[k], feat_idx, iatm_idx, atoms_instance, system_alf)
        da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)

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
        da_df = np.divide(1.0, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)
        n_features_times_3_tmp_matrix[feat_idx, 0] = da_df[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = da_df[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = da_df[2]

        feat_idx += 1

        # Phi
        df_da = dPhi_da(jatm_idx, local_non_alf_atoms[k], zeta1, zeta2, feat_idx, iatm_idx, atoms_instance, system_alf)
        da_df = np.divide(1, df_da, out=np.zeros_like(df_da), where= np.abs(df_da) > np.finfo(float).eps * 10)
        n_features_times_3_tmp_matrix[feat_idx, 0] = da_df[0]
        n_features_times_3_tmp_matrix[feat_idx, 1] = da_df[1]
        n_features_times_3_tmp_matrix[feat_idx, 2] = da_df[2]

        feat_idx += 1

    return n_features_times_3_tmp_matrix