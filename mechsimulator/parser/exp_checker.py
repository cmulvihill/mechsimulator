import copy
import numpy as np


# Allowed groups (keys) and their required params (values) in the 'info' sheet
ALLOWED_INFO_GROUPS = {
    'overall':      ('set_id', 'source', 'description', 'reac_type',
                     'meas_type', 'num_exps', 'version'),
    'plot':         ('variable', 'start', 'end', 'inc'),
    'plot_format':  (),
    'mix':          (),
    'spc':          (),
    'sim_opts':     (),
    'exp_objs':     (),
    'ignore_row':   (),
}

# Allowed groups (keys) and their required params (values) in the 'exp' sheets
ALLOWED_EXP_GROUPS = {
    'overall':      ('exp_id',),
    'conds':        (),
    'mix':          (),
    'result':       (),
    'ignore_row': (),
}

# Allowed reactor types (keys) and:
# (1) required inputs in the 'conds' field of the exp_sheets and the 'plot'
#       field of the 'info' sheet
# (2) optional inputs in the 'conds' field of the exp_sheets and the 'plot'
#       field of the 'info' sheet
# (3) the allowed measurement types
# In the required inputs, a tuple indicates that only one of those values is
# required (e.g., either 'res_time' or 'mdot' is required for a JSR).
ALLOWED_REAC_TYPES = {
    'st':           (('temp', 'pressure', 'end_time'),
                     ('dpdt',),
                     ('abs', 'emis', 'idt', 'outlet', 'ion', 'pressure',
                      'conc', 'half_life')),
    'pfr':          (('temp', 'pressure', 'length', ('res_time', 'mdot'),
                      'area',),
                     ('x_profile', 't_profile', 't_profile_setpoints'),
                     ('outlet',)),
    'jsr':          (('temp', 'pressure', ('res_time', 'mdot'), 'vol'),
                     (),
                     ('outlet',)),
    'rcm':          (('temp', 'pressure', 'end_time'),
                     ('time', 'v_of_t'),
                     ('idt', 'pressure')),
    'const_t_p':    (('temp', 'pressure', 'end_time'),
                     (),
                     ('abs', 'emis', 'idt', 'outlet', 'ion', 'pressure',
                      'conc')),
    'free_flame':   (('temp', 'pressure'),
                     ('phi',),  # so that 'phi' can be the plot_var
                     ('lfs',),)
}

# Allowed measurement types (keys) and:
# (1) required inputs in the 'plot' field of the 'info' sheet,
# (2) required inputs in the 'conds' field of the exp_sheet, and
# (3) optional inputs.

# NOTE: could go through and remove the 'variable start end inc'?
ALLOWED_MEAS_TYPES = {
    'abs':          (('variable', 'timestep', 'end_time', 'wavelength',
                      'active_spc'),
                     ('abs_coeff', 'path_length'),
                     ('start', 'end', 'inc',)),
    'emis':         (('variable', 'timestep', 'end_time', 'wavelength',
                      'active_spc'),
                     (),
                     ('start', 'end', 'inc',)),
    'idt':          (('variable', 'start', 'end', 'inc', 'idt_targ',
                      'idt_method', 'end_time'),
                     (),
                     ()),
    'outlet':       (('variable', 'start', 'end', 'inc'),
                     (),
                     ()),
    'ion':          (('variable', 'timestep', 'end_time',),
                     (),
                     ('start', 'end', 'inc',)),
    'pressure':     (('variable', 'timestep', 'end_time',),
                     (),
                     ('start', 'end', 'inc',)),
    'conc':         (('variable', 'timestep', 'end_time',),
                     (),
                     ('start', 'end', 'inc',)),
    'lfs':          (('variable', 'start', 'end', 'inc'),
                     (),
                     (),),
    'half_life':    (('variable', 'end_time', 'target_spc'),
                     (),
                     ('start', 'end', 'inc',)),
}

