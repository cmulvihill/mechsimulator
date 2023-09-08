import numpy as np
import matplotlib.pyplot as plt
from mechsimulator.parser.exp import ALLOWED_UNITS

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


def get_rename_instr(mech_spc_dct1, mech_spc_dct2):
    """ Gets the rename_instr, which relates the species names in the Excel
        file with those in the mechanism. Does this by comparing the two
        mech_spc_dcts

        :param mech_spc_dct1: the reference mech_spc_dct
        :param mech_spc_dct2: the mech_spc_dct to be renamed
        :return rename_instr: spc_names in mech_spc_dct2 to be renamed
        :rtype: dct {spc_to_be_renamed: new_spc_name, ...}
    """

    rename_instr = {}
    # Loop over each species in the mech_spc_dct to be renamed
    for spc2, spc_dct2 in mech_spc_dct2.items():
        ich2 = spc_dct2['inchi']
        mlt2 = spc_dct2['mult']
        chg2 = spc_dct2['charge']
        exc2 = spc_dct2['exc_flag']
        # Loop over each species in the reference mech_spc_dct
        for spc1, spc_dct1 in mech_spc_dct1.items():
            ich1 = spc_dct1['inchi']
            mlt1 = spc_dct1['mult']
            chg1 = spc_dct1['charge']
            exc1 = spc_dct1['exc_flag']
            if ich2 == ich1 and mlt2 == mlt1 and chg2 == chg1 and exc1 == exc2:
                rename_instr[spc2] = spc1
                break  # no need to continue
        # If spc2 was not found in mech_spc_dct1, save value as None
        if spc2 not in rename_instr.keys():
            rename_instr[spc2] = None

    return rename_instr


def translate_spcs(names, rename_instr):
    """ Renames the species inside of an object according to the instructions
        inside rename_instr. The names input can either be a list or a dct

        :param names: an input with spc names that are to be redefined
        :type names: dct {spc1: val1, spc2: ...}, list [spc1, spc2, ...], or
            tuple (spc1, spc2, ...)
        :param rename_instr: spc_names in the experiment to be renamed according
            to the mechanism spc names
        :type rename_instr: dct {spc_to_be_renamed: new_spc_name, ...}
        :return translated_names: the input names but with all spcs renamed
        :rtype: dct, list, or tuple (depending on the input)
    """

    assert isinstance(names, (dict, list, tuple)), (
        f'Input "names" must be a dict, list, or tuple but is a {type(names)}')

    # Rename a dictionary with the format {spc1: value1, spc2: ...}; this will
    # usually be a dictionary describing the initial mixture
    if isinstance(names, dict):
        translated_names = {}
        for spc, value in names.items():
            renamed_spc = rename_instr[spc]
            translated_names[renamed_spc] = value

    # Rename a list or tuple of spcs: [spc1, spc2, ...] or (spc1, spc2, ...);
    # this will often be a list of target_spcs
    else:
        translated_names = []
        for spc in names:
            renamed_spc = rename_instr[spc]
            translated_names.append(renamed_spc)
        if isinstance(names, tuple):  # change to tuple if needed
            translated_names = tuple(translated_names)

    return translated_names


def get_plot_conds(exp_set):
    """ Gets a Numpy array describing the variation of the plotting variable
    """

    plot_dct = exp_set['plot']
    start = plot_dct['start'][0]
    end = plot_dct['end'][0]
    inc = plot_dct['inc'][0]
    num = int((end - start) / inc) + 1
    plot_conds = np.linspace(start, end, num)

    return plot_conds


def get_uniform_times(exp_set):
    """ Gets a uniform times array for an exp_set based on the plot instructions
    """

    max_time = exp_set['plot']['end_time'][0]
    min_time = 0
    timestep = exp_set['plot']['timestep'][0]
    ntimes = int((max_time - min_time) / timestep) + 1
    times = np.linspace(min_time, max_time, ntimes)

    return times


