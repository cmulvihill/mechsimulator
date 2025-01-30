"""
Parses Excel files containing experimental data to obtain exp_set dictionaries
"""

import pandas as pd
import numpy as np
from mechsimulator.parser import exp_checker
from mechsimulator.parser import util
from mechsimulator.parser import spc as spc_parser

# Allowed physical quantities (keys) and:
# (1) corresponding allowed units
# (2) conversions factors to get to the internal units
# (3) full name of the quantity (for printing purposes)
# Note: the first units given for each quantity are the internal units
ALLOWED_UNITS = {
    'temp':         (('K', 'C', 'F', 'R'),
                     (1, None, None, 5.55555e-1),
                     'Temperature'),
    'pressure':     (('atm', 'bar', 'kPa', 'Pa', 'MPa', 'torr'),
                     (1, 9.86923e-1, 9.86923e-3, 9.86923e-6, 9.86923e0, 1/760),
                     'Pressure'),
    'time':         (('s', 'ms', 'micros'),
                     (1, 1.0e-3, 1.0e-6),
                     'Time'),
    'conc':         (('X', 'ppm', '%', 'molec/cm3'),
                     (1, 1.0e-6, 1.0e-2, None),
                     'Mole fraction'),
    'length':       (('m', 'cm', 'mm'),
                     (1, 1.0e-2, 1.0e-3),
                     'Length'),
    'area':         (('m2', 'cm2', 'mm2'),
                     (1, 1.0e-4, 1.0e-6),
                     'Area'),
    'vol':          (('m3', 'cm3', 'mm3'),
                     (1, 1.0e-6, 1.0e-9),
                     'Volume'),
    'abs_coeff':    (('m-1atm-1', 'cm-1atm-1',),
                     (1, 1.0e2),
                     'Absorption coefficient'),
    'abs':          (('%', 'fraction'),
                     (1, 100),
                     'Absorption'),
    'dpdt':         (('%/ms',),
                     (1,),
                     'dP/dt'),
    'mdot':         (('kg/s', 'g/s'),
                     (1, 1.0e-3,),
                     'Mass flow rate'),
    'velocity':     (('cm/s', 'm/s'),
                     (1, 1.0e2),
                     'Velocity'),
    'phi':          (('',),
                     (1,),
                     'Equivalence ratio')
}

# Mappings for alternate names (keys) to their physical quantities (values)
ALTERNATE_NAMES = {
    'path_length':          'length',
    'end_time':             'time',
    'res_time':             'time',
    'idt':                  'time',
    'timestep':             'time',
    'lfs':                  'velocity',
    'v_of_t':               'vol',
    'x_profile':            'length',
    't_profile':            'temp',
    't_profile_setpoints':  'temp',
    'half_life':            'time',
}

# Params in the 'plot' field of the 'info' sheet that should be in list form
LIST_PARAMS = ('idt_targ', 'idt_method', 'wavelength', 'active_spc')

# Number of columns in sheets
NINFO_COLS = 4  # the 'info' sheet
NEXP_COLS = 7  # all 'exp' sheets


def load_exp_set(fname):
    """ Reads an Excel file that contains data on an experiment set and returns
        an exp_set object

        :param fname: filename of .xlsx file describing an experiment set
        :type fname: str
        :return exp_set: description of a set of experiments
        :rtype: dct
    """

    # Get information on sheet names
    sheet_names = pd.ExcelFile(fname, engine='openpyxl').sheet_names
    assert 'info' in sheet_names, (
        f'There is no sheet called "info" in the Excel file {fname}.')
    del sheet_names[sheet_names.index('info')]  # remove 'info' sheet

    # Read excel file and create the exp_set and exp_objs
    exp_set = read_info_sheet_new(fname)  # info sheet
    exp_objs = []
    for sheet_name in sheet_names:
        exp_objs.append(read_exp_sheet_new(fname, sheet_name, exp_set))
    exp_set['exp_objs'] = exp_objs

    # Run some checks (returns objects since minor changes can be made)
    exp_set = exp_checker.chk_exp_set(exp_set)

    # Create the exp_data and xdata arrays and store
    exp_ydata, exp_xdata = get_exp_data(exp_set)
    exp_set['overall']['exp_ydata'] = exp_ydata
    exp_set['overall']['exp_xdata'] = exp_xdata

    return exp_set


