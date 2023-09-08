import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline


def mult_mechs(sorted_sens_coeffs, sorted_rxn_names, targs, temps,
               ref_results):

    nmechs = np.shape(sorted_sens_coeffs)[0]  # first dim is nmechs
    for mech_idx in range(nmechs):
        single_mech_sens_coeffs = sorted_sens_coeffs[mech_idx]
        single_mech_rxn_names = sorted_rxn_names[mech_idx]
        single_mech_ref_results = ref_results[mech_idx]
        # NOTE: will probably need to fix sorted_rxn_names to be specific to the
        # mechanism as well
        write_file(single_mech_sens_coeffs, single_mech_rxn_names, targs,
                   temps, single_mech_ref_results)


def write_file(single_mech_sens_coeffs, sorted_rxn_names, targs, temps,
               ref_results, filename='sens_results.xlsx'):
    """

    :param single_mech_sens_coeffs: sens coeffs for a single mechanism
    :type single_mech_sens_coeffs: np.ndarray of shape (nrxns, nconds, ntargs,
        ntimes) if time-resolved or (nrxns, nconds, ntargs)
    :param sorted_rxn_names: not sure...
    :param targs:
    :param temps:
    :param ref_results:
    :param filename:
    :return:
    """

    print('Writing results to Excel...')

    # Get the array of sorted sens_coeffs
    # sorted_idxs = sim_sens.get_sorted_idxs(sens_coeffs)
    # sorted_sens_coeffs = sim_sens.get_sorted_sens_coeffs(sens_coeffs,
    #                                                      sorted_idxs)
    # sorted_rxn_names = sim_sens.get_sorted_rxn_names(sorted_idxs, rxn_names)

    nrxns = len(single_mech_sens_coeffs)

    with pd.ExcelWriter(filename) as writer:
        # Each species gets three sheets: sorted, unsorted, and ref_results
        # ONLY TWO! for now...
        for targ_idx, targ in enumerate(targs):
            # # Unsorted sens
            # spc_sens_array = sens_coeffs[:, :, targ_idx]
            # sens_df = pd.DataFrame(spc_sens_array, index=rxn_names)
            # sheet_name = f'{spc}, unsorted'
            # sens_df.to_excel(writer, sheet_name=sheet_name, header=temps)

            # Sorted sens
            try:
                sorted_spc_sens_array = single_mech_sens_coeffs[:, :, targ_idx]
                sorted_spc_rxn_names = sorted_rxn_names[:, targ_idx]
            except:
                breakpoint()

            # Note:
            # sorted_sens_df = pd.DataFrame(
            #     sorted_spc_sens_array, index=sorted_spc_rxn_names)
            # sheet_name = f'{spc}, sorted'
            # sorted_sens_df.to_excel(writer, sheet_name=sheet_name, header=temps)
            trans_sorted_spc_sens_array = np.transpose(sorted_spc_sens_array)
            sorted_sens_df = pd.DataFrame(
                trans_sorted_spc_sens_array, index=temps)

            sheet_name = f'{targ}, sorted'
            sorted_sens_df.to_excel(writer, sheet_name=sheet_name,
                                    header=sorted_spc_rxn_names)

            # # Smooth the sorted data and write to a sheet
            # THIS CAUSES WEIRD ERRORS!?
            # smooth_sorted_spc_sens_array = np.empty_like(sorted_spc_sens_array)
            # for rxn_idx in range(nrxns):
            #     rxn_sens = sorted_spc_sens_array[rxn_idx]
            #     spl = UnivariateSpline(temps, rxn_sens, k=5)
            #     fitted = spl(temps)
            #     smooth_sorted_spc_sens_array[rxn_idx] = fitted
            #     # breakpoint()
            #
            # trans_smooth_sorted_spc_sens_array = np.transpose(
            #     smooth_sorted_spc_sens_array)
            # smooth_sorted_sens_df = pd.DataFrame(
            #     trans_smooth_sorted_spc_sens_array, index=temps)
            # sheet_name = f'{spc}, sorted, smooth'
            # smooth_sorted_sens_df.to_excel(writer, sheet_name=sheet_name,
            #                         header=sorted_spc_rxn_names)

            # Write the reference concentrations to a sheet
            spc_ref_results = ref_results[:, targ_idx]
            ref_results_df = pd.DataFrame(spc_ref_results, index=temps)
            sheet_name = f'{targ}, ref_results'
            ref_results_df.to_excel(writer, sheet_name=sheet_name)
