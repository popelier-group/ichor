import numpy as np
from ichor.core.common.arith import kronecker_delta

# impmenentations of the prime functions which are used in the conversions of
# all the multipole moments


def mu_prime(alpha, displacement_vector):

    return displacement_vector[alpha]


def theta_prime(alpha, beta, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]

    return 0.5 * (
        3 * displacement_alpha * displacement_beta
        - norm**2 * kronecker_delta(alpha, beta)
    )


def omega_prime(alpha, beta, gamma, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]
    displacement_gamma = displacement_vector[gamma]

    return 0.5 * (
        5 * displacement_alpha * displacement_beta * displacement_gamma
        - norm**2
        * (
            displacement_alpha * kronecker_delta(beta, gamma)
            + displacement_beta * kronecker_delta(alpha, gamma)
            + displacement_gamma * kronecker_delta(alpha, beta)
        )
    )


def phi_prime(alpha, beta, gamma, chi, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]
    displacement_gamma = displacement_vector[gamma]
    displacement_chi = displacement_vector[chi]

    return 0.125 * (
        35
        * displacement_alpha
        * displacement_beta
        * displacement_gamma
        * displacement_chi
        - 5
        * norm**2
        * (
            displacement_gamma * displacement_chi * kronecker_delta(alpha, beta)
            + displacement_beta * displacement_gamma * kronecker_delta(alpha, chi)
            + displacement_beta * displacement_chi * kronecker_delta(alpha, gamma)
            + displacement_alpha * displacement_chi * kronecker_delta(beta, gamma)
            + displacement_alpha * displacement_beta * kronecker_delta(gamma, chi)
            + displacement_alpha * displacement_gamma * kronecker_delta(beta, chi)
        )
        + norm**4
        * (
            kronecker_delta(alpha, beta) * kronecker_delta(gamma, chi)
            + kronecker_delta(alpha, gamma) * kronecker_delta(beta, chi)
            + kronecker_delta(alpha, chi) * kronecker_delta(beta, gamma)
        )
    )
