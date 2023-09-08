""" Script for demonstrating potential issues with reaction pathway analyzer
"""

import os
import cantera as ct
import numpy as np


def jsr(temp, pressure, mix, gas, target_spcs, res_time, vol, prev_concs=None,
        mdot=None, max_iter=30000):
    """ Runs a jet-stirred reactor simulation

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
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
        :param vol: volume of the reactor (m^3)
        :type vol: float
        :param prev_concs: species concentrations from previous solution at
            a similar condition
        :type prev_concs: numpy array of shape (num_spcs_in_mechanism,)
        :param max_iter: max number of timesteps to achieve steady state
        :type max_iter: int
        :return target_concs: outlet concentrations of target_spcs
        :rtype: Numpy array of shape (num_targets,)
        :return all_concs: outlet concentrations of all species in mech
        :rtype: Numpy array of shape (num_spcs_in_mechanism,)
    """

    pressure = pressure * 101325  # atm to Pa
    gas.TPX = temp, pressure, mix

    # Create reservoirs
    inlet = ct.Reservoir(gas)
    exhaust = ct.Reservoir(gas)

    # Create reactor
    prev_concs_input = True
    if prev_concs is None:
        prev_concs_input = False
        prev_concs = mix
    gas.TPX = temp, pressure, prev_concs  # prev_concs to speed up convergence
    reac = ct.IdealGasReactor(gas, energy='off', volume=vol)

    # Set up devices
    pressure_valve_coeff = 0.01  # "conductance" of the pressure valve
    ct.Valve(upstream=reac, downstream=exhaust, K=pressure_valve_coeff)
    if res_time is not None:  # MFC condition depends on inputs
        ct.MassFlowController(upstream=inlet, downstream=reac,
                              mdot=reac.mass / res_time)
    elif mdot is not None:
        ct.MassFlowController(upstream=inlet, downstream=reac, mdot=mdot)

    # Create reactor network (only the JSR in this case) and advance it to SS
    reac_net = ct.ReactorNet([reac])
    failure = False
    try:
        reac_net.advance_to_steady_state(max_steps=max_iter)
        all_concs = reac.thermo.X  # store output concentrations
    except ct._cantera.CanteraError:
        failure = True
        print(f'The solver failed at {temp} K for mechanism {gas.name}')
        # If no initial guess, next iteration will use initial mix as guess
        if prev_concs_input is False:
            all_concs = None
        # If an initial guess was input, return it for use in the next iteration
        else:
            all_concs = prev_concs

    # Get results for target species
    target_concs = np.zeros(len(target_spcs))
    for idx, target_spc in enumerate(target_spcs):
        if failure:
            target_concs[idx] = None
        else:
            if target_spc in gas.species_names:
                target_concs[idx] = all_concs[gas.species_index(target_spc)]
            else:  # if the target_spc isn't in the mechanism
                target_concs[idx] = None
    end_gas = gas
    rop = None

    return target_concs, all_concs, rop, end_gas


def generate_pdf(gas, element, thresh, filename):
    """ Generates a PDF with the reaction pathway diagram
    """

    # Generate the pathways diagram
    diagram = ct.ReactionPathDiagram(gas, element)

    # Do some formatting
    diagram.show_details = True
    diagram.font = 'CMU Serif Roman'
    diagram.threshold = thresh
    diagram.dot_options = 'node[fontsize=20,shape="box"]'
    diagram.title = f'Reaction path diagram following {element}\n'
    diagram.scale = 1  # -1 normalizes, 1 leaves raw values

    # Write files; will be written to calling script's directory
    dot_filename = 'temp_dotfile.dot'
    diagram.write_dot(dot_filename)
    os.system('dot {0} -Gdpi=300 -Tpdf -o{1}'.format(dot_filename, filename))
    os.remove(dot_filename)


# Load Solution object
mech_filename = 'mymech.cti'
gas = ct.Solution(mech_filename)

# Define simulation conditions
temp = 675  # K
pressure = 100  # atm
mix = {'CH3OCH3': 0.01303, 'O2': 0.0227, 'N2': 0.96427}  # mole fraction
target_spcs = ('O2',)  # not used
res_time = None  # using fixed mass flow rate instead of fixed residence time
vol = 4e-7  # m3
mdot = 7.80159e-5  # kg/s

# Silly way of defining previous concentrations; normally this would be done by
# using a previous solution, but I'm trying to simplify for this example
# (Length of array is 130, which is the number of species in the mechanism)
prev_concs = np.array([
    3.68E-11,1.49E-04,9.86E-19,2.37E-21,
    3.85E-11,2.94E-14,7.91E-07,3.87E-10,
    9.96E-03,2.38E-32,1.22E-18,1.25E-19,
    6.06E-03,9.59E-01,8.83E-11,4.89E-10,
    1.35E-16,1.69E-03,1.47E-11,4.34E-11,
    1.09E-10,7.84E-03,6.31E-04,4.90E-06,
    3.84E-03,8.90E-20,9.29E-13,9.33E-24,
    4.46E-15,5.09E-14,1.64E-03,2.11E-09,
    1.01E-13,2.56E-18,6.60E-18,1.54E-15,
    1.22E-09,3.07E-03,5.97E-03,1.00E-10,
    2.19E-11,1.09E-08,2.93E-04,2.01E-09,
    8.76E-05,7.29E-10,2.10E-09,4.43E-14,
    3.83E-06,2.06E-09,1.67E-05,3.53E-06,
    2.50E-07,7.85E-33,1.79E-52,4.53E-34,
    1.03E-26,8.27E-20,6.59E-27,2.22E-08,
    2.50E-06,1.05E-33,3.79E-37,1.42E-32,
    1.92E-24,3.88E-18,6.36E-34,8.48E-21,
    6.09E-19,2.22E-26,4.80E-23,6.04E-27,
    9.95E-22,3.75E-32,3.87E-34,9.71E-28,
    1.61E-31,5.19E-28,9.32E-23,1.54E-24,
    4.13E-25,1.79E-32,2.78E-11,3.45E-44,
    2.54E-46,5.05E-44,9.16E-39,4.22E-36,
    1.15E-38,2.83E-46,4.00E-19,9.69E-38,
    9.69E-21,1.20E-39,6.93E-40,6.98E-55,
    1.51E-56,2.27E-44,2.01E-46,4.66E-27,
    1.40E-26,1.78E-43,4.06E-40,3.95E-35,
    4.17E-42,1.11E-34,6.41E-35,5.57E-29,
    8.57E-10,9.83E-13,8.34E-06,3.93E-09,
    1.46E-11,0.00E+00,0.00E+00,0.00E+00,
    0.00E+00,0.00E+00,0.00E+00,0.00E+00,
    0.00E+00,0.00E+00,0.00E+00,6.18E-09,
    0.00E+00,6.57E-07,4.43E-05,0.00E+00,
    0.00E+00,0.00E+00
    ]
)


