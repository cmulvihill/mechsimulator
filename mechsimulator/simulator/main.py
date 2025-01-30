import copy
import numpy as np

from mechsimulator.simulator import util
from mechsimulator.simulator import outcome
from mechsimulator.simulator import sens
from mechsimulator.simulator import pathways

from mechsimulator.parser.exp_checker import get_poss_inps


# will add later; model after plotter.main
# EDIT: actually, will probably delete due to the addition of the runner pkg
def mult_sets_filenames():
    pass


def mult_sets(exp_sets, gases, mech_spc_dcts, calc_types, x_srcs,
              cond_srcs, mech_opts_lst=None):
    """ Runs multiple experimental sets against multiple mechanisms

        :param exp_sets:
        :param gases:
        :param mech_spc_dcts:
        :param calc_types:
        :param x_srcs: the source of the x data (e.g., temperature, time) used
            in the simulations; either 'plot' or 'exps'
        :param cond_srcs: the source of the conditions (e.g., temperature)
            used in the simulations; either 'plot' or 'exps'
        :param mech_opts_lst: list containing sim_options for
        :type mech_opts_lst: list
        :return:
    """

    # Loop over each experimental set
    set_ydata_lst = []  # using lists since array dimensions/sizes may vary
    set_xdata_lst = []
    for idx, exp_set in enumerate(exp_sets):
        set_ydata, set_xdata = single_set(
            exp_set, gases, mech_spc_dcts, calc_types[idx], x_srcs[idx],
            cond_srcs[idx], mech_opts_lst=mech_opts_lst)
        set_ydata_lst.append(set_ydata)
        set_xdata_lst.append(set_xdata)

    return set_ydata_lst, set_xdata_lst


def single_set(exp_set, gases, mech_spc_dcts, calc_type, x_src,
               cond_src, mech_opts_lst=None):
    """ Calculates the predictions of any number of mechanisms at the conditions
        of a single exp_set

        :param exp_set: object describing a set of experiments
        :type exp_set: dct
        :param gases: Cantera objects describing kinetics mechanisms/gases
        :type gases: list
        :param mech_spc_dcts: species identifying info for each mechanisms
        :type mech_spc_dcts: list
        :return mech_results: simulator results for one exp_set using many mechs
        :rtype: Numpy array whose shape depends on the type of measurement:
            (i) time-resolved: (nmechs, nconds, ntargs, ntimes)
            (ii) non-time-resolved: (nmechs, nconds, ntargs)
    """

    # Check inputs
    util.check_srcs(x_src, cond_src)

    # Initialize variables
    mech_ydata_shape, _, _, mech_xdata = util.get_mech_info(
        exp_set, calc_type, x_src, cond_src, gases)
    set_xdata = mech_xdata  # xdata is the same for all mechs in the set
    nmechs = len(gases)
    set_ydata_shape = (nmechs,) + mech_ydata_shape  # prepend mechs_dim
    dtype = 'object' if calc_type == 'pathways' else 'float'
    set_ydata = np.ndarray(set_ydata_shape, dtype=dtype)

    # Loop over each mech and run a simulation with each
    for mech_idx, gas in enumerate(gases):
        # Get the mech_opts for each mech
        if mech_opts_lst is None:
            mech_opts = None
        else:
            mech_opts = mech_opts_lst[mech_idx]
        # Get the updated_exp_set for the current mech
        updated_exp_set = update_exp_set(exp_set, mech_opts=mech_opts)
        # Run the simulation and store the results
        mech_spc_dct = mech_spc_dcts[mech_idx]
        mech_ydata = single_mech(updated_exp_set, gas, mech_spc_dct, calc_type,
                                 cond_src, mech_xdata, mech_ydata_shape,
                                 mech_opts=mech_opts)
        set_ydata[mech_idx] = mech_ydata

    return set_ydata, set_xdata


def single_mech(exp_set, gas, mech_spc_dct, calc_type, cond_src, xdata,
                ydata_shape, mech_opts=None):

    # Must get conds_dct for each mech since spc names can change btw. mechs
    conds_dct = get_conds_dct(exp_set, mech_spc_dct, cond_src, gas,
                              mech_opts=mech_opts)

    # Run the desired calculation type
    reac_type = exp_set['overall']['reac_type']
    meas_type = exp_set['overall']['meas_type']
    if calc_type == 'outcome':
        mech_ydata = outcome.single_mech(
            conds_dct, gas, reac_type, meas_type, xdata, ydata_shape)
    elif calc_type == 'sens':
        mech_ydata = sens.single_mech(
            conds_dct, gas, reac_type, meas_type, xdata, ydata_shape)
    elif calc_type == 'rop':
        raise NotImplementedError('rop not ready!')
    else:  # 'pathways'
        mech_ydata = pathways.single_mech(
            conds_dct, gas, reac_type, ydata_shape)

    return mech_ydata


