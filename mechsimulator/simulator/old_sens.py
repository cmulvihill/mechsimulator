import numpy as np
from mechsimulator.simulator import reactors


def st(temps, pressure, mix, gas, target_spcs, end_time, p_of_t=None,
       factor=0.1):
    """

        :param temps: temperatures at which to perform calculations (K)
        :type temps: Numpy array of shape (num_temps,)
        :param pressure: pressure at which to perform calculations (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...}
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param target_spcs: desired species concentrations
        :type target_spcs: list [spc1, spc2, ...]
        :param end_time: end time for the simulation (s); simulation will end
            at the first of either this time or the max time in p_of_t
        :type end_time: float
        :param p_of_t: specified pressure (any units) vs time (s) profile;
            can be None if no non-ideal effects are being simulated
        :type p_of_t: Numpy array of shape (2, num_timesteps)
        :param factor: factor by which to perturb A factors
        :type factor: float
        :return sens_coeffs: sens coeffs for each rxn, temp, spcs, and timestep
        :rtype: Numpy array of shape (num_rxns, num_temps, num_target_spcs,
            num_timesteps)
    """
    # Get the reference results (used as baseline for sens calcs)
    ref_results = np.ndarray((len(temps), len(target_spcs)))
    for temp_idx, temp in enumerate(temps):
        ref_result, _, _ = reactors.pfr(temp, pressure, mix, gas, target_spcs,
                                        mdot, area, length)
        # ref_results has shape (num_spcs, num_times); the last entry (i.e., the
        # reactor outlet) is the value to be stored in ref_results
        ref_results[temp_idx, :] = ref_result[:, -1]

    return sens_coeffs, ref_results



def jsr(temps, pressure, mix, gas, target_spcs, res_time, vol, mdot=None, factor=0.1):
    """ Calculates sensitivity coefficients for any number of target species
        across a range of temperatures for a JSR simulation

        :param temps: temperatures at which to perform calculations (K)
        :type temps: Numpy array of shape (num_temps,)
        :param pressure: pressure at which to perform calculations (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...} (example:
            {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param target_spcs: desired species concentrations
        :type target_spcs: list [spc1, spc2, ...]
        :param res_time: reactor residence time (s)
        :type res_time: float
        :param vol: reactor volume (m^3)
        :type vol: float
        :param factor: factor by which to perturb A factors
        :type factor: float
        :return sens_coeffs: sens coeffs for each rxn, temp, and target species
        :rtype: Numpy array of shape (num_rxns, num_temps, num_target_spcs)
    """

    # Get the reference results (used as baseline for sens calcs) and the
    # prev_concs_array, which helps converge to a solution
    ref_results = np.ndarray((len(temps), len(target_spcs)))
    prev_concs_array = np.ndarray((len(temps), gas.n_species))
    for temp_idx, temp in enumerate(temps):
        if temp_idx == 0:  # if on first temp, can't use prev_concs
            ref_result, prev_concs = reactors.jsr(
                temp, pressure, mix, gas, target_spcs, res_time, vol, mdot=mdot)
        else:  # otherwise, use prev_concs
            ref_result, prev_concs = reactors.jsr(
                temp, pressure, mix, gas, target_spcs, res_time, vol, mdot=mdot,
                prev_concs=prev_concs_array[(temp_idx - 1), :])  # -1 uses latest value
        ref_results[temp_idx, :] = ref_result
        prev_concs_array[temp_idx, :] = prev_concs

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.ndarray((num_rxns, len(temps), len(target_spcs)))
    for rxn_idx in range(num_rxns):
        current_rxn = gas.reactions()[rxn_idx].equation
        print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
        gas.set_multiplier(1.0)  # reset all multipliers to the original values
        gas.set_multiplier(1 + factor, rxn_idx)
        for temp_idx, temp in enumerate(temps):
            result, _ = reactors.jsr(temp, pressure, mix, gas, target_spcs,
                                     res_time, vol, mdot=mdot,
                                     prev_concs=prev_concs_array[temp_idx, :])
            ref = ref_results[temp_idx, :]
            sens_coeff = (result - ref) / (ref * factor)
            sens_coeffs[rxn_idx, temp_idx, :] = sens_coeff

    return sens_coeffs, ref_results