def read_info_sheet_new(fname):
    """ Reads the 'info' sheet describing overall information on an exp set

        :param fname: filename of .xlsx file describing an experiment set
        :type fname: str
        :return: exp_set: description of a set of experiments; used for spc list
        :rtype exp_set: dct
    """

    # Load the dataframe and initialize the object
    print(f'Reading the "info" sheet in Excel file {fname}...')
    df = pd.read_excel(fname, sheet_name='info', header=None, skiprows=1,
                       engine='openpyxl')
    assert df.shape[1] >= 4, f'"info" sheets must have at least 4 columns'
    exp_set = {'overall': {}, 'plot': {}, 'plot_format': {}, 'mix': {},
               'spc': {}, 'sim_opts': {}, 'exp_objs': []}

    # Loop over each row
    for _, row in df.iterrows():
        group = row[0]
        # Note: this if/else is necessary because openpyxl returns some rows
        # that are all NaNs
        if isinstance(group, str):
            assert group in exp_checker.ALLOWED_INFO_GROUPS, (
                f"The group '{group}' is not allowed in the 'info' sheet. Options "
                f"are: {exp_checker.ALLOWED_INFO_GROUPS.keys()}")
            # Read the row based on the group name
            if group == 'overall':
                _overall(row, exp_set, sheet_type='info')
            elif group == 'plot':
                _plot(row, exp_set)
            elif group == 'plot_format':
                _plot_format(row, exp_set)
            elif group == 'mix':
                _mix(row, exp_set, sheet_type='info')
            elif group == 'spc':
                _spc(row, exp_set)
            elif group == 'sim_opts':
                _sim_opts(row, exp_set)
            elif group == 'ignore_row':
                pass
        else:
            assert np.isnan(group)  # check that the group is NaN

    return exp_set


def read_exp_sheet_new(fname, sheet_name, exp_set):
    """ Reads an Excel sheet describing a single experiment

        :param fname: filename of .xlsx file describing an experiment set
        :type fname: str
        :param sheet_name: name of the sheet in the Excel file
        :type sheet_name: str
        :param: exp_set: description of a set of experiments (used for spc list)
        :type exp_set: dct
        :return exp_obj: description of a single experiment
        :rtype: dct
    """

    # Load the dataframe and initialize the object
    print(f'Reading sheet {sheet_name} in Excel file {fname}...')
    df = pd.read_excel(fname, sheet_name=sheet_name, header=None, skiprows=1,
                       engine='openpyxl')
    assert df.shape[1] >= NEXP_COLS, (
        f'Experimental sheets must have at least {NEXP_COLS} columns')
    exp_obj = {'overall': {}, 'conds': {}, 'mix': {}, 'result': {}}

    # Loop over each row
    for _, row in df.iterrows():
        group = row[0]
        assert group in exp_checker.ALLOWED_EXP_GROUPS, (
            f"The group '{group}' is not allowed in exp sheets. Options "
            f"are: {exp_checker.ALLOWED_EXP_GROUPS.keys()}")
        # Read the row based on the group name
        if group == 'overall':
            _overall(row, exp_obj, sheet_type='exp')
        elif group in ('conds', 'result'):
            _conds_result(row, exp_obj, exp_set)
        elif group == 'mix':
            _mix(row, exp_obj, sheet_type='exp')
        elif group == 'ignore_row':
            pass

    return exp_obj


