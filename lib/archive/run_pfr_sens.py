import cantera as ct
import numpy as np
from mechsimulator.simulator import sens as sim
from mechsimulator.plotter import sens as plotter
from mechsimulator.writer import sens as writer

# Inputs
target_spcs = ['NH3',
               'NO',
               ]
mech_filename = '../bin/data/Glarborg.cti'
temps = np.linspace(900, 905, 2)  # K
# temps = [1000, ]
pressure = 1  # atm
mdot = 3.58e-5  # kg/s
length = 0.31  # m
area = 1.13e-4  # m^2
mix = {'NH3': 245e-6, 'H2': 330e-6, 'O2': 0.10, 'N2': 0.899425}
factor = 0.1
num_top_rxns = 25  # number of rxns to plot


# Run calculations
gas = ct.Solution(mech_filename)
sens_coeffs, ref_results = sim.pfr(
    temps, pressure, mix, gas, target_spcs, mdot, area, length, factor)

# Get the unsorted rxn names
rxn_names = sim.get_rxn_names(gas)

# Sort the results
sorted_idxs = sim.get_sorted_idxs(sens_coeffs)

# Write sensitivity results to file
writer.write_file(sens_coeffs, target_spcs, temps, rxn_names, ref_results,
                  filename='../bin/sens_results.xlsx')

# Plot the results
plotter.plot_sens(
    sens_coeffs, num_top_rxns, rxn_names, target_spcs, temps, ref_results)