def pfr(temps, pressure, mix, gas, target_spcs, mdot, area, length, factor=0.1):
    """ Calculates sensitivity coefficients for any number of target species
        across a range of temperatures for a PFR simulation

        :param temps: temperatures at which to perform calculations (K)
        :type temps: Numpy array of shape (num_temps,)
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...}
            (example: {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param target_spcs: desired species concentrations
        :type target_spcs: list [spc1, spc2, ...]
        :param mdot: reactor mass flow rate (kg/s)
        :type mdot: float
        :param area: reactor cross-sectional area (m^2)
        :type area: float
        :param length: reactor length (m)
        :type length: float
        :param factor: factor by which to perturb A factors
        :type factor: float
        :return sens_coeffs: sens coeffs for each rxn, temp, and species
        :rtype: Numpy array of shape (num_rxns, num_temps, num_spcs)
    """

    # Get the reference results (used as baseline for sens calcs)
    ref_results = np.ndarray((len(temps), len(target_spcs)))
    for temp_idx, temp in enumerate(temps):
        ref_result, _, _ = reactors.pfr(temp, pressure, mix, gas, target_spcs,
                                        mdot, area, length)
        # ref_results has shape (num_spcs, num_times); the last entry (i.e., the
        # reactor outlet) is the value to be stored in ref_results
        ref_results[temp_idx, :] = ref_result[:, -1]

    # Get the sensitivity coefficients
    num_rxns = gas.n_reactions
    sens_coeffs = np.ndarray((num_rxns, len(temps), len(target_spcs)))
    for rxn_idx in range(num_rxns):
        current_rxn = gas.reactions()[rxn_idx].equation
        print(f'Current rxn: {current_rxn}, {rxn_idx + 1} out of {num_rxns}')
        gas.set_multiplier(1.0)  # reset the multipliers to the original values
        gas.set_multiplier(1 + factor, rxn_idx)
        for temp_idx, temp in enumerate(temps):
            results, _, _ = reactors.pfr(temp, pressure, mix, gas, target_spcs,
                                         mdot, area, length)
            result = results[:, -1]  # get the last (outlet) concentration
            ref = ref_results[temp_idx, :]
            sens_coeff = (result - ref) / (ref * factor)
            sens_coeffs[rxn_idx, temp_idx, :] = sens_coeff

    return sens_coeffs, ref_results


def get_sorted_idxs(sens_coeffs):

    num_rxns, _, num_spcs = np.shape(sens_coeffs)
    sorted_idxs = np.ndarray((num_rxns, num_spcs))
    for spc_idx in range(num_spcs):
        max_vals = np.zeros(num_rxns)
        for rxn_idx in range(num_rxns):
            max_vals[rxn_idx] = np.amax(abs(sens_coeffs[rxn_idx, :, spc_idx]))

        sorted_idx = np.argsort(max_vals)[::-1]  # -1: sort from large to small
        sorted_idxs[:, spc_idx] = sorted_idx

    return sorted_idxs


def get_sorted_sens_coeffs(sens_coeffs, sorted_idxs):
    """

        :param sens_coeffs:
        :type sens_coeffs: Numpy array of shape (num_rxns, num_temps, num_spcs)
        :param sorted_idxs:
        :type sorted_idxs: Numpy array of shape (num_rxns, num_spcs)
        :return sorted_sens_coeffs:
        :rtype: Numpy array of shape (num_rxns, num_temps, num_spcs)
    """
    num_rxns, num_temps, num_spcs = np.shape(sens_coeffs)
    sorted_sens_coeffs = np.ndarray((num_rxns, num_temps, num_spcs))

    for spc_idx in range(num_spcs):
        spc_sens_coeffs = sens_coeffs[:, :, spc_idx]
        spc_sorted_idxs = sorted_idxs[:, spc_idx]
        spc_sorted_vals = spc_sens_coeffs[spc_sorted_idxs.astype(int)]
        sorted_sens_coeffs[:, :, spc_idx] = spc_sorted_vals

    return sorted_sens_coeffs


def get_sorted_rxn_names(sorted_idxs, rxn_names):
    """

    :param sorted_idxs:
    :param rxn_names:
    :return:
    """
    num_rxns, num_spcs = np.shape(sorted_idxs)
    sorted_rxn_names = np.ndarray((num_rxns, num_spcs), dtype=object)

    for rxn_idx in range(num_rxns):
        for spc_idx in range(num_spcs):
            sorted_idx = int(sorted_idxs[rxn_idx, spc_idx])
            rxn_name = rxn_names[sorted_idx]
            sorted_rxn_names[rxn_idx, spc_idx] = rxn_name

    return sorted_rxn_names


def get_rxn_names(gas):
    """ Gets a Numpy array of reaction names from a Cantera Solution object

        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :return rxn_names: numpy array of all reaction names in gas
        :rtype: Numpy array (dtype=object) of shape (num_rxns,)
    """
    num_rxns = gas.n_reactions
    rxn_names = np.ndarray((num_rxns), dtype=object)
    for rxn_idx, rxn in enumerate(gas.reactions()):
        rxn_names[rxn_idx] = rxn.equation

    return rxn_names


def get_filtered_results(sens_coeffs, temps, ref_results, start_temp, end_temp):
    """

        :param sens_coeffs: sens coeffs for each rxn, temp, and species
        :type sens_coeffs: Numpy array of shape (num_rxns, num_temps, num_spcs)
        :param temps:
        :param ref_results:
        :param start_temp:
        :param end_temp:
        :return:
    """
    assert min(temps) <= start_temp and max(temps) >= end_temp, (
        'Start and end temps must be within the range of the temps values')
    # Get start and end idxs; depends on whether the temps increase or decrease
    if (temps[1] - temps[0]) > 0:  # if temps go from small to large
        start_idx = np.argmin(abs(temps - start_temp))
        end_idx = np.argmin(abs(temps - end_temp))
    else:  # if temps go from large to small
        start_idx = np.argmin(abs(temps - end_temp))
        end_idx = np.argmin(abs(temps - start_temp))

    filt_sens_coeffs = sens_coeffs[:, start_idx:end_idx+1, :]
    filt_temps = temps[start_idx:end_idx+1]
    filt_ref_results = ref_results[start_idx:end_idx+1]

    return filt_sens_coeffs, filt_temps, filt_ref_results
