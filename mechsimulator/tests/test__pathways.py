from mechsimulator import plotter
from mechsimulator import parser


def test_st():
    """ Tests a shock tube simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/Mulvihill_2021_N2O.xlsx'
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
    # Mech names input currently not working...
    # mech_names = [
    #     'my_mech',
    # ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Plot the results
    figs_axes = plotter.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    plotter.util.build_pdf(figs_axes, filename='output_st.pdf')


def test_jsr():
    """ Tests a jet-stirred reactor simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/yan_2022_100_atm_rich.xlsx'
    ]
    calc_types = ['pathways']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        # 'data/HPmechv3_FAKE.cti',
        'data/HPmechv3.cti',
    ]
    spc_csv_filenames = [
        'data/hpmechv3_species.csv',
    ]
    # currently not working...
    mech_names = [
        'Glarborg',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Plot the results
    figs_axes = plotter.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    plotter.util.build_pdf(figs_axes, filename='pathways_jsr.pdf')


if __name__ == '__main__':
    # test_st()
    test_jsr()
    # test_idt()
