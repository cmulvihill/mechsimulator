import numpy as np
import pandas as pd
from mechsimulator.plotter import util as plot_util
from mechsimulator.simulator import util as sim_util


def write_mech_results(exp_set, mech_results, mech_nicknames=None):
    """

    :param exp_set:
    :param mech_results: contains simulation data for any number of mechanisms
    :type mech_results: Numpy array of shape (num_mechs, num_temps, num_spcs)
        (this is only true for JSR; will be different for other experiments)
    :return:
    """
    nmechs, ntemps, nspcs = np.shape(mech_results)
    descr = exp_set['overall']['description']
    target_spcs = list(exp_set['spc'].keys())
    mech_nicknames = [f'mech{mech_idx + 1}' for mech_idx in range(nmechs)] or \
        mech_nicknames
    assert nmechs == len(mech_nicknames)
    temps = sim_util.get_plot_conds(exp_set)
    for mech_idx, mech_nickname in enumerate(mech_nicknames):
        filename = f'{descr}_{mech_nickname}.xlsx'
        mech_result = mech_results[mech_idx, :, :]
        with pd.ExcelWriter(filename) as writer:
            mech_result_df = pd.DataFrame(mech_result, index=temps)
            if exp_set['overall']['meas_type'] == 'lfs':
                # Only single column for LFS
                mech_result_df.to_excel(writer)
            elif exp_set['overall']['reac_type'] == 'rcm' and \
                exp_set['overall']['meas_type'] == 'idt':
                header = exp_set['plot']['idt_targ'][0]
                mech_result_df.to_excel(writer, header=header)
            else:
                mech_result_df.to_excel(writer, header=target_spcs)


def write_mech_results_time(exp_set, mech_results, xdata, mech_nicknames=None):
    """

    :param exp_set:
    :param mech_results: contains simulation data for any number of mechanisms
    :type mech_results: Numpy array of shape (nmechs, nconds, ntargs, ntimes)
    :return:
    """

    nmechs, nconds, nspcs, ntimes = np.shape(mech_results)
    descr = exp_set['overall']['description']
    target_spcs = list(exp_set['spc'].keys())
    cond_titles, _, _ = plot_util.get_cond_titles(exp_set, 'plot')
    mech_nicknames = [f'mech{mech_idx + 1}' for mech_idx in range(nmechs)] or \
        mech_nicknames
    assert nmechs == len(mech_nicknames)

    for mech_idx, mech_nickname in enumerate(mech_nicknames):
        filename = f'{descr}_{mech_nickname}.xlsx'
        with pd.ExcelWriter(filename) as writer:
            for cond_idx, cond in enumerate(cond_titles):
                sheet_name = f'{cond}'
                cond_result = mech_results[mech_idx, cond_idx, :, :]
                mech_result_df = pd.DataFrame(np.transpose(cond_result),
                                              index=xdata)
                mech_result_df.to_excel(writer, header=target_spcs,
                                        sheet_name=sheet_name)


# def write_exp_data(exp_set, pathname='results'):
#
#     exp_data, temps = comparisons.get_exp_data_jsr(exp_set)
#     source = exp_set['overall']['source']
#     description = exp_set['overall']['description']
#     target_spcs = list(exp_set['spc'].keys())
#     filename = source + ', ' + description + '.xlsx'
#
#     # Each species gets its own sheet
#     with pd.ExcelWriter(pathname + '/' + filename) as writer:
#         for spc_idx, target_spc in enumerate(target_spcs):
#             spc_data = exp_data[spc_idx, :]  # all data for one spc
#             # If all entries for the species are empty, print a notice
#             if all(np.isnan(spc_data)):
#                 print(f'No experimental data found for spc {target_spc}')
#             # Otherwise, write to the file
#             else:
#                 spc_data = exp_data[spc_idx, :]
#                 spc_data_df = pd.DataFrame(spc_data, index=temps)
#                 sheet_name = target_spc
#                 spc_data_df.to_excel(writer, sheet_name=sheet_name)
