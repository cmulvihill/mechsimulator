from mechsimulator import parser
from mechsimulator import simulator


def test_jsr():
    """ Tests a JSR simulation
    """
    exp_filename = 'data/Tran_JSR_mdot.xlsx'
    mech_filenames = [
        '../../dee/mechanisms/Danilack_thermal_stereo_v8.cti',
    ]

    spc_csv_filenames = [
        'data/Danilack_species.csv',
    ]
    calc_type = 'outcome'
    plot_or_exps = 'exps'

    simulator.main.single_set(exp_filename, mech_filenames, spc_csv_filenames,
                              calc_type, plot_or_exps)


def test_st_abs():
    """ Tests a shock tube absorption simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/davidson_1990_no.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['exps']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/N2O_mechanism_Mulvihill.cti',
    ]
    spc_csv_filenames = [
        'data/Mulvihill_N2O_species.csv',
    ]
    mech_names = [
        # 'Glarborg',
        # '+ Alturaifi rates',
        # '+ Alturaifi therm',
        'from Sulaiman',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Run the simulations
    set_ydata_lst, set_xdata_lst = simulator.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    print('set_ydata_lst:\n', set_ydata_lst)
    print('set_xdata_lst:\n', set_xdata_lst)


def test_st_idt():
    """ Tests a shock tube IDT simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/mathieu_2015_phi05_99_1atm.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['exps']  # should be 'plot' or 'exps'
    conds_sources = ['exps']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/glarborg_no_c.cti',
    ]
    spc_csv_filenames = [
        'data/glarborg_oh_star_species.csv',
    ]
    mech_names = [
        # 'Glarborg',
        # '+ Alturaifi rates',
        # '+ Alturaifi therm',
        'from Sulaiman',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Run the simulations
    set_ydata_lst, set_xdata_lst = simulator.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)

    print('set_ydata_lst:\n', set_ydata_lst)
    print('set_xdata_lst:\n', set_xdata_lst)

if __name__ == '__main__':
    # test_jsr()
    test_st_abs()
    # test_st_idt()

