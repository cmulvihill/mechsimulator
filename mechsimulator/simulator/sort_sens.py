import numpy as np


def sort_single_set(set_sens, gases):
    """ Sorts sensitivities for a single set (i.e., any number of mechanisms).
        Note that the mechanisms are sorted separately from one another (since
        the names/numbers of reactions may differ between mechanisms).
    
        :param set_sens: sensitivity coefficients for a single set
        :type set_sens: Numpy.ndarray of shape (nmechs, nrxns, nconds, ntargs,
            ntimes) if time-resolved or (nmechs, nrxns, nconds, ntargs)
        :param gases: Cantera objects describing kinetics mechanisms/gases
        :type gases: list
        :return sorted_set_sens: sorted sensitivity coefficients for a set
        :rtype: same as set_sens
        :return sorted_set_rxns: sorted rxn names for a set
        :rtype: Numpy.ndarray (dtype=object) of shape (nmechs, nrxns, nconds,
            ntargs) if time-resolved or (nmechs, nrxns, ntargs)
    """

    # Load initial data
    sorted_set_sens = np.ndarray(np.shape(set_sens))
    ndims = np.ndim(set_sens)
    # Initialize the array containing the rxn names
    if ndims == 5:  # time-resolved
        nmechs, nrxns, nconds, ntargs, _ = np.shape(set_sens)
        sorted_set_rxns = np.ndarray(
            (nmechs, nrxns, nconds, ntargs), dtype=object)  # object for strs
    else:  # ndims = 4; not time-resolved
        nmechs, nrxns, _, ntargs = np.shape(set_sens)
        sorted_set_rxns = np.ndarray((nmechs, nrxns, ntargs), dtype=object)
    # Sort each mechanism within the set
    for mech_idx, gas in enumerate(gases):
        mech_sens = set_sens[mech_idx]
        sorted_mech_sens, sorted_mech_rxns = sort_single_mech(mech_sens, gas)
        sorted_set_sens[mech_idx] = sorted_mech_sens
        sorted_set_rxns[mech_idx] = sorted_mech_rxns

    return sorted_set_sens, sorted_set_rxns