# ---- Functions for reading single rows from specific groups (alphabetical)----
def _conds_result(row, exp_obj, exp_set):
    """ Reads a 'conds' or 'result' row from an exp sheet
    """

    # Read raw data (param and raw_val read later)
    group, _, _, units, low_bnd, upp_bnd, bnd_type = row[:NEXP_COLS]

    # Read any extra params and any time series info and check the bounds
    param, extra_params = _split_param(row)
    raw_val = _time_series(row, sheet_type='exp')
    low_bnd, upp_bnd, bnd_type = _check_bounds(low_bnd, upp_bnd, bnd_type)

    # Convert the units of the raw value
    if param in exp_set['spc'].keys():  # if param is a spcs name
        val = convert_units(raw_val, 'conc', units)
    else:
        val = convert_units(raw_val, param, units)
    val_tuple = (val, low_bnd, upp_bnd, bnd_type, units)

    # Determine where to save info based on extra params
    if not extra_params:  # the usual case: no commas in 'param' field
        if param in ('idt', 'abs', 'emis'):  # if a special case
            assert exp_obj[group].get(param) is None, (
                f"The '{param}' field has already been defined! Use "
                f"a comma-separated integer to specify new instances.")
            # Store
            exp_obj[group][param] = {1: val_tuple}  # save with a 1
        else:  # otherwise, just save the value (most common case)
            # Store
            exp_obj[group][param] = val_tuple
    else:  # if there were commas in the parameter field
        observable_num = int(extra_params[0])  # int starting with 1
        # Create dct if needed
        if exp_obj[group].get(param) is None:
            exp_obj[group][param] = {}
        # If on a time array of absorption data or IDT data
        if param in ('abs', 'emis', 'idt'):
            # Store
            exp_obj[group][param][observable_num] = val_tuple
        else:  # not sure what to do in this case; should be one of the above
            raise NotImplementedError(f'not sure what to do with param {param}')
        # If on an absorption coefficient
        if param == 'abs_coeff':
            # If both a wavelength_num and spc were given
            if len(extra_params) == 2:
                spc = extra_params[1]
            # Otherwise, if only spc was given, use 1 for observable_num
            elif len(extra_params) == 1:
                observable_num = 1
                spc = extra_params[0]
            else:
                raise NotImplementedError('abs_coeff has too many params given')
            # Create dct if needed
            if exp_obj[group][param].get(observable_num) is None:
                exp_obj[group][param][observable_num] = {}
            # Store
            exp_obj[group][param][observable_num][spc] = val_tuple


def _mix(row, exp_set_or_obj, sheet_type='exp'):
    """ Reads a 'mix' row (either the 'info' or 'exp' sheets)
    """
    def get_conv_val(_param, _raw_val, _units):
        """ Converts a value to the desired internal units OR deals with values
            given via the fuel/oxid keywords
        """
        if _param not in no_units:
            _conv_val = convert_units(_raw_val, 'conc', _units)
        else:  # if in the special list of no_units
            if _param in ('fuel', 'oxid'):
                _conv_val = [entry.strip() for entry in _raw_val.split(',')]
            else:  # 'fuel_ratios' or 'oxid_ratios'
                if isinstance(_raw_val, str):
                    _conv_val = [float(ent) for ent in _raw_val.split(',')]
                else:  # if a float (i.e., single value), change to list
                    _conv_val = [_raw_val]

        return _conv_val

    _check_sheet_type(sheet_type)
    no_units = ('phi', 'fuel', 'fuel_ratios', 'oxid', 'oxid_ratios')

    if sheet_type == 'info':
        param, raw_val, units = row[1], row[2], row[3]
        conv_val = get_conv_val(param, raw_val, units)
        low_bnd, upp_bnd, bnd_type = None, None, None  # no bounds for 'info'
    else:  # exp
        _, param, raw_val, units, low_bnd, upp_bnd, bnd_type = row[:NEXP_COLS]
        conv_val = get_conv_val(param, raw_val, units)
        low_bnd, upp_bnd, bnd_type = _check_bounds(low_bnd, upp_bnd, bnd_type)
    # Store
    exp_set_or_obj['mix'][param] = (conv_val, low_bnd, upp_bnd, bnd_type, units)


def _overall(row, exp_set_or_obj, sheet_type='exp'):
    """ Reads an 'overall' row from either the 'info' or 'exp' sheets
    """

    _check_sheet_type(sheet_type)
    if sheet_type == 'info':
        param, raw_val = row[1], row[2]
    else:  # exp
        _, param, raw_val, _, _, _, _ = row[:NEXP_COLS]
    # Store
    exp_set_or_obj['overall'][param] = raw_val


