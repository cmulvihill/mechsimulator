from mechsimulator import simulator


def single_mech(conds_dct, gas, reac_type, ydata_shape):
    """

        :param conds_dct:
        :param gas:
        :param reac_type:
        :return:
    """

    mech_end_tpx = simulator.outcome.single_mech(
        conds_dct, gas, reac_type, 'pathways', None, ydata_shape)

    return mech_end_tpx
