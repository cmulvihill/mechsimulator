import numpy as np
from mechsimulator.simulator import outcome


def single_mech(conds_dct, gas, reac_type, meas_type, xdata, ydata_shape,
                factor=0.01):

    if reac_type == 'jsr':
        sens_coeffs = jsr(conds_dct, gas, meas_type, ydata_shape, factor=factor)
    elif reac_type == 'st':
        sens_coeffs = st(conds_dct, gas, meas_type, xdata, ydata_shape,
                         factor=factor)
    elif reac_type == 'pfr':
        sens_coeffs = pfr(conds_dct, gas, meas_type, xdata, ydata_shape,
                          factor=factor)
    elif reac_type == 'free_flame':
        sens_coeffs = free_flame(conds_dct, gas, meas_type, ydata_shape,
                                 factor=factor)
    elif reac_type == 'const_t_p':
        sens_coeffs = const_t_p(conds_dct, gas, meas_type, xdata, ydata_shape,
                                factor=factor)
    elif reac_type == 'rcm':
        sens_coeffs = rcm(conds_dct, gas, meas_type, xdata, ydata_shape,
                                factor=factor)
    else:
        raise NotImplementedError(
            f"reac_type '{reac_type}' is not implemented for sens!")

    return sens_coeffs


def const_t_p(conds_dct, gas, meas_type, xdata, ydata_shape, factor=0.01):

    # Get the reference results (used as baseline for sens calcs)
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    ref_result = outcome.const_t_p(
        conds_dct, gas, meas_type, xdata, outcome_ydata_shape)

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.full(ydata_shape, np.nan)
    for rxn_idx in range(num_rxns):
        current_rxn = gas.reactions()[rxn_idx].equation
        print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
        gas.set_multiplier(1.0)  # reset all multipliers to  original values
        gas.set_multiplier(1 + factor, rxn_idx)
        # Run simulation and calculate sens coefficients
        rxn_result = outcome.const_t_p(
            conds_dct, gas, meas_type, xdata, outcome_ydata_shape)
        sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
        sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs


def free_flame(conds_dct, gas, meas_type, ydata_shape, factor=0.01):

    # Get the reference results (used as baseline for sens calcs)
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    ref_result, prev_solns = outcome.free_flame(
        conds_dct, gas, meas_type, outcome_ydata_shape)

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.full(ydata_shape, np.nan)
    for rxn_idx in range(num_rxns):
        current_rxn = gas.reactions()[rxn_idx].equation
        print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
        gas.set_multiplier(1.0)  # reset all multipliers to the original values
        gas.set_multiplier(1 + factor, rxn_idx)
        # Run simulation and calculate sens coefficients
        rxn_result, _ = outcome.free_flame(
            conds_dct, gas, meas_type, outcome_ydata_shape,
            prev_solns=prev_solns)
        sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
        sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs


def rcm(conds_dct, gas, meas_type, xdata, ydata_shape, factor=0.01):

    # Get the reference results (used as baseline for sens calcs)
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    ref_result = outcome.rcm(
        conds_dct, gas, meas_type, xdata, outcome_ydata_shape)

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.full(ydata_shape, np.nan)

    # Hardcoding for the stereo WIREs paper
    hardcoded_rxn_idxs =  [0, 3, 5, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21,
                           22, 23, 28, 31, 32, 33, 37, 38, 42, 44, 47, 49, 51,
                           53, 54, 55, 59, 61, 63, 65, 67, 70, 72, 73, 74, 75,
                           77, 79, 83, 87, 88, 89, 93, 97, 98, 101, 102, 105,
                           110, 111, 112, 115, 117, 119, 121, 122, 124, 125,
                           126, 131, 132, 134, 136, 138, 140, 141, 143, 144,
                           145, 146, 148, 150, 152, 153, 156, 157, 159, 160,
                           163, 164, 166, 167, 170, 175, 176, 184, 187, 188,
                           190, 191, 194, 196, 201, 203, 204, 205, 206, 208,
                           209, 216, 218, 219, 221, 222, 223, 228, 229, 231,
                           233, 234, 236, 238, 239, 240, 242, 243, 244, 249,
                           252, 255, 256, 258, 260, 263, 265, 266, 268, 270,
                           271, 272, 275, 279, 281, 282, 283, 284, 286, 287,
                           288, 290, 291, 292, 293, 295, 297, 298, 302, 303,
                           304, 309, 310, 312, 313, 315, 316, 320, 321, 323,
                           324, 329, 332, 334, 335, 337, 341, 342, 346, 350,
                           354, 355, 357, 361, 363, 364, 365, 367, 368, 369,
                           370, 371, 374, 375, 377, 380, 381, 384, 385, 388,
                           389, 390, 391, 392, 394, 396, 401, 402, 408, 410,
                           411, 412, 413, 418, 420, 422, 424, 425, 426, 433,
                           435, 441, 442, 443, 446, 447, 448, 451, 452, 453,
                           456, 457, 462, 463, 464, 467, 470, 472, 473, 477,
                           481, 488, 489, 492, 493, 495, 497, 498, 499, 501,
                           503, 506, 507, 509, 511, 512, 513, 519, 521, 524,
                           526, 531, 533, 534, 535, 536, 537, 538, 541, 543,
                           544, 546, 547, 552, 553, 557, 558, 560, 566, 569,
                           570, 571, 574, 576, 577, 578, 580, 581, 591, 592,
                           596, 603, 604, 610, 614, 616, 617, 619, 622, 623,
                           625, 626, 627, 629, 637, 649, 651, 652, 653, 654,
                           660, 662]

    for rxn_idx in range(num_rxns):
        if rxn_idx in hardcoded_rxn_idxs:
            current_rxn = gas.reactions()[rxn_idx].equation
            print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
            gas.set_multiplier(1.0)  # reset all multipliers to original values
            gas.set_multiplier(1 + factor, rxn_idx)
            # Run simulation and calculate sens coefficients
            rxn_result = outcome.rcm(
                conds_dct, gas, meas_type, xdata, outcome_ydata_shape)
            sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
            sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs


def st(conds_dct, gas, meas_type, xdata, ydata_shape, factor=0.01):

    # Get the reference results (used as baseline for sens calcs)
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    ref_result = outcome.st(
        conds_dct, gas, meas_type, xdata, outcome_ydata_shape)

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.full(ydata_shape, np.nan)

    # Hardcoding for Jaeyoung's C2H6 simulations
    # hardcoded_rxn_idxs = [279, 284, 253, 285, 59, 60, 48, 204, 231, 214, 289, 276, 205,
    #             158, 254, 2, 3, 326, 152, 271, 262, 250, 156, 210, 568, 1]

    # Hardcoding for Jaeyoung's C2H6 simulations; updated mech (just added 1 to
    # all numbers above 7 from the above list since he added one new reaction in
    # the first 8) (actually, being lazy and just subtracting 1 from the numbers
    # below 7, then adding 1 to all)
    hardcoded_rxn_idxs = [279, 284, 253, 285, 59, 60, 48, 204, 231, 214, 289, 276, 205,
                158, 254, 1, 2, 326, 152, 271, 262, 250, 156, 210, 568, 0]
    hardcoded_rxn_idxs = np.array(hardcoded_rxn_idxs)
    hardcoded_rxn_idxs += 1

    # Hardcoding for Curran C3H8 paper (using Luna's mech!)
    # hardcoded_rxn_idxs = [9,596,118,656,472,365,417,10,364,169,369,164,393,14]

    # Hardcoding for Curran C3H8 paper (using full NUIG1.1 mech!)
    # hardcoded_rxn_idxs = [642,37,38,177,776,125,739,693,748,641,687,679,688]

    for rxn_idx in range(num_rxns):
        if rxn_idx in hardcoded_rxn_idxs:
            current_rxn = gas.reactions()[rxn_idx].equation
            print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
            gas.set_multiplier(1.0)  # reset all multipliers to original values
            gas.set_multiplier(1 + factor, rxn_idx)
            # Run simulation and calculate sens coefficients
            rxn_result = outcome.st(
                conds_dct, gas, meas_type, xdata, outcome_ydata_shape)
            sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
            sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs


def jsr(conds_dct, gas, meas_type, ydata_shape, factor=0.01):
    """ Calculates sensitivity coefficients for any number of target species
        across a range of conditions for a JSR simulation

    """

    # Get the reference results (used as baseline for sens calcs) and the
    # prev_soln, which helps converge to a solution
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    # Run solver twice to get ref results: once with no starting point, and then
    # with the previous solution from the first attempt
    _, prev_solns = outcome.jsr(
        conds_dct, gas, meas_type, outcome_ydata_shape, output_all=True)
    ref_result, _ = outcome.jsr(
        conds_dct, gas, meas_type, outcome_ydata_shape, prev_solns=prev_solns)

    # Hardcoding for the stereo WIREs paper
    # hardcoded_rxn_idxs = [0, 3, 5, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21,
    #                       22, 23, 28, 31, 32, 33, 37, 38, 42, 44, 47, 49, 51,
    #                       53, 54, 55, 59, 61, 63, 65, 67, 70, 72, 73, 74, 75,
    #                       77, 79, 83, 87, 88, 89, 93, 97, 98, 101, 102, 105,
    #                       110, 111, 112, 115, 117, 119, 121, 122, 124, 125,
    #                       126, 131, 132, 134, 136, 138, 140, 141, 143, 144,
    #                       145, 146, 148, 150, 152, 153, 156, 157, 159, 160,
    #                       163, 164, 166, 167, 170, 175, 176, 184, 187, 188,
    #                       190, 191, 194, 196, 201, 203, 204, 205, 206, 208,
    #                       209, 216, 218, 219, 221, 222, 223, 228, 229, 231,
    #                       233, 234, 236, 238, 239, 240, 242, 243, 244, 249,
    #                       252, 255, 256, 258, 260, 263, 265, 266, 268, 270,
    #                       271, 272, 275, 279, 281, 282, 283, 284, 286, 287,
    #                       288, 290, 291, 292, 293, 295, 297, 298, 302, 303,
    #                       304, 309, 310, 312, 313, 315, 316, 320, 321, 323,
    #                       324, 329, 332, 334, 335, 337, 341, 342, 346, 350,
    #                       354, 355, 357, 361, 363, 364, 365, 367, 368, 369,
    #                       370, 371, 374, 375, 377, 380, 381, 384, 385, 388,
    #                       389, 390, 391, 392, 394, 396, 401, 402, 408, 410,
    #                       411, 412, 413, 418, 420, 422, 424, 425, 426, 433,
    #                       435, 441, 442, 443, 446, 447, 448, 451, 452, 453,
    #                       456, 457, 462, 463, 464, 467, 470, 472, 473, 477,
    #                       481, 488, 489, 492, 493, 495, 497, 498, 499, 501,
    #                       503, 506, 507, 509, 511, 512, 513, 519, 521, 524,
    #                       526, 531, 533, 534, 535, 536, 537, 538, 541, 543,
    #                       544, 546, 547, 552, 553, 557, 558, 560, 566, 569,
    #                       570, 571, 574, 576, 577, 578, 580, 581, 591, 592,
    #                       596, 603, 604, 610, 614, 616, 617, 619, 622, 623,
    #                       625, 626, 627, 629, 637, 649, 651, 652, 653, 654,
    #                       660, 662]

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions  # might differ from sens_coeffs for this mech
    hardcoded_rxn_idxs = range(num_rxns)  # run all rxns
    sens_coeffs = np.full(ydata_shape, np.nan)
    for rxn_idx in range(num_rxns):
        if rxn_idx in hardcoded_rxn_idxs:
            current_rxn = gas.reactions()[rxn_idx].equation
            print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
            gas.set_multiplier(1.0)  # reset all multipliers to the original values
            gas.set_multiplier(1 + factor, rxn_idx)
            # Run simulation and calculate sens coefficients
            rxn_result, _ = outcome.jsr(conds_dct, gas, meas_type,
                                        outcome_ydata_shape, prev_solns=prev_solns)
            sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
            sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs


def pfr(conds_dct, gas, meas_type, xdata, ydata_shape, factor=0.01):
    """ Calculates sensitivity coefficients for any number of target species
        across a range of temperatures for a PFR simulation

        :param factor: factor by which to perturb A factors
        :type factor: float
        :return sens_coeffs: sens coeffs for each rxn, temp, and species
        :rtype: Numpy array of shape (num_rxns, num_temps, num_spcs)
    """

    # Get the reference results (used as baseline for sens calcs) and the
    # prev_soln, which helps converge to a solution
    outcome_ydata_shape = ydata_shape[1:]  # strip first dim (# of rxns)
    ref_result = outcome.pfr(conds_dct, gas, meas_type, xdata,
                             outcome_ydata_shape)

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions  # might differ from sens_coeffs for this mech
    sens_coeffs = np.full(ydata_shape, np.nan)
    for rxn_idx in range(num_rxns):
        current_rxn = gas.reactions()[rxn_idx].equation
        print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
        gas.set_multiplier(1.0)  # reset all multipliers to the original values
        gas.set_multiplier(1 + factor, rxn_idx)
        # Run simulation and calculate sens coefficients
        rxn_result = outcome.pfr(
            conds_dct, gas, meas_type, xdata, outcome_ydata_shape)
        sens_coeff = (rxn_result - ref_result) / (ref_result * factor)
        sens_coeffs[rxn_idx, :] = sens_coeff

    return sens_coeffs