# Allowed 'idt_method' options for determining ignition delay time
ALLOWED_IDT_METHODS = ('baseline_extrap', 'max_slope', 'max_value')

# Allowed parameters for defining a mixture with phi:
# (1) required parameters
# (2) optional parameters
ALLOWED_PHI_PARAMS = (
    ('fuel', 'oxid', 'phi'),
    ('fuel_ratios', 'oxid_ratios')
)

# Allowed simulation options (keys) and:
# (1) their default values
# (2) permitted reactor types for that option (blank indicates all reactors)
ALLOWED_SIM_OPTS = {
    'niters':           (2e4,
                         ('jsr',)),
    'nsteps':           (2e3,
                         ('pfr',)),
    'width':            (0.05,
                         ('free_flame', 'burner')),
    'log_level':        (0,
                         ('free_flame', 'burner')),
    'ratio':            (10.0,
                         ('free_flame', 'burner')),
    'slope':            (0.8,
                         ('free_flame', 'burner')),
    'curve':            (0.8,
                         ('free_flame', 'burner')),
    'prune':            (0.05,
                         ('free_flame', 'burner')),
    'sens_factor':      (0.01,
                         ()),
    'auto':             (True,
                         ('free_flame', 'burner')),
    'transport_model':  ('multi',
                         ('free_flame', 'burner')),
    'prev_soln_targ':   ('temp',
                         ('free_flame', 'burner')),
    'eos':              ('ig',
                         ()),
}

# Allowed plot formatting options and their default values
ALLOWED_PLOT_FORMAT = {
    'plot_points':  None,  # True if meas_type in POINT_MEAS_TYPES; see below
    'xunit':        None,
    'xlim':         None,
    'yunit':        None,
    'ylim':         None,
    'omit_targs':   None,
    'exp_on_top':   True,
    'rows_cols':    (4, 3),
    'marker_size':  15,
    'group_by':     'targ',  # 'cond' if meas_type in POINT_MEAS_TYPES
    'exp_color':    'black',
    'xscale':       'linear',
    'yscale':       'linear',
}

# Measurement types that default to plotting as points
POINT_MEAS_TYPES = ('outlet', 'idt', 'lfs', 'half_life')


def chk_exp_set(exp_set):
    """ Runs checks on everything in an exp_set

        :param: exp_set: description of a set of experiments
        :type exp_set: dct
    """

    # Fix any number densities (i.e., convert to mole fractions)
    fix_num_dens(exp_set)

    # Check the 'info' sheet
    exp_set = chk_info_sheet(exp_set)
    # Check the exp_objs (must check exp_objs AFTER exp_set)
    for idx, exp_obj in enumerate(exp_set['exp_objs']):
        exp_set['exp_objs'][idx] = chk_exp_obj(exp_obj, exp_set)

    return exp_set