def get_conds_dct(exp_set, mech_spc_dct, cond_src, gas, mech_opts=None):
    """ Gets the conditions dict

        :param exp_set:
        :param mech_spc_dct:
        :param cond_src:
        :return:
    """

    # Run a check on the species
    check_spcs(exp_set, mech_spc_dct, gas)

    # Load initial data
    reac_type = exp_set['overall']['reac_type']
    meas_type = exp_set['overall']['meas_type']
    plot_dct = exp_set['plot']

    if cond_src == 'plot':
        var = exp_set['plot']['variable'][0]
        conds = util.get_plot_conds(exp_set)
        nconds = len(conds)
    else:  # 'exps'
        exp_objs = exp_set['exp_objs']
        nconds = len(exp_objs)  # each experiment is its own condition

    # Loop over possible inputs and build the conditions dict
    conds_dct = {}
    poss_inps = get_poss_inps(reac_type, meas_type, cond_src, rm_bad=True)
    for inp in poss_inps:
        conds_dct[inp] = [None] * nconds  # initialize as Nones
        if cond_src == 'plot':
            if inp == var:  # if on plotting variable, use array
                conds_dct[inp] = conds
            elif plot_dct.get(inp) is not None:  # if a single value exists
                conds_dct[inp] = [plot_dct[inp][0]] * nconds
            # Otherwise, just leave as Nones
        else:  # 'exps'
            for cond_idx, exp_obj in enumerate(exp_objs):
                if exp_obj['conds'].get(inp) is not None:
                    if inp == 'abs_coeff':  # special case; it's a dict
                        # Does this need a [0] at the end with my new format?
                        conds_dct[inp][cond_idx] = exp_obj['conds'][inp]
                    else:
                        conds_dct[inp][cond_idx] = exp_obj['conds'][inp][0]
                # Otherwise, just leave as None

    # Add the mix information since it is stored separately
    exp_spc_dct = exp_set['spc']
    rename_instr = util.get_rename_instr(mech_spc_dct, exp_spc_dct)
    if cond_src == 'plot':
        raw_mix = exp_set['mix']
        if 'fuel' in raw_mix:  # if mix is defined using phi
            mix = rename_fuel_oxid_spcs(raw_mix, rename_instr)
            if exp_set['plot']['variable'][0] == 'phi':
                mix_lst = []
                for cond in conds:
                    mix.update({'phi': cond})
                    mix_lst.append(copy.deepcopy(mix))
            else:  # if the plot_var is something other than phi
                mix_lst = [mix] * nconds
            conds_dct['mix'] = mix_lst
        else:  # if mix is defined using mole fracs
            tuple_mix = util.translate_spcs(raw_mix, rename_instr)
            mix = rm_uncertainty(tuple_mix)  # remove uncertainty bounds
            conds_dct['mix'] = [mix] * nconds
    else:  # 'exps'
        conds_dct['mix'] = [None] * nconds
        for cond_idx, exp_obj in enumerate(exp_objs):
            raw_mix = exp_obj['mix']
            tuple_mix = util.translate_spcs(raw_mix, rename_instr)
            mix = rm_uncertainty(tuple_mix)  # remove uncertainty bounds
            conds_dct['mix'][cond_idx] = mix
        # NEED TO ADD CONDITION HERE FOR 'FUEL' (IN TERMS OF PHI)

    # Add the targ_spcs info since it is stored separately
    raw_targ_spcs = tuple(exp_spc_dct.keys())
    targ_spcs = util.translate_spcs(raw_targ_spcs, rename_instr)
    conds_dct['targ_spcs'] = targ_spcs

    # Add the P(t) information since it is stored separately
    if reac_type == 'st':
        conds_dct['p_of_t'] = [None] * nconds
        if cond_src == 'plot':
            if 'dpdt' in plot_dct:
                end_time = plot_dct['end_time']
                dpdt = plot_dct['dpdt']
                p_of_t = create_p_of_t(end_time, dpdt)
                conds_dct['p_of_t'] = [p_of_t] * nconds
        else:  # 'exps'
            for cond_idx, exp_obj in enumerate(exp_objs):
                if 'pressure' in exp_obj['result']:
                    times = exp_obj['result'].get('time')[0]
                    pressures = exp_obj['result'].get('pressure')[0]
                    p_of_t = np.vstack((times, pressures))
                    conds_dct['p_of_t'][cond_idx] = p_of_t
                elif 'dpdt' in exp_obj['conds']:
                    end_time = exp_obj['conds']['end_time'][0]
                    dpdt = exp_obj['conds']['dpdt'][0]
                    p_of_t = create_p_of_t(end_time, dpdt)
                    conds_dct['p_of_t'][cond_idx] = p_of_t
                # Otherwise, leave as None

    # Add V(t) information
    if reac_type == 'rcm':
        # For now, being dumb and only taking from the 'info' sheet. Need to add
        # ability to take from experimental sheets
        times = plot_dct['time'][0]
        volume = plot_dct['v_of_t'][0]
        v_of_t = np.vstack((times, volume))
        conds_dct['v_of_t'] = [v_of_t] * nconds

    # Add ignition delay time information
    if meas_type == 'idt':
        conds_dct['idt_method'] = plot_dct['idt_method'][0]
        raw_idt_targs = plot_dct['idt_targ'][0]
        idt_targs = []
        for raw_idt_targ in raw_idt_targs:
            if raw_idt_targ == 'pressure':
                idt_targ = ['pressure']  # list for use below with extend
            else:  # if a species
                idt_targ = util.translate_spcs([raw_idt_targ], rename_instr)
            idt_targs.extend(idt_targ)  # extend b/c adding list to list
        conds_dct['idt_targ'] = idt_targs

    # Add the T(x) information
    if plot_dct.get('t_profile') is not None:
        conds_dct['x_profile'] = plot_dct['x_profile']
        conds_dct['t_profile'] = plot_dct['t_profile']
        conds_dct['t_profile_setpoints'] = plot_dct['t_profile_setpoints']
    elif conds_dct.get('x_profile') is not None:  # need to remove if was created (i.e., if on PFR) but not used
        conds_dct.pop('x_profile')
        conds_dct.pop('t_profile')
        conds_dct.pop('t_profile_setpoints')

    # Add the active species
    if meas_type in ('abs', 'emis'):  # should 'ion' be here also?
        conds_dct['active_spc'] = exp_set['plot']['active_spc']

    # Add the wavelengths
    if meas_type in ('abs', 'emis'):
        conds_dct['wavelength'] = exp_set['plot']['wavelength']

    if meas_type == 'half_life':
        conds_dct['half_life_targ'] = exp_set['plot']['target_spc']

    return conds_dct


