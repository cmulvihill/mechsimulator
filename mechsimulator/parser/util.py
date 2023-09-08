""" Provides common functions for parsing files
"""

import numpy as np


MEAS_TYPE_DIMS = {
    'ion':          4,
    'abs':          3,
    'emis':         3,
    'pressure':     3,
    'temp':         3,
    'burner_conc':  3,
    'burner_temp':  3,
    'conc':         3,
    'idt':          2,
    'outlet':       2,
    'lfs':          2,
}


def chk_entry(entry):
    """ Converts a value to None if it is either '-' or NaN, the latter of which
        means it was blank in the Excel file

        :param entry: entry from a Pandas dataframe that was read from Excel
        :type entry: either a str or a float
        :return chkd_entry: either the exact same as entry or None
        :rtype: either the same type as entry or None if it was '-' or NaN
    """

    if isinstance(entry, str) and entry == '-':
        chkd_entry = None
    elif isinstance(entry, float) and np.isnan(entry):
        chkd_entry = None
    else:
        chkd_entry = entry

    return chkd_entry


def get_exp_dims(exp_set):
    """ Gets the dimensions of the results of an exp set. These dimensions will
        be the same for either the experimental result or a mechanism simulation

        :param exp_set: object describing a set of experiments
        :type exp_set: dict
        :return ndims: the number of dimensions of the experiment
        :rtype: int
    """

    meas_type = exp_set['overall']['meas_type']
    ndims = MEAS_TYPE_DIMS[meas_type]

    return ndims