def chk_info_sheet(exp_set):
    """ Runs checks on an exp_set, mostly on parameters from the 'info' sheet
    """

    set_id = exp_set['overall']['set_id']  # for printing
    id_str = f"In set ID {set_id}, "
    reac_type = exp_set['overall']['reac_type']
    meas_type = exp_set['overall']['meas_type']

    # Check that the groups have the required input params
    for group, params in exp_set.items():
        for reqd_inp in ALLOWED_INFO_GROUPS[group]:
            assert reqd_inp in params, (
                f"{id_str} param '{reqd_inp}' is missing from group '{group}'")

    # Check that the reactor type is allowed
    assert reac_type in ALLOWED_REAC_TYPES.keys(), (
        f"{id_str}reac_type '{reac_type}' is no good. "
        f"Options are: {tuple(ALLOWED_REAC_TYPES.keys())}")

    # Check that the measurement type is allowed
    assert meas_type in ALLOWED_REAC_TYPES[reac_type][2], (
        f"{id_str}meas_type '{meas_type}' is no good for reac_type {reac_type}."
        f" Options are: {ALLOWED_REAC_TYPES[reac_type][2]}")

    # Check that the number of exp_objects matches the number indicated in the
    # info sheet
    nexps = exp_set['overall']['num_exps']
    nexp_objs = len(exp_set['exp_objs'])
    assert nexps == nexp_objs, (
        f"{id_str}the 'info' sheet indicates {nexps}"
        f" experiments, while there are {nexp_objs} exp_objs")

    # Check that the required inputs exist in the plot field, both according to
    # meas_type and reac_type
    plot_info = exp_set['plot']
    plot_var = plot_info['variable']
    reqd_meas_inps = ALLOWED_MEAS_TYPES[meas_type][0]
    reqd_reac_inps = ALLOWED_REAC_TYPES[reac_type][0]
    for reqd_meas_inp in reqd_meas_inps:
        assert reqd_meas_inp in plot_info.keys(), (
            f"{id_str}required 'plot' input '{reqd_meas_inp}' is missing. "
            f"This is required for meas_type '{meas_type}'")
    # Check for the proper inputs according to the reactor type
    for reqd_reac_inp in reqd_reac_inps:
        # If reqd_reac_inp is a string, i.e., a single value
        if isinstance(reqd_reac_inp, str):
            assert reqd_reac_inp in plot_info.keys() or reqd_reac_inp \
                in plot_var, (
                f"{id_str}required 'plot' input '{reqd_reac_inp}' is "
                f"missing. This is required for reac_type '{reac_type}'")
        # If reqd_reac_inp is a tuple with multiple optional variables
        else:
            satisfied = False
            # Make sure  one and only one of the optional inputs was given
            for opt_inp in reqd_reac_inp:
                if opt_inp in plot_info.keys():
                    assert not satisfied, (
                        f"{id_str}only one of the optional"
                        f" inputs, {reqd_reac_inp}, should be given")
                    satisfied = True
            assert satisfied, (
                f"{id_str}one of the optional inputs,"
                f" {reqd_reac_inp}, should be given")

    # Check that the increment is not zero (would cause a divide by 0 error
    # later when getting the plot_conds array)
    assert plot_info['inc'] != 0, (
        f"{id_str}the 'inc' cannot be 0")

    # Check that only allowed plot instructions are given
    poss_inps = get_poss_inps(reac_type, meas_type, 'plot', rm_bad=False)
    for inp in plot_info.keys():
        assert inp in poss_inps, (
                f"{id_str}the input '{inp}' is not permitted for"
                f" the reactor type '{reac_type}' and the measurement type"
                f" '{meas_type}'. Options are {poss_inps}")

    # Check that the number of wavelengths indicated in the 'plot' field matches
    # that given in the results of the exp_sheets
    if meas_type in ('abs', 'emis'):
        nexp_wvlens = get_nwvlens(exp_set)
        nset_wvlens = len(exp_set['plot']['wavelength'])
        assert nexp_wvlens == nset_wvlens, (
            f"{id_str}there are {nexp_wvlens} wavelengths indicated in the exp"
            f" sheets, but {nset_wvlens} indicated in the 'plot' field")

    # Check some things regarding ignition delay time measurements
    if meas_type == 'idt':
        idt_targs = exp_set['plot']['idt_targ'][0]
        idt_methods = exp_set['plot']['idt_method'][0]
        ntargs = len(idt_targs)
        nmethods = len(idt_methods)
        # Check that the number of targets and methods are the same
        assert ntargs == nmethods, (
            f"{id_str}the number of IDT targets, {idt_targs}, "
            f"and IDT methods, {idt_methods}, are different")
        # Check that the methods are allowed
        for idt_method in idt_methods:
            assert idt_method in ALLOWED_IDT_METHODS, (
                f"{id_str}the idt_method '{idt_method}' is not "
                f"allowed. Options are: {ALLOWED_IDT_METHODS}")
        # Check that the targets are allowed
        all_spcs = tuple(exp_set['spc'].keys())
        for idt_targ in idt_targs:
            if idt_targ != 'pressure':
                assert idt_targ in all_spcs, (
                    f"{id_str}the idt_targ '{idt_targ}' is not allowed. Options"
                    f" are 'pressure' or any one defined species: {all_spcs}")

    # Check that the end_time and timestep are compatible
    # This is a dumb check. It should just do this within the numerical accuracy
    #timestep = exp_set['plot'].get('timestep')
    #end_time = exp_set['plot'].get('end_time')
    #if timestep is not None and end_time is not None:
    #    assert np.isclose(end_time[0] % timestep[0], 0, atol=1e-8), (
    #        f'{id_str}the end_time, {end_time}, is not a multiple '
    #        f'of the timestep, {timestep}')

    # Check some things regarding active spcs (for absorption, emission, etc.)
    active_spc = exp_set['plot'].get('active_spc')
    if active_spc:
        for active_spc in active_spc:
            assert active_spc in exp_set['spc'], (
                f"{id_str}active species {active_spc} is not defined")

    # Check that the mixture is acceptably defined
    exp_set = chk_mix(exp_set, exp_set, id_str, sheet_type='info')

    # Check the sim opts and fill in missing values with defaults
    def_opts = ALLOWED_SIM_OPTS.keys()
    # Check that all given opts are allowed
    for opt in exp_set['sim_opts']:
        assert opt in def_opts, (
            f"{id_str}the sim_opt {opt} is not allowed. Options: {def_opts}.")
        if ALLOWED_SIM_OPTS[opt][1] != ():  # if 2nd entry blank, all reacs ok
            assert reac_type in ALLOWED_SIM_OPTS[opt][1], (
                f"{id_str}sim_opt {opt} not allowed for reactor {reac_type}")
    # Fill in any missing default opts
    for def_opt in def_opts:
        if def_opt not in exp_set['sim_opts']:
            exp_set['sim_opts'][def_opt] = ALLOWED_SIM_OPTS[def_opt]

    # Check the plot format options and fill in missing values with defaults
    plt_frmt = exp_set['plot_format']
    def_frmts = ALLOWED_PLOT_FORMAT.keys()
    # Check that all given opts are allowed
    for frmt, val in plt_frmt.items():
        assert frmt in def_frmts, (
            f"{id_str}plot_format '{frmt}' not allowed. Options: {def_frmts}.")
        if frmt == 'group_by':
            assert val in ('targ', 'cond'), (
                f"{id_str}'group_by' should be 'targ' or 'cond', not '{val}'")
            if meas_type in POINT_MEAS_TYPES:
                assert val == 'cond', (
                    f"{id_str}'group_by' should be 'cond' for meas_type "
                    f"'{meas_type}', not 'targ'")
        elif frmt == 'plot_points':
            assert isinstance(val, bool), (
                f"{id_str}'plot_points' should be 'yes' or 'no', not '{val}'")
        # Checks on the xunit and yunit are done in the plotting code
        if frmt in ('xunit', 'yunit'):
            assert val not in ('C', 'F'), (
                f"{id_str}the x/y unit cannot be {val}. Temp. must be in K")
    # Fill in any missing opts with defaults
    for def_frmt in def_frmts:
        if def_frmt not in plt_frmt:
            # If the missing opt is plot_points, get default based on meas_type
            if def_frmt == 'plot_points':
                if meas_type in POINT_MEAS_TYPES:
                    plt_frmt['plot_points'] = True
                else:
                    plt_frmt['plot_points'] = False
            # If the missing opt is plot_points, get default based on meas_type
            elif def_frmt == 'group_by':
                if meas_type in POINT_MEAS_TYPES:
                    plt_frmt['group_by'] = 'cond'
                else:
                    plt_frmt['group_by'] = ALLOWED_PLOT_FORMAT[def_frmt]
            # If the missing opt is yscale, get default based on meas_type
            elif def_frmt == 'yscale' and meas_type == 'idt':
                plt_frmt['yscale'] = 'log'
            else:
                plt_frmt[def_frmt] = ALLOWED_PLOT_FORMAT[def_frmt]

    return exp_set


