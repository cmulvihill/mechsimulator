import matplotlib.pyplot as plt
import numpy as np
from mechsimulator.simulator import util
from mechsimulator.simulator import reactors

ELEMENT = 'C'


def single_mech(conds_dct, gas, reac_type, meas_type, xdata, ydata_shape,
                prev_solns=None):

    if reac_type == 'jsr':
        mech_ydata, _ = jsr(conds_dct, gas, meas_type, ydata_shape,
                            prev_solns=prev_solns)
    elif reac_type == 'st':
        mech_ydata = st(conds_dct, gas, meas_type, xdata, ydata_shape)
    elif reac_type == 'pfr':
        mech_ydata = pfr(conds_dct, gas, meas_type, xdata, ydata_shape)
    elif reac_type == 'free_flame':
        mech_ydata, _ = free_flame(conds_dct, gas, meas_type, ydata_shape,
                                   prev_solns=prev_solns)
    elif reac_type == 'const_t_p':
        mech_ydata = const_t_p(conds_dct, gas, meas_type, xdata, ydata_shape)
    elif reac_type == 'rcm':
        mech_ydata = rcm(conds_dct, gas, meas_type, xdata, ydata_shape)
    else:
        raise NotImplementedError(f"reac_type '{reac_type}' not working")

    return mech_ydata


def rcm(conds_dct, gas, meas_type, xdata, ydata_shape):

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    end_times = conds_dct['end_time']
    targ_spcs = conds_dct['targ_spcs']
    v_of_ts = conds_dct['v_of_t']

    # Loop over all conditions
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    for cond_idx in range(ydata_shape[0]):  # [0] gives # of conditions
        raw_concs, raw_pressures, raw_times, _, _ = reactors.rcm(
            temps[cond_idx], pressures[cond_idx], mixes[cond_idx], gas,
            targ_spcs, end_times[cond_idx], v_of_ts[cond_idx])
        # Process the raw results
        mech_ydata[cond_idx] = process_rcm(
            raw_concs, raw_pressures, raw_times, conds_dct, cond_idx,
            meas_type, xdata)

    return mech_ydata


def process_rcm(raw_concs, raw_pressures, raw_times, conds_dct,
                cond_idx, meas_type, uniform_times):

    if meas_type == 'idt':
        idt_targs = conds_dct['idt_targ']
        idt_methods = conds_dct['idt_method']  # same length as idt_targs
        targ_spcs = conds_dct['targ_spcs']
        # Loop over each target/method pair and get the IDT data
        cond_ydata = np.ndarray((len(idt_targs),))
        for targ_idx, idt_targ in enumerate(idt_targs):
            idt_method = idt_methods[targ_idx]
            if idt_targ == 'pressure':
                targ_profile = raw_pressures
            else:  # if a species
                spc_idx = targ_spcs.index(idt_targ)  # idx of spc in targets
                targ_profile = raw_concs[spc_idx]  # conc. of target spc
            idt, warnings = st_idt(targ_profile, raw_times, method=idt_method)
            if warnings:
                print(f'Warning: {warnings} was returned for ST IDT simulation')
            cond_ydata[targ_idx] = idt
    else:
        raise NotImplementedError(f"'{meas_type}' not working for RCM")

    return cond_ydata


def const_t_p(conds_dct, gas, meas_type, xdata, ydata_shape):

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    end_times = conds_dct['end_time']
    targ_spcs = conds_dct['targ_spcs']

    # Loop over all conditions
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    for cond_idx in range(ydata_shape[0]):  # [0] gives # of conditions
        raw_concs, raw_press, raw_temps, raw_times, _, end_gas = reactors.const_t_p(
            temps[cond_idx], pressures[cond_idx], mixes[cond_idx], gas,
            targ_spcs, end_times[cond_idx])
        # Process the raw results
        mech_ydata[cond_idx] = process_const_t_p(
            raw_concs, raw_press, raw_temps, raw_times, conds_dct, cond_idx,
            end_gas, meas_type, xdata)

    return mech_ydata