def _plot(row, exp_set_or_obj):
    """ Reads a 'plot' row from the 'info' sheet
    """

    _, param, raw_val, units = row[:4]
    # If on the plotting variable info
    if param in ('start', 'end', 'inc'):
        # Check that the plotting variable has already been defined
        assert 'variable' in exp_set_or_obj['plot'].keys(), (
            f'The parameter "variable" must be defined before {param}')
        # Use the plotting variable as the quantity
        fake_param = exp_set_or_obj['plot']['variable'][0]  # e.g., 'temp'
        conv_val = convert_units(raw_val, fake_param, units)
    elif param in ('t_profile'):
        raw_val = _time_series(row, sheet_type='info', value_and_series=True)    
        conv_val = convert_units(raw_val, param, units)
        # Either create the setpoints entry or append to it
        if exp_set_or_obj['plot'].get('t_profile_setpoints') is None:
            exp_set_or_obj['plot']['t_profile_setpoints'] = [conv_val[0]]  # only first
        else: 
           exp_set_or_obj['plot']['t_profile_setpoints'].append(conv_val[0])
        # Either create the t_profile entry or append to it
        if exp_set_or_obj['plot'].get('t_profile') is None:
            exp_set_or_obj['plot']['t_profile'] = [conv_val[1]]  # only first
        else: 
           exp_set_or_obj['plot']['t_profile'].append(conv_val[1])
            
    # If on any other variable
    else:
        # Check if the row contains a time series, then convert units
        raw_val = _time_series(row, sheet_type='info')
        conv_val = convert_units(raw_val, param, units)

    # If there is a comma in the input field, split the str around it
    if isinstance(conv_val, str) and ',' in conv_val:
        assert param in LIST_PARAMS, (
            f"The param {param} in the 'plot' field of the 'info' sheet should "
            f"not be a list. Options are limited to {LIST_PARAMS}")
        conv_val = [entry.strip() for entry in conv_val.split(',')]
    # If no comma and in the LIST_PARAMS, convert str to lst
    elif param in LIST_PARAMS:
        conv_val = [conv_val]
    # Store (set bound info to None; don't use fake_param)
    if param != 't_profile':  # don't do for t_profile; handled above
        exp_set_or_obj['plot'][param] = (conv_val, None, None, None, units)


def _plot_format(row, exp_set):
    """ Reads a 'plot_format' row from the 'info' sheet
    """

    param, raw_val, units = row[1:4]
    if param in ('xlim', 'ylim'):
        conv_val = [float(entry) for entry in raw_val.split(',')]
    elif param == 'rows_cols':
        conv_val = [int(entry) for entry in raw_val.split(',')]
    elif param == 'omit_targs':
        conv_val = [entry.strip() for entry in raw_val.split(',')]
    elif param in ('plot_points', 'exp_on_top'):  # Boolean
        if raw_val == 'yes':
            conv_val = True
        elif raw_val == 'no':
            conv_val = False
        else:
            conv_val = raw_val
    else:
        conv_val = raw_val
    # Store
    exp_set['plot_format'][param] = conv_val


def _spc(row, exp_set):
    """ Reads a 'spc' row from the 'info' sheet
    """

    assert len(row) >= 6, (
        f"'spc' row {list(row)} is too short. Should have smiles, multiplicity,"
        f" charge, and excited flag given.")
    spc, smiles, mult, charge, exc_flag = row[1:6]
    inchi = spc_parser.to_inchi(spc_parser.from_smiles(smiles))
    spc_dct = {
        'inchi': inchi,
        'smiles': smiles,
        'mult': mult,
        'charge': charge,
        'exc_flag': exc_flag}
    # Store
    exp_set['spc'][spc] = spc_dct


def _sim_opts(row, exp_set):

    _, param, raw_val, units = row[:4]
    # Check if the row contains a time series, then convert units
    raw_val = _time_series(row, sheet_type='info')
    conv_val = convert_units(raw_val, param, units)
    exp_set['sim_opts'][param] = conv_val