def sort_single_mech(mech_sens, gas):
    """ Sorts sensitivity coefficients and rxn names for a single mechanism
    
        :param mech_sens: sensitivity coefficients for a single mechanism
        :type mech_sens: Numpy.ndarray of shape (nrxns, nconds, ntargs, ntimes)
            (time-resolved) or (nrxns, nconds, ntargs) (non-time-resvolved)
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :return sorted_mech_sens: sorted sensitivity coefficients
        :rtype: same as mech_sens
        :return sorted_mech_rxns: sorted reaction names
        :rtype: Numpy.ndarray (dtype=object) of shape (nrxns, nconds, ntargs)
            if time-resolved or (nmechs, nrxns, ntargs)
    """

    def _sorted_sens(mech_sens):
        """ Sorts sensitivities for a single mech
        """
        # Get the sorted indices and info on the dimensionality
        sorted_idxs = _sorted_idxs(mech_sens)
        ndims, nrxns, nconds, ntargs, ntimes = dim_info(mech_sens)
        # Apply sorting differently depending on the dimensionality
        if ndims == 4:  # time-resolved
            sorted_sens = np.ndarray((nrxns, nconds, ntargs, ntimes))
            for cond_idx in range(nconds):
                for targ_idx in range(ntargs):
                    targ_sens = mech_sens[:, cond_idx, targ_idx]
                    targ_sorted_idxs = sorted_idxs[:, cond_idx, targ_idx]
                    targ_sorted_vals = targ_sens[targ_sorted_idxs.astype(int)]
                    sorted_sens[:, cond_idx, targ_idx] = targ_sorted_vals
        else:  # ndims = 3; not time-resolved
            sorted_sens = np.ndarray((nrxns, nconds, ntargs))
            for targ_idx in range(ntargs):
                targ_sens = mech_sens[:, :, targ_idx]
                targ_sorted_idxs = sorted_idxs[:, targ_idx]
                targ_sorted_vals = targ_sens[targ_sorted_idxs.astype(int)]
                sorted_sens[:, :, targ_idx] = targ_sorted_vals

        return sorted_sens

    def _sorted_rxns(mech_sens, gas):
        """ Sorts the reaction names for a single mechanism's sensitivities

            sorted_rxns has one less dimension than sens: for time-resolved,
            the time (or position) dimension is removed, while for non-time-
            resolved, the conds dimension is removed
        """
        # Get the sorted indices
        sorted_idxs = _sorted_idxs(mech_sens)
        # Get unsorted reaction names. For mechs with less reactions than nrxns
        # (which is nrxns for the biggest mech), remaining reactions are Nones
        ndims, nrxns, _, _, _ = dim_info(mech_sens)
        rxns = np.ndarray(nrxns, dtype=object)  # default is None
        for reaction_idx, reaction in enumerate(gas.reactions()):
            rxns[reaction_idx] = reaction.equation
        # Sort
        sorted_rxns = rxns[sorted_idxs]

        return sorted_rxns

    def _sorted_idxs(mech_sens):
        """ Gets indices to sort sens coeffs for a single mech (large to small).
            For time-resolved experiments, the maximum is taken across all times
            for a single condition/target. For non-time-resolved data, the
            maximum is taken across all conditions for a single target.

            sorted_rxns has one less dimension than sens: for time-resolved,
            the time (or position) dimension is removed, while for non-time-
            resolved, the conds dimension is removed

            :return sorted_idxs: idxs that will sort a mech_sens array
            :rtype: Numpy.ndarray of shape (nrxns, nconds, ntargs) if
                time-resolved or (nrxns, ntargs)
        """
        # Get the max values along one axis (replace NaNs with 0; no warnings)
        if np.ndim(mech_sens) == 4:  # time-resolved
            max_vals = np.max(abs(np.nan_to_num(mech_sens)), axis=3)  # 3 is time
        else:  # ndims = 3; not time-resolved
            max_vals = np.max(abs(np.nan_to_num(mech_sens)), axis=1)  # 1 is cond
        # Although np.nanmax (used above) will prioritize numeric values over
        # NaNs, a reaction could have all NaNs if the reaction is absent from
        # the mech. So, replace NaNs with 0 before sorting to keep NaNs at end
        max_vals = np.nan_to_num(max_vals)
        sorted_idxs = np.argsort(max_vals, axis=0)[::-1]  # -1: large to small

        return sorted_idxs

    def dim_info(mech_sens):
        """ Gets information regarding the dimensionality of a mech_sens array
        """
        ndims = np.ndim(mech_sens)
        if ndims == 4:  # time-resolved
            nrxns, nconds, ntargs, ntimes = np.shape(mech_sens)
        elif ndims == 3:  # not time-resolved
            nrxns, nconds, ntargs = np.shape(mech_sens)
            ntimes = None
        else:
            raise NotImplementedError(
                f'mech_sens needs 3 or 4 dims, not {ndims}.')

        return ndims, nrxns, nconds, ntargs, ntimes

    sorted_mech_sens = _sorted_sens(mech_sens)
    sorted_mech_rxns = _sorted_rxns(mech_sens, gas)

    return sorted_mech_sens, sorted_mech_rxns


def get_filtered_results(sens, temps, ref_results, start_temp, end_temp):
    """

        :param sens: sens coeffs for each rxn, temp, and species
        :type sens: Numpy array of shape (nrxns, ntemps, nspcs)
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

    filt_sens = sens[:, start_idx:end_idx + 1, :]
    filt_temps = temps[start_idx:end_idx + 1]
    filt_ref_results = ref_results[start_idx:end_idx + 1]

    return filt_sens, filt_temps, filt_ref_results