def create_p_of_t(end_time, dpdt):
    """ Creates a P(t) array from an end_time and a dP/dt

        :param end_time: final time of the simulation (seconds)
        :param dpdt: linear change in pressure during the simulation (%/ms)
        :return p_of_t: array of noramlized pressure starting at 1 and going
            to the end pressure calculated by the end_time and dpdt
        :rtype: Numpy array of shape (2,
    """

    times = np.array([0, end_time])
    end_pressure = 1 + ((end_time * 1e3) * dpdt) / 100
    pressures = np.array([1, end_pressure])
    p_of_t = np.vstack((times, pressures))

    return p_of_t


def update_exp_set(exp_set, mech_opts=None):
    """ Updates an exp_set with information from the simulation options

        :param exp_set:
        :param mech_opts:
        :return:
    """

    # If there are no mech_opts given or the only mech_opts are mechanism names,
    # then save a bit of time by not doing a deepcopy
    if mech_opts is None or tuple(mech_opts.keys()) == ('mech_names',):
        updated_exp_set = exp_set
    # Otherwise, make a copy of the exp_set and use mech_opts to update certain
    # portions of the exp_set
    else:
        # DOESN'T DO ANYTHING RIGHT NOW
        updated_exp_set = copy.deepcopy(exp_set)

    return updated_exp_set


def rm_uncertainty(inp_mix):
    """ Removes the uncertainty bounds from a mixture

        :param inp_mix: mixture with uncertainty bounds
        :type inp_mix: dct {param1: (val1, lb1, ub1, type1), param2: ...}
        :return new_mix: mixture with uncertainty bounds removed
        :rtype: dct {param1: val1, param2: ...}
    """

    new_mix = {}
    for spc, tup in inp_mix.items():
        new_mix[spc] = tup[0]

    return new_mix