def chk_exp_obj(exp_obj, exp_set):
    """ Runs checks on an exp_obj to make sure certain conditions are met

        :param exp_obj: description of a single experiment
        :type: dct
        :param: exp_set: description of a set of experiments
        :type exp_set: dct
    """

    # Check that the experiment ID is defined
    set_id = exp_set['overall']['set_id']
    assert exp_obj['overall'].get('exp_id') is not None, (
        f"For set ID {set_id}, one exp_sheet is missing the 'exp_id' field")
    exp_id = exp_obj['overall']['exp_id']
    id_str = f"In set ID {set_id}, exp ID {exp_id}, "

    # Check for all required inputs for the given reactor type
    reac_type = exp_set['overall']['reac_type']
    reqd_reac_inps = ALLOWED_REAC_TYPES[reac_type][0]
    for reqd_reac_inp in reqd_reac_inps:
        # If the required input is a single required value (e.g., 'temp')
        if isinstance(reqd_reac_inp, str):
            assert reqd_reac_inp in exp_obj['conds'].keys(), (
                f"{id_str}req'd input '{reqd_reac_inp}' missing from 'conds'")
        # If the required input is a tuple, only one of which is required (e.g.,
        # 'res_time' or 'mdot' for a JSR)
        else:  # in this case, reqd_reac_inp is a tuple with multiple variables
            satisfied = False
            # Make sure that one and only one of the optional inputs was given
            for opt_inp in reqd_reac_inp:
                if opt_inp in exp_obj['conds'].keys():
                    assert not satisfied, (
                        f"{id_str}only one of the optional inputs, "
                        f"{reqd_reac_inp}, should be given.")
                    satisfied = True
            assert satisfied, (
                f"{id_str}one of the optional inputs, {reqd_reac_inp}, needed")

    # Check for all required inputs for the given measurement type
    meas_type = exp_set['overall']['meas_type']
    reqd_meas_inps = ALLOWED_MEAS_TYPES[meas_type][1]
    for reqd_meas_inp in reqd_meas_inps:
        assert reqd_meas_inp in exp_obj['conds'].keys(), (
            f"{id_str}the red'd input {reqd_meas_inp} missing from 'conds'")

    # Check that only allowed conditions are given
    poss_inps = get_poss_inps(reac_type, meas_type, 'exps')
    for inp in exp_obj['conds'].keys():
        assert inp in poss_inps, (
            f"{id_str}input '{inp}' not allowed for reactor type '{reac_type}' "
            f"and measurement type '{meas_type}'. Options are {poss_inps}.")

    # Check that all arrays in the result section are the same length
    lengths = []
    for name, result in exp_obj['result'].items():
        if isinstance(result, tuple):  # if a tuple, result is a val_tuple
            val = result[0]  # the array is the first entry
            if isinstance(val, np.ndarray):
                val = val[~np.isnan(val)]  # remove NaNs
                lengths.append(len(val))
        elif isinstance(result, dict):  # if dct, result is a dct of val_tuples
            for val_tuple in result.values():
                val = val_tuple[0]  # the array is the first entry
                if isinstance(val, np.ndarray):
                    val = val[~np.isnan(val)]  # remove NaNs
                    lengths.append(len(val))
    # The lengths should all be the same (i.e., 1) or empty if no arrays (0)
    assert len(set(lengths)) in (0, 1), (
        f"{id_str}time-resolved arrays in 'result' are not all the same length")

    # Check some things regarding absorption measurements
    if meas_type == 'abs':
        assert exp_obj['result'].get('abs') is not None, (
            f"Set ID {set_id} is 'abs' but exp ID {exp_id} has no 'abs' data")
        # Check that the keys of the result section are formatted correctly
        for key in exp_obj['result']['abs'].keys():
            assert isinstance(key, int), (
                f"{id_str}'abs' result requires integers as keys (1, 2, ...)")
        # Check that the species defined in the absorption coefficients are also
        # defined in the active spcs
        active_spc = exp_set['plot']['active_spc']
        for abs_coeffs in exp_obj['conds']['abs_coeff'].values():
            for spc in abs_coeffs.keys():
                assert spc in active_spc, (
                    f"{id_str}'{spc}' is defined in the absorption coefficients"
                    f" but not in the active spcs, {active_spc}.")

    if meas_type == 'idt':
        # Check that the number of IDTs indicated in the 'plot' field matches
        # that given in the results of the exp_sheets
        nexp_idts = get_nidts(exp_set)
        nset_idts = len(exp_set['plot']['idt_targ'][0])
        assert nexp_idts == nset_idts, (
            f"{id_str}there are {nexp_idts} IDTs indicated in the exp sheets, "
            f"but {nset_idts} indicated in the 'plot' field")

    # Check that the mixture is acceptably defined
    exp_obj = chk_mix(exp_obj, exp_set, id_str, sheet_type='exp')

    return exp_obj