# Call the jsr function to run the simulation
_, all_concs, _, end_gas = jsr(
    temp, pressure, mix, gas, target_spcs, res_time, vol, prev_concs=prev_concs,
    mdot=mdot)

# ------------------ Problem 1: flux values off by factor of 2 ----------------

# Generate the PDF of the reaction pathway diagram
element = 'C'
generate_pdf(gas, element, 0.001, 'sample_diagram.pdf')

# Print some values pertaining to different rates of progress
rxns = gas.reaction_equations()  # used later

# RO2 = QOOH
rxn_idx = 821
print(rxns[rxn_idx])
print(f'net progress: {gas.net_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera forward progress: {gas.forward_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera reverse progress: {gas.reverse_rates_of_progress[rxn_idx]:.2e}')
fwd_rate_constant = gas.forward_rate_constants[rxn_idx]  # s-1
print(f'forward rate constant: {fwd_rate_constant:.2e}')
conc = gas.concentrations[gas.species_index("RO2")]  # kmol/m3
calc_fwd_prog = conc * fwd_rate_constant
print(f'calculated "by hand" forward progress: {calc_fwd_prog:.2e}')
if np.isclose(calc_fwd_prog, gas.forward_rates_of_progress[rxn_idx]):
    print('Cantera and "by hand" forward progress are the same')
else:
    print('Cantera and "by hand" forward progress are different!')
print('\n')


# R + O2 = RO2
rxn_idx = 814
print(rxns[rxn_idx])
print(f'net progress: {gas.net_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera forward progress: {gas.forward_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera reverse progress: {gas.reverse_rates_of_progress[rxn_idx]:.2e}')
fwd_rate_constant = gas.forward_rate_constants[rxn_idx]  # m3/kmol-s
print(f'forward rate constant: {fwd_rate_constant:.2e}')
ro2_conc = gas.concentrations[gas.species_index("R")]  # kmol/m3
o2_conc = gas.concentrations[gas.species_index("O2")]  # kmol/m3
calc_fwd_prog = ro2_conc * o2_conc * fwd_rate_constant
print(f'"by hand" forward progress: {calc_fwd_prog:.2e}')
if np.isclose(calc_fwd_prog, gas.forward_rates_of_progress[rxn_idx]):
    print('Cantera and "by hand" forward progress are the same')
else:
    print('Cantera and "by hand" forward progress are different!')
print('\n')


# QOOH + O2 = O2QOOH
rxn_idx = 823
print(rxns[rxn_idx])
print(f'net progress: {gas.net_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera forward progress: {gas.forward_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera reverse progress: {gas.reverse_rates_of_progress[rxn_idx]:.2e}')
fwd_rate_constant = gas.forward_rate_constants[rxn_idx]  # m3/kmol-s
print(f'forward rate constant: {fwd_rate_constant:.2e}')
qooh_conc = gas.concentrations[gas.species_index("QOOH")]  # kmol/m3
o2_conc = gas.concentrations[gas.species_index("O2")]  # kmol/m3
calc_fwd_prog = qooh_conc * o2_conc * fwd_rate_constant
print(f'"by hand" forward progress: {calc_fwd_prog:.2e}')
if np.isclose(calc_fwd_prog, gas.forward_rates_of_progress[rxn_idx]):
    print('Cantera and "by hand" forward progress are the same')
else:
    print('Cantera and "by hand" forward progress are different!')
print('\n')


# ------------- Problem 2: reaction is missing from pathway diagram ------------

# RO2 + RO2 = RO + RO + O2
rxn_idx = 816
print(rxns[rxn_idx])
print(f'net progress: {gas.net_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera forward progress: {gas.forward_rates_of_progress[rxn_idx]:.2e}')
print(f'Cantera reverse progress: {gas.reverse_rates_of_progress[rxn_idx]:.2e}')
fwd_rate_constant = gas.forward_rate_constants[rxn_idx]  # m3/kmol-s
print(f'forward rate constant: {fwd_rate_constant:.2e}')
conc = gas.concentrations[gas.species_index("RO2")]  # kmol/m3
calc_fwd_prog = conc * conc * fwd_rate_constant
print(f'"by hand" forward progress: {calc_fwd_prog:.2e}')
if np.isclose(calc_fwd_prog, gas.forward_rates_of_progress[rxn_idx]):
    print('Cantera and "by hand" forward progress are the same')
else:
    print('Cantera and "by hand" forward progress are different!')
print('\n')