def _time_series(row, sheet_type='exp', value_and_series=False):
    """ Checks if a row has a time series. The returned value will be either
        a time series (numpy array) with a certain number of datapoints or a
        single value

        Can be used for several different groups in either 'info' or exp sheets
    """

    # Check sheet type, read raw value, and set the number of columns
    _check_sheet_type(sheet_type)
    raw_val = row[2]
    ncols = NEXP_COLS if sheet_type == 'exp' else NINFO_COLS

    # If there is a value AND a series, read both
    if value_and_series:
        npoints = len(row) - ncols  # num of time-resolved datapoints
        series = np.zeros(npoints)
        series[:] = row[ncols:] 
        val = [raw_val, series]
    # If raw_val is blank, assume the row contains a time series
    elif util.chk_entry(raw_val) is None:
        npoints = len(row) - ncols  # num of time-resolved datapoints
        val = np.zeros(npoints)
        val[:] = row[ncols:]
    # Otherwise, it's a single value
    else:
        val = raw_val

    return val


# ------------------ Function for compiling experimental data ------------------
def get_exp_data(exp_set):
    """ Reads the experimental data from an exp set. This will be stored in the
        exp_set['overall']['exp_ydata'] field

    :return exp_ydata: y data for the experiment
    :rtype: Numpy array; could be two dims (time-resolved) or one
    :return exp_xdata: x data for the experiment
    :rtype: 1-D Numpy array of shape (ntimes,) or (nconds,)
    """
    def get_unique_times(exp_set):
        """ Gets all unique times in a dataset. Useful for experimental data 
            with randomly spaced time values 
        """
        all_times = []
        exp_objs = exp_set['exp_objs']
        for exp_obj in exp_objs:
            all_times.extend(exp_obj['result']['time'][0])
        unique_times = sorted(list(set(all_times)))

        return unique_times

    def interp_oned_array(given_ydata, given_xdata, desired_xdata):
        """ Interpolates a one-dimensional array of y data to fit on desired
            x data grid
        """
        interp_ydata = np.ndarray((len(desired_xdata),), dtype=float)
        # Loop over every unique x point
        for unique_idx, unique_xdatum in enumerate(desired_xdata):
            # If the unique x point is in the exp x data, store matching y data
            if unique_xdatum in given_xdata:
                exp_idx = np.where(given_xdata == unique_xdatum)
                interp_ydata[unique_idx] = given_ydata[exp_idx]
            else:  # otherwise, just store as NaN
                interp_ydata[unique_idx] = np.nan

        return interp_ydata

    # Load some initial parameters
    meas_type = exp_set['overall']['meas_type']
    plot_var = exp_set['plot']['variable'][0]  # the variable for the exp_set
    exp_objs = exp_set['exp_objs']
    nconds = len(exp_objs)

    # Get exp_xdata and exp_ydata based on measurement type
    if meas_type == 'outlet':
        # Get the xdata
        exp_xdata = np.ndarray((len(exp_objs),))
        for cond_idx, exp_obj in enumerate(exp_objs):
            exp_xdata[cond_idx] = exp_obj['conds'][plot_var][0]
        # Get the ydata
        spcs = exp_set['spc'].keys()
        ntargs = len(spcs)
        exp_ydata = np.ndarray((nconds, ntargs))
        for cond_idx, exp_obj in enumerate(exp_objs):
            result = exp_obj['result']
            for spc_idx, spc in enumerate(spcs):
                if spc in result:
                    # If the entry is a Numpy array, it was empty in the Excel
                    # sheet; set to NaN in this case
                    if isinstance(result[spc][0], np.ndarray):
                        exp_ydata[cond_idx, spc_idx] = np.nan
                    else:
                        exp_ydata[cond_idx, spc_idx] = result[spc][0]
                else:
                    exp_ydata[cond_idx, spc_idx] = np.nan

    elif meas_type == 'idt':
        # Get the xdata
        exp_xdata = np.ndarray((len(exp_objs),))
        for cond_idx, exp_obj in enumerate(exp_objs):
            exp_xdata[cond_idx] = exp_obj['conds'][plot_var][0]
        # Get the ydata
        ntargs = exp_checker.get_nidts(exp_set)
        exp_ydata = np.ndarray((nconds, ntargs))
        for cond_idx, exp_obj in enumerate(exp_objs):
            result = exp_obj['result']['idt']
            for idt_idx in range(ntargs):
                if idt_idx + 1 in result:  # +1 b/c idt #s in Excel are 1-index
                    exp_ydata[cond_idx, idt_idx] = result[idt_idx + 1][0]
                else:
                    exp_ydata[cond_idx, idt_idx] = np.nan

    elif meas_type == 'half_life':
        # Get the xdata
        exp_xdata = np.ndarray((len(exp_objs),))
        for cond_idx, exp_obj in enumerate(exp_objs):
            exp_xdata[cond_idx] = exp_obj['conds'][plot_var][0]
        # Get the ydata
        ntargs = 1  # I guess I'm limiting myself to one half-life for now...
        exp_ydata = np.ndarray((nconds, ntargs))
        for cond_idx, exp_obj in enumerate(exp_objs):
            exp_ydata[cond_idx] = exp_obj['result']['half_life'][0]

    elif meas_type == 'conc':
        # Get the xdata
        exp_xdata = get_unique_times(exp_set)
        ntimes = len(exp_xdata)
        # Get the ydata
        spcs = exp_set['spc'].keys()
        ntargs = len(spcs)
        exp_ydata = np.ndarray((nconds, ntargs, ntimes))
        for cond_idx, exp_obj in enumerate(exp_objs):
            result = exp_obj['result']
            exp_times = result['time'][0]
            for spc_idx, spc in enumerate(spcs):
                if spc in result:
                    sing_spc = result[spc][0]
                    exp_ydata[cond_idx, spc_idx] = interp_oned_array(
                        sing_spc, exp_times, exp_xdata)
                else:
                    exp_ydata[cond_idx, spc_idx] = np.nan

    elif meas_type == 'abs':
        # Get the xdata
        exp_xdata = get_unique_times(exp_set)
        ntimes = len(exp_xdata)
        # Get the ydata
        nwvlens = len(exp_set['plot']['wavelength'])
        nspcs = len(exp_set['plot']['active_spc'])
        ntargs = nwvlens * (nspcs + 1)  # +1: total abs for each wvlen
        exp_ydata = np.ndarray((nconds, ntargs, ntimes))
        exp_ydata[:] = np.nan  # set all to NaN by default
        for cond_idx in range(nconds):
            for wvlen_idx in range(nwvlens):
                total_idx = (wvlen_idx + 1) * (nspcs + 1) - 1
                total = exp_objs[cond_idx]['result']['abs'][wvlen_idx + 1][0]
                exp_ydata[cond_idx, total_idx] = total  # only total is not NaN

    elif meas_type == 'lfs':
        # Get the xdata
        exp_xdata = np.ndarray((len(exp_objs),))
        for cond_idx, exp_obj in enumerate(exp_objs):
            if plot_var == 'phi':
                exp_xdata[cond_idx] = exp_obj['mix'][plot_var][0][0]
            else:
                exp_xdata[cond_idx] = exp_obj['conds'][plot_var]
        # Get the ydata
        ntargs = 1
        exp_ydata = np.ndarray((nconds, ntargs))
        for cond_idx, exp_obj in enumerate(exp_objs):
            result = exp_obj['result']
            exp_ydata[cond_idx] = result['lfs'][0]
    else:
        raise NotImplementedError(f"meas_type '{meas_type}' is not working")

    exp_xdata = np.array(exp_xdata)  # convert list to numpy array

    return exp_ydata, exp_xdata