def fix_num_dens(exp_set):
    """ Converts any number densities to mole fractions. Will fail if more than
        one thermodynamic state is specified in the 'info' sheet
    """
    def _fix_mix(mix, tot_num_dens):
        """ Converts a singular mix to mole fractions
        """

        for spc, entry in mix.items():
            units = entry[4]
            if units == 'molec/cm3':
                assert tot_num_dens is not None, (
                    'multiple thermo states in the info sheet w/number density!'
                    ' use mole fractions or only one thermo state')
                fixed_val = entry[0] / tot_num_dens
                mix[spc] = (fixed_val,) + entry[1:]

    # First, fix the 'info' sheet (only the mix to look at)
    tot_num_dens = _tot_num_dens(exp_set, sheet_type='info')
    _fix_mix(exp_set['mix'], tot_num_dens)

    # Second, fix the exp_objs (need to look at mix and result)
    all_spcs = tuple(exp_set['spc'].keys())
    meas_type = exp_set['overall']['meas_type']
    for exp_obj in exp_set['exp_objs']:
        tot_num_dens = _tot_num_dens(exp_obj, sheet_type='exp')
        # Fix the mix first
        _fix_mix(exp_obj['mix'], tot_num_dens)
        # Next, fix any results
        if meas_type in ('conc', 'burner_conc'):
            for name, RowEntry in exp_obj['result'].items():
                if name in all_spcs and RowEntry[4] == 'molec/cm3':
                    new_val = RowEntry[0] / tot_num_dens
                    exp_obj['result'][name] = (new_val,) + RowEntry[1:]



