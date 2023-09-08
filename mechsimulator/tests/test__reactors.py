""" Tests the mechsimulator.simulator.reactors module
"""

import cantera as ct
import numpy as np
from mechsimulator.simulator import reactors
from mechsimulator.simulator import util


def test_st_no_dpdt():
    """ Tests the st function, without any dP/dt
    """

    mech_filename = 'data/Hong_MECH.cti'
    gas = ct.Solution(mech_filename)
    temp = 952
    pressure = 3.5
    mix = {'H2': 0.04, 'O2': 0.02, 'Ar': 0.94}
    target_spcs = ['OH',]
    end_time = 0.05

    # Run simulations and get IDT
    target_concs, times = reactors.st(temp, pressure, mix, gas, target_spcs,
                                      end_time)
    target_conc = target_concs[0]
    idt, warnings = util._get_st_idt(target_conc, times, plot=False, method=1)
    assert isinstance(idt, float)
    assert len(warnings) == 0


def test_st_with_dpdt():
    """ Tests the st function with dP/dt
    """

    mech_filename = 'data/Hong_MECH.cti'
    gas = ct.Solution(mech_filename)
    dpdt = 0.02  # units of %/ms
    end_time = 0.02  # seconds
    p_of_t = np.array([[0, end_time], [1, 1 + dpdt * (end_time * 1000)]])
    temp = 952
    pressure = 3.5
    mix = {'H2': 0.04, 'O2': 0.02, 'Ar': 0.94}
    target_spcs = ['OH',]
    end_time = 0.02

    # Run simulations and get IDT
    target_concs, times = reactors.st(temp, pressure, mix, gas, target_spcs,
                                      end_time, p_of_t=p_of_t)
    target_conc = target_concs[0]
    idt, warnings = util._get_st_idt(target_conc, times, plot=False, method=3)
    assert isinstance(idt, float)
    assert len(warnings) == 0


def test_rcm():
    """ Tests the rcm function
    """

    gas = ct.Solution('gri30.xml')  # this .xml file comes with Cantera
    temp = 500
    pressure = 1
    mix = {'CH4': 0.1, 'O2': 0.2, 'N2': 0.7}
    gas.set_equivalence_ratio(1, 'CH4:1', 'O2:1, N2:3.76')
    end_time = 0.1
    v_of_t = np.genfromtxt('data/t_V_profile.csv', delimiter=',',
                           skip_header=1)
    v_of_t = v_of_t.transpose()
    pressures, times = reactors.rcm(temp, pressure, mix, gas, end_time, v_of_t)
    idt, warnings = util._get_rcm_idt(pressures, times)


def test_const_t_p():
    """ Tests the const_t_p function
    """
    gas = ct.Solution('gri30.xml')  # this .xml file comes with Cantera
    temp = 1000
    pressure = 1
    mix = {'CH4': 0.1, 'O2': 0.2, 'N2': 0.7}
    gas.set_equivalence_ratio(1, 'CH4:1', 'O2:1, N2:3.76')
    target_spcs = ['H2O', 'OH']
    end_time = 0.1

    target_concs, times = reactors.const_t_p(temp, pressure, mix, gas,
                                             target_spcs, end_time)


def test_pfr():
    """ Tests the pfr function
    """
    gas = ct.Solution('gri30.xml')  # this .xml file comes with Cantera
    temp = 900
    pressure = 6
    mix = {'CH4': 0.07, 'O2': 0.07, 'Ar': 0.86}
    target_spcs = ['CH4', 'O2', 'H2O']
    mdot = 4e-5  # kg/s
    area = 1e-4  # m^2
    length = 0.3  # m
    target_concs, times, positions = reactors.pfr(
        temp, pressure, mix, gas, target_spcs, mdot, area, length)

    assert np.shape(target_concs)[0] == len(target_spcs)


def test_jsr():
    """ Tests the jsr function
    """
    gas = ct.Solution('gri30.xml')  # this .xml file comes with Cantera
    temp = 800
    pressure = 1
    mix = {'CH4': 0.005, 'O2': 0.04, 'Ar': 0.955}
    target_spcs = ['CH4', 'O2', 'H2O']
    res_time = 0.1  # s
    vol = 8e-5  # m^3

    target_concs, all_concs = reactors.jsr(
        temp, pressure, mix, gas, target_spcs, res_time, vol)

    assert np.shape(target_concs)[0] == len(target_spcs)


if __name__ == '__main__':
    test_st_no_dpdt()
    test_st_with_dpdt()
    test_rcm()
    test_const_t_p()
    test_pfr()
    test_jsr()