def interp(ydata, xdata, desired_xdata):
    """ Takes a y data array with some inconsistent and/or unknown step size in
        the x variable and interpolates the y data to make the x data have a
        uniform step size. The input y data may be a Numpy array of dimension 1
        or 2 (the second dimension must be the x dimension). xdata will usually
        be time or position

        :param ydata: Numpy array containing y data to be interpolated; can be
            one array (ndim=1) or multiple arrays (ndim=2) to be interpolated
        :type ydata: Numpy.ndarray
        :param xdata: Numpy array containing the x data corresponding to the y
            data; must have ndim=1 and be monotonically increasing
        :type xdata: Numpy.ndarray
        :param desired_xdata: desired grid of x values to which the y data will
            be interpolated; must have ndim=1 and be monotonically increasing
        :type desired_xdata: Numpy.ndarray
        :return interp_ydata: the interpolated y data
        :rtype: Numpy.ndarray
    """

    ndims = np.ndim(ydata)
    assert ndims in (1, 2), (
        f'ydata arrays should have number of dimensions 1 or 2, not {ndims}')
    assert np.all(xdata[1:] > xdata[:-1]), (
        'xdata should be monotonically increasing ')

    # Interpolate the data; method depends on the dimensionality
    if ndims == 1:
        interp_ydata = np.interp(desired_xdata, xdata, ydata)
    else:  # ndims = 2
        narrs = np.shape(ydata)[0]  # assumes x is the second dim
        nxdata = len(desired_xdata)
        interp_ydata = np.ndarray((narrs, nxdata))
        for arr_idx, arr in enumerate(ydata):
            interp_ydata[arr_idx, :] = np.interp(desired_xdata, xdata, arr)

    # Set interpolated y data that extend past the given y data to NaN
    # Get idxs beyond which the data doesn't extend
    high_cutoff = np.argmin(abs(desired_xdata - xdata[-1]))  # first match
    low_cutoff = np.argmin(abs(desired_xdata - xdata[0]))  # first match
    # Correct case when max desired_xdata is less than max xdata
    if max(desired_xdata) < max(xdata):
        high_cutoff = len(desired_xdata)
    # Set values
    if ndims == 1:
        interp_ydata[high_cutoff:] = np.nan
        interp_ydata[:low_cutoff] = np.nan
    else:  # ndims = 2
        interp_ydata[:, high_cutoff:] = np.nan
        interp_ydata[:, :low_cutoff] = np.nan

    return interp_ydata