def rename_fuel_oxid_spcs(inp_mix, rename_instr):
    """ Renames the species in a mixture defined using equivalence ratios
    """

    new_mix = {}
    # Rename the fuel and oxidizer species
    raw_fuel = inp_mix['fuel'][0]
    new_mix['fuel'] = util.translate_spcs(raw_fuel, rename_instr)
    raw_oxid = inp_mix['oxid'][0]
    new_mix['oxid'] = util.translate_spcs(raw_oxid, rename_instr)

    # Add the fuel and oxidizer ratios, if present
    if 'fuel_ratios' in inp_mix:
        new_mix['fuel_ratios'] = inp_mix['fuel_ratios']
    if 'oxid_ratios' in inp_mix:
        new_mix['oxid_ratios'] = inp_mix['oxid_ratios']

    return new_mix


def check_spcs(exp_set, mech_spc_dct, gas):
    """ Checks the species defined in the exp_set and the mech_spc_dct for any
        problems. This cannot be done at the parser level since it depends on
        not only the exp_set but also the mechanism

        There are two possible problems:
        (1) A species defined in the exp_set is not defined in the mech_spc_dct
        (2) A species defined in the exp_set and the mech_spc_dct is not defined
            in the Solution object (i.e., gas)

        Both problems are only checked for species that MUST be defined: namely,
        those that are in initial mixtures, IDT targets, or active species in
        emission/absorption experiments
    """
    def check_single_spc(spc, rename_instr, sheet_type):
        """ Checks a single species to see if it's properly defined
        """
        new_name = rename_instr[spc]
        assert new_name is not None, (
            f"'{spc}' is in '{sheet_type}' mix but not in the mech_spc_dct. "
            f"All spcs in initial mixture must be in the mech_spc_dct.")
        assert new_name in gas.species_names, (
            f"'{spc}' is in '{sheet_type}' mix but not in the Solution object. "
            f"All spcs in initial mixture must be in the Solution object.")

    # Load some initial data
    rename_instr = util.get_rename_instr(mech_spc_dct, exp_set['spc'])
    meas_type = exp_set['overall']['meas_type']

    # Check the info sheet to see if any of the mix species are undefined
    info_mix = exp_set['mix']
    if 'fuel' in info_mix:  # if defined in terms of ratios
        for spc in info_mix['fuel'][0]:
            check_single_spc(spc, rename_instr, 'info')
        for spc in info_mix['oxid'][0]:
            check_single_spc(spc, rename_instr, 'info')
    else:  # if defined in terms of spc mole fracs (e.g., 'H2': 0.1, 'O2': 0.9)
        for spc in info_mix:
            check_single_spc(spc, rename_instr, 'info')

    # Check each experiment to see if any of the mix species are undefined (mix
    # species should be the same as in the info sheet, but just being thorough)
    for exp_obj in exp_set['exp_objs']:
        exp_mix = exp_obj['mix']
        if 'fuel' in exp_mix:  # if defined in terms of ratios
            for spc in exp_mix['fuel'][0]:  # [0] omits uncertainty
                check_single_spc(spc, rename_instr, 'exp')
            for spc in exp_mix['oxid'][0]:
                check_single_spc(spc, rename_instr, 'exp')
        else:  # if defined in terms of spc mole fracs
            for spc in exp_mix:
                check_single_spc(spc, rename_instr, 'exp')

    # Check that IDT targets are defined
    if meas_type == 'idt':
        idt_targs = exp_set['plot']['idt_targ'][0]
        for idt_targ in idt_targs:
            if idt_targ != 'pressure':  # if on a species
                new_name = rename_instr[idt_targ]
                assert new_name is not None, (
                    f"IDT target '{idt_targ}' is not in the mech_spc_dct")
                assert new_name in gas.species_names, (
                    f"IDT target '{idt_targ}' should appear with the name '"
                    f"{new_name} in the Solution object, but does not.")

    # Check that active species are defined
    if meas_type in ('abs', 'emis'):
        active_spcs = exp_set['plot']['active_spc']
        for active_spc in active_spcs:
            new_name = rename_instr[active_spc]
            assert new_name is not None, (
                f"Active species '{active_spc}' is not in the mech_spc_dct")
            assert new_name in gas.species_names, (
                f"Active species '{active_spc}' should appear with the name '"
                f"{new_name} in the Solution object, but does not.")