def process_const_t_p(raw_concs, raw_pressures, raw_temps, raw_times, conds_dct,
                      cond_idx, end_gas, meas_type, uniform_times):

    if meas_type == 'conc':
        # Simply interpolate the raw concentrations to fit the uniform times
        cond_ydata = util.interp(raw_concs, raw_times, uniform_times)
    elif meas_type == 'outlet':
        end_time = conds_dct['end_time'][cond_idx]
        # Interpolate to get the data at exactly the specified end_time
        end_data = util.interp(raw_concs, raw_times, np.array([end_time]))
        cond_ydata = end_data[:, -1]  # take the last time (only one, actually)
    elif meas_type == 'pathways':
        cond_ydata = end_gas.TPX
    else:
        raise NotImplementedError(
            f"meas_type '{meas_type}' not implemented for reac_type const_t_p")

    return cond_ydata


def free_flame(conds_dct, gas, meas_type, ydata_shape, prev_solns=None):

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    targ_spcs = conds_dct['targ_spcs']

    # Make sure prev_soln is the right size (if given)
    if prev_solns is not None:
        nconds = len(temps)  # picking temps arbitrarily
        assert nconds == len(prev_solns), (  # outer dim should equal nconds
            f"free_flame prev_solns should have {nconds} conditions, not "
            f"{len(prev_solns)} ")

    # Loop over the conditions, performing a simulation for each
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    new_soln_lst = []
    for cond_idx in range(ydata_shape[0]):
        # Set conditions
        temp = temps[cond_idx]
        pressure = pressures[cond_idx]
        mix = mixes[cond_idx]
        # Set previous solution, if it was given
        if prev_solns is not None:
            prev_soln = prev_solns[cond_idx]
        else:
            if cond_idx == 0:
                prev_soln = None
            else:  # use solution from previous condition in this loop
                prev_soln = new_soln_lst[cond_idx - 1]

        # Run the simulation
        raw_concs, pos, vels, raw_temps, rop, end_gas = reactors.free_flame(
            temp, pressure, mix, gas, targ_spcs, prev_soln=prev_soln)
        # Process the raw results
        new_soln = np.vstack((pos / max(pos), raw_temps))  # normalize position
        new_soln_lst.append(new_soln)
        mech_ydata[cond_idx] = process_free_flame(raw_concs, pos, vels, temp,
                                                  rop, end_gas, meas_type)

    return mech_ydata, new_soln_lst


def process_free_flame(raw_concs, pos, vels, temp, rop, end_gas, meas_type):

    if meas_type == 'lfs':
        mech_ydata = vels[0] * 100  # convert to cm/s
    else:
        raise NotImplementedError(f"meas_type {meas_type} not working")

    return mech_ydata


def jsr(conds_dct, gas, meas_type, ydata_shape, prev_solns=None,
        output_all=False):

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    res_times = conds_dct['res_time']
    vols = conds_dct['vol']
    mdots = conds_dct['mdot']  # either res_time or mdot will be used
    targ_spcs = conds_dct['targ_spcs']

    # Make sure that the prev_soln array is the right size (if given)
    if prev_solns is not None:
        prev_solns_shape = np.shape(prev_solns)
        assert prev_solns_shape[0] == ydata_shape[0]  # [0] is # of conditions
        assert prev_solns_shape[1] == gas.n_species

    # If output_all was indicated, initialize
    if output_all:  # all_concs has shape = (nconds, nspcs)
        all_concs = np.ndarray((ydata_shape[0], gas.n_species))
    else:
        all_concs = None

    # Loop over the conditions, performing a simulation for each
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    for cond_idx in range(ydata_shape[0]):
        temp = temps[cond_idx]
        pressure = pressures[cond_idx]
        mix = mixes[cond_idx]
        res_time = res_times[cond_idx]
        vol = vols[cond_idx]
        mdot = mdots[cond_idx]
        # Get the previous concentrations
        if prev_solns is not None:
            prev_concs = prev_solns[cond_idx]
        elif cond_idx == 0:    # if prev_soln not given and on first time,
            prev_concs = None  # set as None (will use mix as prev_concs)
        # Run the simulation
        raw_concs, prev_concs, _, end_gas = reactors.jsr(
            temp, pressure, mix, gas, targ_spcs, res_time, vol, mdot=mdot,
            prev_concs=prev_concs)
        # If all concentrations were requested, store them
        if output_all:
            all_concs[cond_idx, :] = prev_concs
        # Process the raw results
        mech_ydata[cond_idx] = process_jsr(raw_concs, end_gas, meas_type)

    return mech_ydata, all_concs
    

