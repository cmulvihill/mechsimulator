from mechsimulator import plotter
from mechsimulator import parser


def test_st_conc():
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
    plotter.util.build_pdf(figs_axes, filename='output_st_conc.pdf')


def test_st_abs():
    """ Tests a shock tube simulation
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
    # Mech names input currently not working...
    mech_names = [
        'my_mech',
    ]
    dpdt = [
        2,
    ]

    # Plot the results
    figs_axes = plotter.main.mult_sets_filenames(
            exp_filenames, mech_filenames, spc_csv_filenames, calc_types,
            x_sources, conds_sources, mech_names=mech_names, dpdt=dpdt)
    plotter.util.build_pdf(figs_axes, filename='output_st_abs.pdf')


def test_st_abs2():
    """ Tests a shock tube simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/davidson_1990_o2.xlsx'
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
    plotter.util.build_pdf(figs_axes, filename='output_st_abs2.pdf')


def test_jsr():
    """ Tests a jet-stirred reactor simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/Tang_2021_NH3_JSR_phi05.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/glarborg_oh_star.cti',
        'data/glarborg_alturaifi_rates.cti',
        'data/glarborg_alturaifi_rates_therm.cti',
        # 'data/glarborg_alturaifi_from_sulaiman_rates_therm.cti',
    ]
    spc_csv_filenames = [
        'data/glarborg_oh_star_species.csv',
        'data/glarborg_oh_star_species.csv',
        'data/glarborg_oh_star_species.csv',
        # 'data/glarborg_oh_star_species.csv',
    ]
    # currently not working...
    mech_names = [
        'Glarborg',
        # '+ Alturaifi rates',
        # '+ Alturaifi therm',
        # 'from Sulaiman',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Plot the results
    figs_axes = plotter.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    plotter.util.build_pdf(figs_axes, filename='output_jsr.pdf')


def test_jsr2():
    """ Tests a jet-stirred reactor simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/yan_2022_rich_100_atm.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
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
    plotter.util.build_pdf(figs_axes, filename='output_jsr.pdf')


def test_pfr():
    """ Tests a jet-stirred reactor simulation
    """

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/stagni_2020_pfr.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/glarborg_no_c.cti',
        'data/glarborg_no_c_hnoh.cti'
    ]
    spc_csv_filenames = [
        'data/glarborg_species.csv',
        'data/glarborg_species.csv',
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
    plotter.util.build_pdf(figs_axes, filename='stagni_pfr_hnoh.pdf')


def test_st_idt():

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/mathieu_2015_phi05_99_1atm.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/glarborg_no_c.cti',
        'data/glarborg_no_c_hnoh.cti'
    ]
    spc_csv_filenames = [
        'data/glarborg_oh_star_species.csv',
        'data/glarborg_oh_star_species.csv',
        # 'data/glarborg_oh_star_species.csv',
    ]
    mech_names = [
        'Glarborg',
        '+ Alturaifi rates',
        '+ Alturaifi therm',
        # 'from Sulaiman',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Plot the results
    figs_axes = plotter.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    plotter.util.build_pdf(figs_axes, filename='output_st_idt_hnoh.pdf')


def test_lfs():

    # Inputs regarding experimental sets; should all be the same length
    exp_filenames = [
        'data/madeup_H2_O2_LFS.xlsx'
    ]
    calc_types = ['outcome']
    x_sources = ['plot']  # should be 'plot' or 'exps'
    conds_sources = ['plot']  # should be 'plot' or 'exps'

    # Inputs regarding mechanisms; should all be the same length
    mech_filenames = [
        'data/h2o2.yaml',
    ]
    spc_csv_filenames = [
        'data/glarborg_oh_star_species.csv',
        # 'data/glarborg_oh_star_species.csv',
    ]
    mech_names = [
        'Glarborg',
        '+ Alturaifi rates',
        '+ Alturaifi therm',
        # 'from Sulaiman',
    ]

    # Load the various objects using the filenames
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Plot the results
    figs_axes = plotter.main.mult_sets(
        exp_sets, gases, mech_spc_dcts, calc_types, x_sources, conds_sources)
    plotter.util.build_pdf(figs_axes, filename='output_lfs.pdf')


if __name__ == '__main__':
    # test_st_conc()
    test_st_abs()
    # test_st_abs2()
    # test_jsr()
    # test_jsr2()
    # test_pfr()
    # test_st_idt()
    # test_lfs()