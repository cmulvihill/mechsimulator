import numpy as np
from itertools import repeat
from functools import partial
from multiprocessing import Pool, freeze_support
from mechsimulator.simulator import outcome


def single_mech(conds_dct, gas, reac_type, meas_type, xdata, ydata_shape,
                factor=0.02):

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

    # Hardcoding for the stereo WIREs paper: January 2024 attempt (coarse grid)
    #hardcoded_rxn_idxs = [

# 5, 6, 8, 9, 11, 12, 15, 17, 18, 20, 21, 22, 24, 26, 28, 30, 34, 35, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50, 51, 52, 54, 56, 58, 59, 60, 61, 62, 65, 66, 68, 69, 71, 77, 80, 81, 82, 84, 85, 88, 89, 90, 91, 93, 94, 97, 98, 99, 101, 102, 104, 107, 108, 109, 110, 112, 115, 116, 117, 121, 122, 123, 124, 125, 126, 127, 129, 130, 131, 132, 134, 135, 136, 139, 140, 142, 144, 145, 147, 156, 157, 160, 161, 162, 164, 167, 168, 169, 172, 173, 174, 175, 177, 179, 182, 183, 184, 185, 186, 188, 192, 199, 200, 202, 203, 204, 207, 210, 212, 216, 217, 218, 219, 222, 223, 224, 227, 229, 233, 234, 238, 239, 240, 244, 245, 248, 251, 252, 255, 257, 258, 259, 260, 262, 263, 266, 267, 268, 269, 270, 271, 273, 276, 277, 278, 279, 280, 282, 284, 289, 291, 292, 295, 299, 302, 304, 309, 310, 311, 312, 313, 315, 318, 325, 329, 330, 334, 335, 336, 340, 341, 344, 346, 347, 348, 350, 352, 353, 357, 358, 362, 363, 364, 366, 369, 372, 373, 376, 377, 378, 383, 386, 387, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 401, 402, 403, 404, 405, 406, 412, 413, 414, 415, 416, 418, 419, 420, 421, 423, 425, 426, 432, 434, 436, 438, 441, 442, 445, 447, 448, 449, 451, 452, 455, 457, 458, 459, 463, 465, 466, 467, 468, 472, 473, 476, 477, 479, 480, 481, 485, 486, 487, 488, 489, 493, 494, 495, 498, 499, 500, 502, 503, 506, 509, 512, 515, 517, 518, 519, 521, 522, 523, 525, 527, 528, 529, 530, 532, 533, 534, 540, 542, 544, 546, 549, 551, 555, 556, 558, 559, 560, 562, 564, 566, 567, 568, 569, 571, 572, 574, 576, 577, 578, 581, 582, 583, 586, 587, 588, 590, 593, 596, 597, 598, 599, 600, 601, 602, 604, 606, 613, 618, 621, 625, 626, 627, 628, 629, 631, 632, 633, 634, 635, 637, 639, 640, 641, 642, 643, 647, 648, 650, 651, 652, 655, 658, 659, 662, 665, 669, 670, 676, 677, 680, 682, 684, 685, 689, 690, 691, 696, 697, 701, 702, 706, 707, 708, 710, 713, 714, 715, 719, 720, 721, 723, 724, 730, 731, 732, 735, 736, 738, 739, 740, 742, 744, 745, 748, 751, 752, 754, 755, 759, 761, 762, 764, 767, 769, 771, 772, 774, 777, 782, 783, 789, 810, 811, 852, 853, 866, 867, 922, 923, 950, 951, 1022, 1023, 1079, 1080, 1125, 1126, 1217, 1218, 1223, 1224, 1239, 1240, 1273, 1274, 1342, 1343, 1374, 1375, 1432, 1433, 1550, 1551, 1669, 1670, 1690, 1691, 1708, 1709, 1718, 1719, 1722, 1723, 1757, 1758, 1780, 1781, 1817, 1818, 1921, 1922, 1931, 1932, 2024, 2025, 2113, 2114, 2126, 2127, 2144, 2145, 2222, 2223, 2247, 2248, 2254, 2255, 2324, 2325, 2342, 2343, 2360, 2361, 2364, 2365, 2366, 2367, 2383, 2384, 2540, 2541, 2623, 2624, 2625, 2626, 2643, 2644, 2649, 2650, 2651, 2652, 2672, 2673, 2682, 2683, 2696, 2697, 2716, 2717, 2723, 2724, 2734, 2735, 2770, 2771, 2848, 2849, 2889, 2890, 2899, 2900, 2904, 2905, 2920, 2921, 2939, 2940, 2954, 2955, 2959, 2960, 3071, 3072, 3100, 3101, 3163, 3164, 3286, 3287, 3656, 3657, 3683, 3684, 3706, 3707, 3720, 3721, 3736, 3737, 3802, 3803]

    # Hardcoding for the stereo WIREs paper: January 2024 attempt (fine grid)
    hardcoded_rxn_idxs = [20, 60, 223, 291, 518, 578, 588, 625, 633, 634, 650, 2540, 2541, 2940, 3071, 3072, 3706, 3707, 3720, 3721]

    # Hardcoding for the stereo WIREs paper: August attempt but for high-res
    #hardcoded_rxn_idxs = [10, 12, 89, 95, 114, 190, 221, 308, 318, 382, 420, 464, 465, 509, 554, 571, 615, 639, 669, 674]

    # Hardcoding for the stereo WIREs paper: August attempt
    #hardcoded_rxn_idxs =  [1, 2, 10, 12, 13, 14, 15, 18, 19, 20, 21, 25, 26, 29, 30, 31, 32, 34, 35, 36, 37, 43, 46, 47, 49, 51, 52, 53, 54, 55, 60, 61, 65, 66, 69, 70, 73, 78, 80, 81, 83, 84, 89, 91, 92, 94, 95, 96, 99, 101, 102, 104, 107, 109, 114, 115, 118, 121, 124, 132, 133, 135, 138, 139, 140, 143, 144, 146, 147, 149, 151, 153, 156, 158, 159, 161, 165, 166, 169, 171, 172, 174, 177, 179, 183, 184, 185, 190, 191, 194, 195, 196, 202, 203, 204, 205, 206, 209, 210, 215, 218, 220, 221, 222, 223, 224, 228, 230, 232, 234, 236, 240, 243, 245, 248, 252, 253, 254, 255, 256, 257, 258, 264, 265, 268, 269, 271, 274, 276, 277, 280, 281, 282, 286, 289, 291, 293, 297, 301, 303, 304, 306, 307, 308, 309, 316, 317, 318, 319, 320, 323, 325, 330, 332, 334, 336, 337, 338, 340, 343, 344, 346, 347, 348, 349, 351, 352, 353, 355, 359, 360, 361, 364, 365, 366, 368, 370, 375, 379, 381, 382, 385, 386, 387, 389, 390, 391, 396, 399, 411, 413, 414, 418, 420, 421, 422, 423, 425, 428, 429, 432, 433, 435, 438, 443, 446, 447, 449, 450, 454, 455, 456, 457, 458, 459, 460, 462, 464, 465, 474, 475, 476, 477, 478, 482, 484, 489, 490, 494, 496, 498, 499, 501, 506, 509, 512, 517, 519, 523, 527, 528, 530, 536, 537, 540, 542, 544, 545, 546, 547, 549, 552, 554, 555, 557, 560, 563, 564, 567, 568, 569, 570, 571, 576, 577, 580, 582, 585, 586, 587, 588, 590, 596, 597, 600, 601, 602, 603, 605, 609, 612, 615, 618, 623, 624, 625, 633, 634, 636, 637, 638, 639, 642, 644, 646, 648, 649, 651, 656, 661, 663, 665, 669, 674, 677, 678, 680, 682]


    # Hardcoding for the stereo WIREs paper: April attempt
    #hardcoded_rxn_idxs =  [0, 3, 5, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21,
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

    # Trying with multiproc
    #pool = Pool(processes=35)
    #temp_sens_coeffs = pool.map(partial(
    #    _single_rxn, gas=gas, conds_dct=conds_dct, meas_type=meas_type, 
    #    xdata=xdata, outcome_ydata_shape=outcome_ydata_shape, 
    #    ref_result=ref_result, factor=factor, num_rxns=num_rxns), 
    #    hardcoded_rxn_idxs)
    #pool.close()
    #pool.join()
    #breakpoint()

    return sens_coeffs