def st(conds_dct, gas, meas_type, xdata, ydata_shape):
    """ Gets the outcome of a shock tube simulation for a single mech
    """

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    end_times = conds_dct['end_time']
    targ_spcs = conds_dct['targ_spcs']
    p_of_ts = conds_dct['p_of_t']

    # Loop over all conditions
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    for cond_idx in range(ydata_shape[0]):  # [0] gives # of conditions
        raw_concs, raw_pressures, raw_temps, raw_times, _, _ = reactors.st(
            temps[cond_idx], pressures[cond_idx], mixes[cond_idx], gas,
            targ_spcs, end_times[cond_idx], p_of_t=p_of_ts[cond_idx])
        # Process the raw results
        mech_ydata[cond_idx] = process_st(
            raw_concs, raw_pressures, raw_temps, raw_times, conds_dct, cond_idx,
            meas_type, xdata)

    return mech_ydata


def process_st(raw_concs, raw_pressures, raw_temps, raw_times, conds_dct,
               cond_idx, meas_type, uniform_times):
    """ Processes the outcome for a single condition of a shock tube simulation

        :param raw_concs:
        :param raw_pressures:
        :param raw_temps:
        :param raw_times:
        :param conds_dct:
        :param cond_idx: index of the current condition; used for things that
            are cond. dependent (e.g., absorption coefficient)
        :type cond_idx:
        :return:
    """

    if meas_type == 'conc':
        # Simply interpolate the raw concentrations to fit the uniform times
        cond_ydata = util.interp(raw_concs, raw_times, uniform_times)

    elif meas_type == 'idt':
        # Load information from conds_dct
        idt_targs = conds_dct['idt_targ']
        idt_methods = conds_dct['idt_method']  # same length as idt_targs
        targ_spcs = conds_dct['targ_spcs']
        # Loop over each target/method pair and get the IDT data
        cond_ydata = np.ndarray((len(idt_targs),))
        for targ_idx, idt_targ in enumerate(idt_targs):
            idt_method = idt_methods[targ_idx]
            if idt_targ == 'pressure':
                targ_profile = raw_pressures
            else:  # if a species
                spc_idx = targ_spcs.index(idt_targ)  # idx of spc in targets
                targ_profile = raw_concs[spc_idx]  # conc. of target spc
            idt, warnings = st_idt(targ_profile, raw_times, method=idt_method)
            if warnings:
                print(f'Warning: {warnings} was returned for ST IDT simulation')
            cond_ydata[targ_idx] = idt
    elif meas_type == 'abs':
        # Load information from conds_dct
        active_spcs = conds_dct['active_spc']
        abs_coeffs = conds_dct['abs_coeff'][cond_idx]  # for all wavelengths
        path_length = conds_dct['path_length'][cond_idx]
        pressure = conds_dct['pressure'][cond_idx]
        targ_spcs = conds_dct['targ_spcs']
        nwvlens = len(conds_dct['wavelength'])
        nspcs = len(active_spcs)
        # Calculate absorption for each wavelength/species pair
        ntargs = nwvlens * (nspcs + 1)  # +1: total abs for each wvlen
        raw_trans = np.ndarray((ntargs, len(raw_times)))  # on raw time grid
        raw_trans[:] = np.nan
        for wvlen_idx in range(nwvlens):
            for spc_idx, active_spc in enumerate(active_spcs):
                abs_coeff = abs_coeffs[wvlen_idx + 1].get(active_spc)[0]
                targ_idx = wvlen_idx * (nspcs + 1) + spc_idx
                # If abs_coeff exists and spc defined in mech, calculate abs
                if abs_coeff is not None and active_spc in targ_spcs:
                    raw_conc = raw_concs[targ_spcs.index(active_spc)]
                    raw_trans[targ_idx] = calc_trans(  # For all times. Always.
                        raw_conc, abs_coeff, pressure, path_length)
            # Get total transmission for the current wavelength
            total_idx = (wvlen_idx + 1) * (nspcs + 1) - 1
            raw_trans[total_idx] = np.nanprod(raw_trans, 0)
            # Convert to percent absorption
            percent_abs = 100 * (1 - raw_trans)
            # Interpolate; changes last dim to be len(uniform_times)
            cond_ydata = util.interp(percent_abs, raw_times, uniform_times)
    elif meas_type == 'outlet':
        end_time = conds_dct['end_time'][cond_idx]
        # Interpolate to get the data at exactly the specified end_time
        end_data = util.interp(raw_concs, raw_times, np.array([end_time]))
        cond_ydata = end_data[:, -1]  # take the last time (only one, actually)
    else:
        raise NotImplementedError(f"'{meas_type}' not working for ST")

    return cond_ydata


