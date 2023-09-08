""" Tests the mechsimulator.parser.exp module
"""

import os
import numpy as np
from mechsimulator.parser import exp

PATH = os.path.dirname(os.path.realpath(__file__))
DAT_PATH = os.path.join(PATH, 'data')


def test_convert_units():
    """ Tests the convert_units function
    """

    val1 = 671.67
    quant1 = 'temp'
    units1 = 'R'
    conv_val1 = exp.convert_units(val1, quant1, units1)
    assert np.isclose(conv_val1, 373.15, rtol=1e-3)

    val2 = 1
    quant2 = 'pressure'
    units2 = 'MPa'
    conv_val2 = exp.convert_units(val2, quant2, units2)
    assert np.isclose(conv_val2, 9.869, rtol=1e-3)

    val3 = 100
    quant3 = 'temp'
    units3 = 'C'
    conv_val3 = exp.convert_units(val3, quant3, units3)
    assert np.isclose(conv_val3, 373.15, rtol=1e-3)

    val4 = 212
    quant4 = 'temp'
    units4 = 'F'
    conv_val4 = exp.convert_units(val4, quant4, units4)
    assert np.isclose(conv_val4, 373.15, rtol=1e-3)

    val5 = 1
    quant5 = 'length'
    units5 = 'cm'
    conv_val5 = exp.convert_units(val5, quant5, units5)
    assert np.isclose(conv_val5, 0.01, rtol=1e-3)

    val6 = 'random'
    quant6 = ''
    units6 = '-'
    conv_val6 = exp.convert_units(val6, quant6, units6)
    assert conv_val6 == 'random'


def test_st_conc():
    """ Tests the reading of an Excel file for a st_abs experiment
    """

    filename = 'Mulvihill_2021_N2O.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)


def test_st_abs():
    """ Tests the reading of an Excel file for a st_abs experiment
    """
    filename = 'davidson_1990_no.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)
    print(_['mix'])


def test_st_idt():
    """ Tests the reading of an Excel file for a st_idt experiment
    """
    filename = 'Mathieu_2015_phi05_99_1atm.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)
    print(_)


def test_pfr():
    """ Tests the reading of an Excel file for a pfr experiment
    """
    filename = 'stagni_2020_pfr.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)


def test_jsr():
    """ Tests the reading of an Excel file for a jsr experiment
    """
    filename = 'sample_jsr_v1.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)


def test_const_t_p_abs():
    """ Tests the reading of an Excel file for a const_t_p experiment
    """
    filename = 'sample_const_t_p_abs_v1.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)
    print(_['plot_format'])


def test_rcm_idt():
    """ Tests the reading of an Excel file for an rcm experiment
    """
    filename = 'sample_rcm_idt_v1.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)
    print(_['plot_format'])


def test_mdot_jsr():

    filename = 'Tran_JSR_mdot.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)


def test_lfs():

    filename = 'sample_lfs.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)
    print('sim_opts:\n', _['sim_opts'])
    print(type(_['sim_opts']['ratio']))


def test_num_dens():
    # filename = 'sample_num_dens.xlsx'
    filename = 'couch_2022_dme_450k_num_dens.xlsx'
    filepath = os.path.join(DAT_PATH, filename)
    _ = exp.load_exp_set(filepath)


if __name__ == '__main__':
    # test_convert_units()
    # test_st_conc()
    # test_st_abs()
    # test_st_idt()
    # test_pfr()
    # test_jsr()
    # test_const_t_p_abs()
    # test_rcm_idt()
    # test_mdot_jsr()
    # test_lfs()
    test_num_dens()
