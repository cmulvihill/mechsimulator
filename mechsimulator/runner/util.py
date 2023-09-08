from mechsimulator.parser.exp_checker import ALLOWED_SIM_OPTS
from mechsimulator.parser.exp_checker import get_poss_inps


def _mech_opts_lst(exp_set, gases, kwarg_dct):
    """ Creates a list of mech_opts, one for each mechanism

        Note: the reason only a single exp_set is required is that the intention
        of this option is to run comparisons against a single set (e.g.,
        trying several values of dP/dt for a single exp_set). There is no way to
        vary some parameter in different ways for different experimental sets.
        However, options can still be used for multiple sets (e.g., mech_names
        for simulating multiple sets)

        :param kwarg_dct:
        :return:
    """

    # Only fill in mech_opts_lst if any kwargs were given
    if kwarg_dct != {}:
        # Initialize
        nmechs = len(gases)
        mech_opts_lst = []
        for mech_idx in range(nmechs):
            mech_opts_lst.append({})  # doing this way to keep dicts unrelated
        # Get the possible inputs for this reac/meas combination
        meas_type = exp_set['overall']['meas_type']
        reac_type = exp_set['overall']['reac_type']
        poss_inps = get_poss_inps(reac_type, meas_type, 'exps', rm_bad=True)
        # Loop over each keyword argument
        ok_names = tuple(ALLOWED_SIM_OPTS.keys()) + poss_inps + ('mech_names',)
        for inp_idx, (name, vals) in enumerate(kwarg_dct.items()):
            assert name in ok_names, (
                f"Input '{name}' not allowed for reactor '{reac_type}' and "
                f"measurement '{meas_type}'. Options are {ok_names}")
            assert isinstance(vals, (list, tuple)), (
                f"kwarg '{name}' should be list or tuple, not {type(vals)}")
            # Check the list length
            assert len(vals) == nmechs, (
                f'Entries in kwarg_dct, {kwarg_dct}, should all be the length '
                f'of the number of mechanisms, {nmechs}')
            # Add each value for the kwarg to each mech_opts dict
            for mech_idx, val in enumerate(vals):
                mech_opts_lst[mech_idx][name] = val
    # If no kwargs, return None
    else:
        mech_opts_lst = None

    return mech_opts_lst


def check_inputs(job_dct, exp_sets):
    """ Check a few things on the input job parameters/exp_sets

        :param job_dct: dictionary describing the job
        :type job_dct: dict
        :param exp_sets: list of experiment objects
        :type exp_sets: list
    """

    # If there are zero experiments in a set (i.e., only the 'plot' field has
    # information), then check that the conds_src is not 'exps'
    for set_idx, exp_set in enumerate(exp_sets):
        nexps = exp_set['overall']['num_exps']
        cond_src = job_dct['cond_srcs'][set_idx]
        if nexps == 0:
            assert cond_src != 'exps', ("With zero experiments in the set, the"
                                        " condition source cannot be 'exps'")