def pfr(conds_dct, gas, meas_type, xdata, ydata_shape):
    # will need xdata for other meas_types, I think

    # Get arrays of reactor inputs
    temps = conds_dct['temp']
    pressures = conds_dct['pressure']
    mixes = conds_dct['mix']
    mdots = conds_dct['mdot']  # either res_time or mdot will be used
    areas = conds_dct['area']
    lengths = conds_dct['length']
    res_times = conds_dct['res_time']
    targ_spcs = conds_dct['targ_spcs']

    # Loop over all conditions
    dtype = 'object' if meas_type == 'pathways' else 'float'
    mech_ydata = np.ndarray(ydata_shape, dtype=dtype)
    for cond_idx in range(ydata_shape[0]):  # [0] gives # of conditions
        raw_concs, raw_times, raw_positions, rop, end_gas = reactors.pfr(
            temps[cond_idx], pressures[cond_idx], mixes[cond_idx], gas,
            targ_spcs, mdots[cond_idx], areas[cond_idx], lengths[cond_idx],
            res_time=res_times[cond_idx])
        # Process raw results
        mech_ydata[cond_idx] = process_pfr(raw_concs, raw_times, raw_positions,
                                           rop, end_gas, meas_type)

    return mech_ydata


def calc_trans(raw_conc, abs_coeff, pressure, path_length):
    """ Evaluates the Beer-Lambert law for an array of concentrations

        :param raw_conc: mole fraction time for a single species
        :type raw_conc: Numpy.ndarray
        :param abs_coeff: absorption coefficient for this species (m-1atm-1)
        :type abs_coeff: float
        :param pressure: total pressure (atm)
        :type pressure: float
        :param path_length: absorption path length (m)
        :type path_length: float
        :return:
    """

    absorbance = raw_conc * abs_coeff * path_length * pressure
    transmission = np.exp(-absorbance)

    return transmission


def process_pfr(raw_concs, raw_times, raw_positions, rop, end_gas, meas_type):

    if meas_type == 'outlet':
        cond_ydata = raw_concs[:, -1]  # -1 takes the last entry
    elif meas_type == 'pathways':
        cond_ydata = end_gas.TPX
    else:
        raise NotImplementedError(f"'{meas_type}' not working for PFR")

    return cond_ydata


def process_jsr(raw_concs, end_gas, meas_type):

    if meas_type == 'outlet':
        cond_ydata = raw_concs
    elif meas_type == 'pathways':
        cond_ydata = end_gas.TPX
    else:
        raise NotImplementedError(f"'{meas_type}' not working for JSR")

    return cond_ydata


