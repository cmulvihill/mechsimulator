import pandas as pd
from mechsimulator.simulator import sens as sim_sens


def write_file(sens_coeffs, target_spcs, temps, rxn_names, ref_results,
               filename='sens_results.xlsx'):

    print('Writing results to Excel...')

    # Get the array of sorted sens_coeffs
    sorted_idxs = sim_sens.get_sorted_idxs(sens_coeffs)
    sorted_sens_coeffs = sim_sens.get_sorted_sens_coeffs(sens_coeffs,
                                                         sorted_idxs)
    sorted_rxn_names = sim_sens.get_sorted_rxn_names(sorted_idxs, rxn_names)

    with pd.ExcelWriter(filename) as writer:
        # Each species gets three sheets: sorted, unsorted, and ref_results
        for spc_idx, spc in enumerate(target_spcs):
            # Unsorted sens
            spc_sens_array = sens_coeffs[:, :, spc_idx]
            sens_df = pd.DataFrame(spc_sens_array, index=rxn_names)
            sheet_name = f'{spc}, unsorted'
            sens_df.to_excel(writer, sheet_name=sheet_name, header=temps)
            # Sorted sens
            sorted_spc_sens_array = sorted_sens_coeffs[:, :, spc_idx]
            sorted_spc_rxn_names = sorted_rxn_names[:, spc_idx]
            sorted_sens_df = pd.DataFrame(sorted_spc_sens_array,
                                          index=sorted_spc_rxn_names)
            sheet_name = f'{spc}, sorted'
            sorted_sens_df.to_excel(writer, sheet_name=sheet_name, header=temps)
            # Reference concentrations
            spc_ref_results = ref_results[:, spc_idx]
            ref_results_df = pd.DataFrame(spc_ref_results, index=temps)
            sheet_name = f'{spc}, ref_results'
            ref_results_df.to_excel(writer, sheet_name=sheet_name)