def _tot_num_dens(exp_set_or_obj, sheet_type='exp'):
    """ Calculate the total number density of an exp_set ('info' sheet) or an
        exp_obj. For exp_set, only works if there is only one thermodynamic
        state specified
    """
    def _calc(temperature, pressure):
        """ Returns the total number density at a temperature and pressure

            :param temperature: temperature in Kelvin
            :param pressure: pressure in atm
            :return tot_num_dens: total number density in molecules/cm3
        """

        univ_gas_const = 82.05737  # cm3 atm K-1 mol-1
        avogadro = 6.022e23  # molecules mol-1
        result = avogadro * pressure / (temperature * univ_gas_const)

        return result

    if sheet_type == 'info':
        # If the user specified more than one thermodynamic state using the
        # plot_var field, return a tot_num_dens of None
        plot_dct = exp_set_or_obj['plot']
        plot_var = plot_dct['variable'][0]
        start = plot_dct['start'][0]
        end = plot_dct['end'][0]
        if plot_var in ('temp', 'pressure') and not np.isclose(start, end):
            tot_num_dens = None
        # Otherwise, calculate tot_num_dens
        else:
            temp = start if plot_var == 'temp' else plot_dct['temp'][0]
            pres = start if plot_var == 'pressure' else plot_dct['pressure'][0]
            tot_num_dens = _calc(temp, pres)
    else:  # exp
        temp = exp_set_or_obj['conds']['temp'][0]
        pres = exp_set_or_obj['conds']['pressure'][0]
        tot_num_dens = _calc(temp, pres)

    return tot_num_dens