# --------------------------- Misc. helper functions ---------------------------
def convert_units(raw_val, quant, units):
    """ Converts a value of some physical quantity in specified units to
        desired internal units

        Note: the desired internal units are found as the first entry in each
            value of ALLOWED_UNITS

        Note: some quantities have alternate names. For example, "end_time" is
            simply a time. These alternate names are defined by the variable
            ALTERNATE_NAMES.

        :param raw_val: the value of some physical dimension (e.g., 1.04)
        :type raw_val: float or Numpy array of shape (nvals,)
        :param quant: the physical quantity that is quantified by val
            (e.g., 'pressure')
        :type quant: str
        :param units: the units used to quantify val (e.g., 'bar')
        :type units: str
        :return conv_val: val that has been converted to desired internal units
        :rtype: float
    """
    def convert_value(val, quant, units, conv_factor):

        # Check for special cases
        if quant == 'temp' and units == 'C':  # Celsius
            single_conv_val = val + 273.15
        elif quant == 'temp' and units == 'F':  # Fahrenheit
            single_conv_val = (val - 32) / 1.8 + 273.15
        elif quant == 'conc' and units == 'molec/cm3':  # number density
            single_conv_val = val

        # Otherwise, use the conversion factor
        else:
            single_conv_val = val * conv_factor

        return single_conv_val

    # If the units are blank or '-', don't convert
    chkd_entry = util.chk_entry(units)
    if chkd_entry is None:
        # Check if the quantity should have units assigned
        if raw_val != 'bal' and quant != 'phi':  # 'bal' = 'conc' but needs no units
            assert quant not in ALLOWED_UNITS.keys() and quant not in \
                ALTERNATE_NAMES.keys(), f"The quantity '{quant}' requires units"
        conv_val = raw_val  # no conversion if units are blank or '-'

    # Otherwise, convert the units
    else:
        # Check if an alternate name exists for quantity
        if quant in ALTERNATE_NAMES.keys():
            quant = ALTERNATE_NAMES[quant]  # e.g., changes "end_time" to "time"
        # Check that the quantity and the units are allowed
        allowed_quants = tuple(ALLOWED_UNITS.keys())
        assert quant in allowed_quants, (
            f'Quantity "{quant}" is not allowed. Options are: {allowed_quants}')
        allowed_units = ALLOWED_UNITS.get(quant)[0]
        assert units in allowed_units, (
            f'Units "{units}" are not allowed for the quantity "{quant}".'
            f' Options are: {allowed_units}')

        # Get the conversion factor
        conv_factors = ALLOWED_UNITS.get(quant)[1]
        units_idx = allowed_units.index(units)
        conv_factor = conv_factors[units_idx]

        # Deal with the unusual case when raw value is a list containing a single value paired with an array
        if isinstance(raw_val, list) and isinstance(raw_val[0], int) and \
            isinstance(raw_val[1], np.ndarray):
            conv_val = []
            # Call the convert_value subfunction
            conv_val.append(convert_value(raw_val[0], quant, units, conv_factor))
            conv_val.append(convert_value(raw_val[1], quant, units, conv_factor))
        # Normal case when it's just a single entry
        else:
            conv_val = convert_value(raw_val, quant, units, conv_factor)

    return conv_val