# Functions for getting IDT
def _get_rcm_idt(pressures, times):
    """ Extracts ignition delay time from a rapid compression machine pressure
        time history

        :param pressures: the pressure time history used to determine IDT
        :type pressures: Numpy array of shape (ntimes,)
        :param times: the time values corresponding to target
        :type times: Numpy array of shape (ntimes,)
        :return idt: ignition delay time (s)
        :rtype: float
        :return warnings: possible warnings regarding the IDT determination
        :rtype: list of strs
    """

    # Get the extrema idxs, which are where the first_deriv changes signs
    first_deriv = np.gradient(pressures, times)
    second_deriv = np.gradient(first_deriv, times)
    extrema_idxs = np.nonzero((np.diff(np.sign(first_deriv)) != 0) * 1)[0]

    # Get the maxima; i.e., where second_deriv < 0
    maxima_idxs = []
    for extrema_idx in extrema_idxs:
        if second_deriv[extrema_idx] < 0:
            maxima_idxs.append(extrema_idx)

    # If there are two peaks, calculate IDT; otherwise, return a warning
    idt = None
    warning = None
    if len(maxima_idxs) == 2:
        time_zero = times[maxima_idxs[0]]
        ignition = times[maxima_idxs[1]]
        idt = ignition - time_zero
    else:
        warning = f'Instead of 2 peaks, {len(maxima_idxs)} peaks were found'

    return idt, warning


def st_idt(targ, times, method='baseline_extrap', plot=False):
    """ Gets the ignition delay time for a shock-tube simulation. Can determine
        IDT using one of three methods.

        :param targ: the target concentration used to determine IDT
        :type targ: Numpy array of shape (ntimes,)
        :param times: the time values corresponding to target
        :type times: Numpy array of shape (ntimes,)
        :param method: the method by which to determine the IDT; options are as
            follows:
            1: intersection of steepest slope with baseline
            2: point of steepest slope
            3: peak value of the target profile
        :type method: str
        :return idt: ignition delay time (s)
        :rtype: float
        :return warnings: possible warnings regarding the IDT determination
        :rtype: list of strs
    """

    warnings = []

    # Get first derivative (note: np.gradient uses central differences)
    first_deriv = np.gradient(targ, times)
    steepest_idx = np.argmax(first_deriv)
    steepest_slope = first_deriv[steepest_idx]
    steepest_time = times[steepest_idx]
    steepest_val = targ[steepest_idx]

    # If using the baseline extrapolation or steepest slope methods, check that
    # the max slope isn't the last point
    if steepest_idx + 1 == len(times) and method in ('baseline_extrap',
                                                     'max_slope'):
        warnings.append('Max slope at last point')

    if method == 'baseline_extrap':
        # Get the slope and intercept of the baseline
        initial_slope = 0  # for now, assuming these are 0; could be better
        initial_int = 0

        # Get the y-intercept of the steepest tangent line
        steepest_int = steepest_val - steepest_slope * steepest_time

        # Find the intersection of the two lines
        idt = (initial_int - steepest_int) / (steepest_slope - initial_slope)
        int_y = steepest_slope * idt + steepest_int  # for plotting
    elif method == 'max_slope':
        idt = steepest_time
    elif method == 'max_value':
        # Check that the max value doesn't occur at the last point
        if np.argmax(targ) + 1 == len(times):
            warnings.append('Peak value at last point')
        idt = times[np.argmax(targ)]
    else:
        raise NotImplementedError

    # Perform plotting if indicated
    if plot:
        plt.plot(times, targ)
        if method == 'baseline_extrap':
            xlim = plt.xlim()  # store current xlim and ylim
            ylim = plt.ylim()
            tangent = steepest_slope * times + steepest_int
            plt.plot(times, tangent, 'r--')
            plt.plot(idt, int_y, 'ro')
            plt.xlim(xlim)  # reset xlim and ylim to zoom in on the target data
            plt.ylim(ylim)
        if method == 'max_slope':
            steepest_value = targ[np.argmax(first_deriv)]
            plt.plot(idt, steepest_value, 'ro')
        if method == 'max_value':
            peak_value = max(targ)
            plt.plot(idt, peak_value, 'ro')
        plt.show()

    if warnings:
        idt = np.nan

    return idt, warnings