def _single_rxn(rxn_idx, gas, conds_dct, meas_type, xdata, outcome_ydata_shape, ref_result, factor, num_rxns):

    current_rxn = gas.reactions()[rxn_idx].equation
    print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
    gas.set_multiplier(1.0)  # reset all multipliers to original values
    gas.set_multiplier(1 + factor, rxn_idx)
    # Run simulation and calculate sens coefficients
    rxn_result = outcome.rcm(
        conds_dct, gas, meas_type, xdata, outcome_ydata_shape)
    sens_coeff = (rxn_result - ref_result) / (ref_result * factor)

    return sens_coeff


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
    #hardcoded_rxn_idxs = [279, 284, 253, 285, 59, 60, 48, 204, 231, 214, 289, 276, 205,
    #            158, 254, 1, 2, 326, 152, 271, 262, 250, 156, 210, 568]
    #hardcoded_rxn_idxs = np.array(hardcoded_rxn_idxs)
    #hardcoded_rxn_idxs += 1

    hardcoded_rxn_idxs = [0, 1, 2]
    

    # Hardcoding for Curran C3H8 paper (using Luna's mech!)
    # hardcoded_rxn_idxs = [9,596,118,656,472,365,417,10,364,169,369,164,393,14]

    # Hardcoding for Curran C3H8 paper (using full NUIG1.1 mech!)
    # hardcoded_rxn_idxs = [642,37,38,177,776,125,739,693,748,641,687,679,688]

    # Should I take absolute value? Should ref result ever be negative?
    ref_result += np.finfo(float).eps  # add epsilon to prevent divide by 0

    exclude_spcs = ('H',)
    print(f'WARNING: leaving out all reactions involving {exclude_spcs}!!')
    for rxn_idx in range(num_rxns):
        #if rxn_idx in hardcoded_rxn_idxs:
        current_rxn = gas.reactions()[rxn_idx].equation
        for exclude_spc in exclude_spcs:
            if exclude_spc in current_rxn:
                print(f'Excluding reaction {current_rxn}')
                continue
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