def _check_sheet_type(sheet_type):
    """ Checks that sheet type is correct
    """

    assert sheet_type in ('info', 'exp'), (
        f"sheet_type should be 'info' or 'exp', not {sheet_type}")


def _check_bounds(low_bnd, upp_bnd, bnd_type):
    """ Checks if any bound inputs were NaN (i.e., blank in the Excel file) or
        '-'; if so, return None. If not, leave unchanged
    """

    low_bnd = util.chk_entry(low_bnd)
    upp_bnd = util.chk_entry(upp_bnd)
    bnd_type = util.chk_entry(bnd_type)

    return low_bnd, upp_bnd, bnd_type


def _split_param(row):
    """ If there are any commas in the param field, splits the first param off
        from the extra params indicated by the columns

        For example, an abs_coeff param entry (in 'conds') could look like this:
            'abs_coeff,1,N2O' meaning the N2O abs coeff for the first wavelength

        For example, an abs param entry (in 'result') could look like this:
            'abs,1' meaning the absorption for the first wavelength

        :return param: the traditional param (e.g., abs, temp, abs_coeff)
        :rtype: str
        :return extra_params: additional params (e.g., 1, 2, N2O)
        :rtype: list
    """

    param = row[1]
    extra_params = []
    if isinstance(param, str):
        split_param = param.split(',')
        if len(split_param) > 1:  # if there were any commas
            param = split_param[0]
            extra_params.extend(split_param[1:])

    return param, extra_params