def get_mech_info(exp_set, calc_type, x_src, cond_src, gases):
    """ Gets the shape of the Numpy array that will describe a single mechanism
        simulation of an exp_set. Works for three different calculation types:
        (1) outcome, (2) sensitivity, or (3) rate of production

    """

    def get_times(exp_set, x_src):

        if x_src == 'plot':
            times = get_uniform_times(exp_set)
        else:
            times = exp_set['overall']['exp_xdata']

        return times

    def get_cond_titles(conds, units):

        cond_titles = []
        for cond in conds:
            cond_title = f'{cond} {units}'
            cond_titles.append(cond_title)

        return cond_titles

    def get_idt_targ_titles(exp_set):

        fake_targs = exp_set['plot']['idt_targ'][0]
        methods = exp_set['plot']['idt_method'][0]
        targs = []
        titles = []
        for idx, fake_targ in enumerate(fake_targs):
            targs.append((fake_targ, methods[idx]))
            titles.append((fake_targ + ', ' + methods[idx]))

        return targs, titles

    # Get the set variable and check that options were used correctly
    plot_var = exp_set['plot']['variable'][0]
    units = ALLOWED_UNITS[plot_var][0][0]
    if x_src == 'exps' and cond_src == 'plot':
        raise NotImplementedError(
            "x_src='exps' and cond_src='plot' is not allowed")
    assert x_src in ('plot', 'exps') and cond_src in ('plot', 'exps'), (
        "x_src and cond_src should be 'plot' or 'exps'")
    # Get the conditions depending on the source
    if cond_src == 'plot':
        conds = get_plot_conds(exp_set)
    else:  # 'exps'
        conds = []
        for exp_obj in exp_set['exp_objs']:
            conds.append(exp_obj['conds'][plot_var][0])  # [0] omits uncertainty
    cond_titles = get_cond_titles(conds, units)

    # Get the targets (and possibly another variable)
    # Note: targets doesn't depend on the x_src
    meas_type = exp_set['overall']['meas_type']
    if meas_type in ('abs', 'emis'):
        nwvlens = len(exp_set['plot']['wavelength'])
        nspcs = len(exp_set['plot']['active_spc'])
        ntargs = nwvlens * (nspcs + 1)  # +1 for total abs for each wvlen
        times = get_times(exp_set, x_src)
        shape = (len(conds), ntargs, len(times))
        x_arrays = (conds, None, times)  # WRONG! Should decide if needed
        x_titles = (cond_titles, None, None)
        xdata = times
    elif meas_type == 'conc':
        targs = list(exp_set['spc'].keys())
        times = get_times(exp_set, x_src)
        shape = (len(conds), len(targs), len(times))
        x_arrays = (conds, targs, times)
        x_titles = (cond_titles, targs, None)
        xdata = times
    elif meas_type == 'pressure':
        targs = ['Pressure']
        times = get_times(exp_set, x_src)
        shape = (len(conds), len(targs), len(times))
        x_arrays = (conds, targs, times)
        x_titles = (cond_titles, targs, None)
        xdata = times
    elif meas_type == 'idt':
        targs, targ_titles = get_idt_targ_titles(exp_set)
        shape = (len(conds), len(targs))
        x_arrays = (conds, targs)
        x_titles = (cond_titles, targ_titles)
        xdata = conds
    elif meas_type == 'outlet':
        targs = list(exp_set['spc'].keys())
        shape = (len(conds), len(targs))
        x_arrays = (conds, targs)
        x_titles = (cond_titles, targs)
        xdata = conds
    elif meas_type == 'lfs':
        targs = ['lfs']
        shape = (len(conds), len(targs))
        x_arrays = (conds, targs)
        x_titles = (cond_titles, targs)
        xdata = conds
    else:  # meas_type == 'ion':
        raise NotImplementedError("'ion' is not implemented yet")

    # If the calculation type is sensitivity or rate of production, add some 
    # information about the reactions
    if calc_type in ('sens', 'rop'):
        # Get the maximum number of reactions among all the mechanisms
        max_nrxns = 0
        for gas in gases:
            if gas.n_reactions > max_nrxns:
                max_nrxns = gas.n_reactions
        shape = (max_nrxns,) + shape  # prepend
        # Need to update to add reaction names to x_arrays and titles

    # If the calculation type is reaction pathways, overwrite the shape to just
    # be the number of conditions
    if calc_type == 'pathways':
        shape = (len(conds),)  # tuple

    return shape, x_arrays, x_titles, xdata


def check_srcs(x_src, cond_src):
    """ Checks the inputs for the x_src and cond_src

    :param x_src:
    :param cond_src:
    :return:
    """

    assert x_src in ('plot', 'exps'), (
        f"'x_src' should be 'plot' or 'exps', not '{x_src}'")
    assert cond_src in ('plot', 'exps'), (
        f"'cond_src' should be 'plot' or 'exps', not '{cond_src}'")
    if x_src == 'exps':
        assert cond_src != 'plot', (
            f"The 'x_src' and 'cond_src' combination 'exps' and 'plot',"
            " respectively, is not allowed.")


def plot_derivs(targ, times):
    """ Toy code for visualizing derivatives
    """

    cutoff_idx = len(targ)
    targ = targ[:cutoff_idx]
    times = times[:cutoff_idx]

    first_deriv = np.gradient(targ, times)
    second_deriv = np.gradient(first_deriv, times)
    extrema_idxs = np.nonzero((np.diff(np.sign(first_deriv)) != 0) * 1)[0]
    inflection_idxs = np.nonzero((np.diff(np.sign(second_deriv)) != 0) * 1)[0]
    print('targ:\n', targ)
    print('diff of targ:\n', np.diff(targ))
    print('first_deriv:\n', first_deriv)
    print('second_deriv:\n', second_deriv)
    print('extrema_idxs:\n', extrema_idxs)
    print('length:\n', len(extrema_idxs))
    print('inflection_idxs:\n', inflection_idxs)
    print('length:\n', len(inflection_idxs))

    fig, axs = plt.subplots(3, 1)
    axs[0].plot(times, targ)
    axs[1].plot(times, first_deriv)
    axs[2].plot(times, second_deriv)

    for idx in extrema_idxs:
        axs[0].plot(times[idx], targ[idx], 'ro')
    # for idx in inflection_idxs:
    #     axs[0].plot(times[idx], targ[idx], 'bo')

    plt.show()
