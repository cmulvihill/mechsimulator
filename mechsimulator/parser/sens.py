import numpy as np
import pandas as pd


def read_file(filename, spc_idxs=None):
    """ Reads an Excel file that contains sensitivity calcs as stored by the
        write_file function

        :param filename: the Excel filename
        :type filename: str
        :param spc_idxs: the list of species
        :type spc_idxs: list [spc_idx1, spc_idx2, ...]
        :return sens_coeffs:
        :rtype: Numpy array of
        :return rxn_names:
        :rtype:
        :return target_spcs:
        :rtype:
        :return temps:
        :rtype:
        :return ref_results:
        :rtype:
        sens_coeffs, rxn_names, target_spcs, temps, ref_results
    """

    print('Reading Excel file...')
    # Get the shapes of the various variables
    sheet_names = pd.ExcelFile(filename, engine='openpyxl').sheet_names
    if spc_idxs is not None:
        assert isinstance(spc_idxs, list), ('spc_idxs should be a list or None')
        num_spcs = len(spc_idxs)
    else:
        num_spcs = int(len(sheet_names)/3)  # 3 sheet/spc
    for sheet_name in sheet_names:
        split_name = str(sheet_name).split()
        if split_name[1] == 'unsorted':
            df = pd.read_excel(filename, sheet_name=sheet_name, index_col=0,
                               engine='openpyxl')
            num_rxns = len(df.index)
            num_temps = len(df.columns)
            rxn_names = np.array(df.index, dtype=object)
            temps = np.array(df.columns)
            break  # just do the first sheet

    # Loop over each sheet
    sens_coeffs = np.ndarray((num_rxns, num_temps, num_spcs))
    ref_results = np.ndarray((num_temps, num_spcs))
    target_spcs = []
    plotted_spc_idx = 0
    for sheet_idx, sheet_name in enumerate(sheet_names):
        spc_idx = int(sheet_idx / 3)
        if spc_idxs is not None:
            if spc_idx not in spc_idxs:
                continue  # skip current spc if it's not in the input spc_idxs
        split_name = str(sheet_name).split(',')

        # Get the values from the unsorted and ref_results sheets
        if split_name[1].strip() == 'unsorted':
            df = pd.read_excel(filename, sheet_name=sheet_name, index_col=0,
                               engine='openpyxl')
            sens_coeffs[:, :, spc_idx] = df.to_numpy()
            target_spcs.append(split_name[0])
        elif split_name[1].strip() == 'ref_results':
            df = pd.read_excel(filename, sheet_name=sheet_name, index_col=0,
                               engine='openpyxl')
            ref_results[:, spc_idx] = df.to_numpy()[:, 0]

    return sens_coeffs, rxn_names, target_spcs, temps, ref_results