def chk_mix(exp_set_or_obj, exp_set, id_str, sheet_type='exp'):
    """ Checks that a mixture is acceptably defined

        :param exp_set_or_obj: the object to be checked; if checking the 'info'
            sheet parameters, this object will be identical to the exp_set input
        :param exp_set: used to get species information
        :param id_str: printout prefix for error messages
        :param sheet_type: either 'info' or 'exp'
        :return exp_set_or_obj: the mixture could have been modified, so return
    """

    # Get some basic mixture information
    mix = exp_set_or_obj['mix']
    all_spcs = tuple(exp_set['spc'].keys())
    if sheet_type == 'info':
        plot_var = exp_set['plot']['variable']
    else:
        plot_var = None
    correct_spc, correct_phi = _mix_type(mix, all_spcs, plot_var)

    # If it's formatted with spc mole fracs, check a few things
    if correct_spc:
        total_mole_frac = 0
        bal_present = False
        for spc, x_tuple in mix.items():
            mole_frac = x_tuple[0]  # [0] omits uncertainty
            if mole_frac == 'bal':
                bal_present = True
                bal_spc = spc
                bal_uncertainty = list(x_tuple)[1:]  # remove first entry
            else:
                total_mole_frac += mole_frac
        assert total_mole_frac <= 1.0001, (
            f"{id_str} total mole frac. can't exceed 1")
        if bal_present:
            new_mix = copy.deepcopy(mix)
            new_mix[bal_spc] = ((1 - total_mole_frac),) + tuple(bal_uncertainty)
            exp_set_or_obj['mix'] = new_mix
            total_mole_frac = 1
        assert np.isclose(total_mole_frac, 1, atol=1e-4), (
            f"{id_str} total mole fraction is {total_mole_frac}. Should be 1")

    # If it's formatted with equivalence ratios, check some things
    if correct_phi:
        for fuel_spc in mix['fuel'][0]:  # check that all fuel spcs are def'd
            assert fuel_spc in all_spcs, (
                f"{id_str}the spc {fuel_spc} is not defined")
        for oxid_spc in mix['oxid'][0]:  # check that all oxid spcs are def'd
            assert oxid_spc in all_spcs, (
                f"{id_str}the spc {oxid_spc} is not defined")
        # Check that the ratios are properly defined (if at all)
        if 'fuel_ratios' in mix:
            assert len(mix['fuel_ratios'][0]) == len(mix['fuel'][0]), (
                f"{id_str}number of entries in fuel and fuel_ratios must match")
        if 'oxid_ratios' in mix:
            assert len(mix['oxid_ratios'][0]) == len(mix['oxid'][0]), (
                f"{id_str}number of entries in oxid and oxid_ratios must match")
        if len(mix['fuel'][0]) > 1:  # ensure fuel_ratios are given if needed
            assert 'fuel_ratios' in mix, (
                f"{id_str}for more than one fuel, fuel_ratios is required")
        if len(mix['oxid'][0]) > 1:  # ensure oxid_ratios are given if needed
            assert 'oxid_ratios' in mix, (
                f"{id_str}for more than one oxidizer, oxid_ratios is required")

    return exp_set_or_obj


# ------------------------- Miscellaneous functions ----------------------------
def get_poss_inps(reac_type, meas_type, plot_or_exps, rm_bad=True):
    """ Gets all possible (i.e., allowed) inputs for either the 'plot' field of
        the 'info' sheet or the 'conds' field of the exp sheets

        :param reac_type: the reactor type
        :type reac_type: str
        :param meas_type: the measurement type
        :type meas_type: str
        :param plot_or_exps: either 'plot' or 'exps'
        :type plot_or_exps: str
        :param rm_bad: whether or not to remove the plot-specific inputs
        :type rm_bad: Bool
        :return poss_inps: all possible inputs
        :rtype: tuple (str1, str2, ...)
    """

    # Get the required inputs and flatten them
    if plot_or_exps == 'plot':
        reqd_meas_inps = ALLOWED_MEAS_TYPES[meas_type][0]
    else:  # 'exps'
        reqd_meas_inps = ALLOWED_MEAS_TYPES[meas_type][1]
    reqd_reac_inps = ALLOWED_REAC_TYPES[reac_type][0]
    flat_reqd_meas_inps = flatten_tup(reqd_meas_inps)
    flat_reqd_reac_inps = flatten_tup(reqd_reac_inps)

    # Get the optional inputs
    opt_meas_inps = ALLOWED_MEAS_TYPES[meas_type][2]
    opt_reac_inps = ALLOWED_REAC_TYPES[reac_type][1]

    # Add together
    poss_inps = flat_reqd_meas_inps + flat_reqd_reac_inps + opt_meas_inps +\
        opt_reac_inps

    # Remove the plotting variable stuff if indicated
    if rm_bad:
        bad_items = ('variable', 'start', 'end', 'inc')
        poss_inps = list(poss_inps)
        for bad_item in bad_items:
            if bad_item in poss_inps:
                poss_inps.remove(bad_item)
        poss_inps = tuple(poss_inps)

    return poss_inps


def flatten_tup(inp_tup):
    """ If any elements in a tuple are themselves tuples, flattens out the tuple
        into a single, flat tuple

        Example: if inp_tup = (1, (2, 3), 4), the output flat
        tuple will be flat_tup = (1, 2, 3, 4)
    """

    flat_tup = []
    for entry in inp_tup:
        if isinstance(entry, str):
            flat_tup.append(entry)
        else:  # if a tuple
            for sub_entry in entry:
                flat_tup.append(sub_entry)
    flat_tup = tuple(flat_tup)

    return flat_tup


def get_nwvlens(exp_set):
    """ Gets the number of wavelengths specified throughout the experimental set
    """

    meas_type = exp_set['overall']['meas_type']
    nwvlens = 0
    for exp_obj in exp_set['exp_objs']:
        current_num = len(exp_obj['result'][meas_type])
        if current_num > nwvlens:
            nwvlens = current_num

    return nwvlens


def get_nidts(exp_set):
    """ Gets the number of IDT values specified throughout the experimental set
    """

    nidts = 0
    for exp_obj in exp_set['exp_objs']:
        current_num = len(exp_obj['result']['idt'])
        if current_num > nidts:
            nidts = current_num

    return nidts


def _mix_type(mix, all_spcs, plot_var):
    """ Determines whether a mixture is defined in terms of mole fractions or
        in terms of equivalence ratio
    """

    # See if the mixture passes the simple species check
    correct_spc = True
    for spc in mix:  # assume that the keys are species
        if spc not in all_spcs:
            correct_spc = False
            break
    # If the simple spc check failed, see if the mix passes a simple phi check
    correct_phi = False
    if correct_spc is False:
        for idx, reqd_inp in enumerate(ALLOWED_PHI_PARAMS[0]):
            if reqd_inp not in mix:
                if plot_var is not None and reqd_inp == plot_var[0]:
                    pass  # if reqd_inp is satisfied via plot_var, don't break
                else:
                    break
            if idx == len(ALLOWED_PHI_PARAMS[0]) - 1:
                correct_phi = True  # True if made it through the loop

    assert correct_spc or correct_phi, (
        "The mixture is incorrectly formatted for both spcs and phi. If "
        "defining in terms of spcs, use the format {spc1: X1, spc2: X2, ...}."
        "If defining in terms of phi, use the format {'phi': phi, "
        "'fuel': fuel, 'oxid': oxid} (fuel_ratios and oxid_ratios may also be "
        "given).")

    return correct_spc, correct_phi
