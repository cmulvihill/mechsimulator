import cantera as ct
import numpy as np
from mechsimulator.simulator import sens as sim
from mechsimulator.plotter import sens as plotter
from mechsimulator.writer import sens as writer

# Inputs
# # For Danilack
# target_spcs = ['CH3CH2OCH2CH3',
#                'O2',
#                'CH4',
#                'C2H4',
#                'CH3C(O)OH',
#                'CO2',
#                'CO',
#                'CH2O',
#                'C2H6',
#                'CH3CH2OH',
#                'CH3CH2OCHCH2',
#                'CH3CHO',
#                'CH3CH2OCHO',
#                'CH3CH2OC(O)CH3',
#                'c-OCH2CH2OCH(CH3)',
#                'CH3C(O)OC(O)CH3'
#                ]

# For Tran
target_spcs = ['DEE',
               # 'CH3COOH',
               # 'C2H5OH',
               # 'C2H5OCHO',
               # 'EA',
               # 'AA',
               # 'CH2O',
]


mech_filename = '../../dee/mechanisms/Tran_fresh.cti'
# mech_filename = '../../dee/mechanisms/Danilack_thermal_stereo_v93.cti'
temps = np.linspace(805, 795, 3)  # K
pressure = 1.053  # atm
res_time = 2  # s
vol = 81.2e-6  # m^3
mix = {'DEE': 0.01, 'O2': 0.06, 'HE': 0.93}  # for Tran
# mix = {'CH3CH2OCH2CH3': 0.01, 'O2': 0.06, 'HE': 0.93}  # for Danilack
factor = 0.1
num_top_rxns = 35  # number of rxns to plot


# Run calculations
mech = ct.Solution(mech_filename)
sens_coeffs, ref_results = sim.jsr(
    temps, pressure, mix, mech, target_spcs, res_time, vol, factor)

# Get the unsorted rxn names
rxn_names = sim.get_rxn_names(mech)

# Sort the results
sorted_idxs = sim.get_sorted_idxs(sens_coeffs)

# Plot the results
plotter.plot_sens(sens_coeffs, num_top_rxns, rxn_names, target_spcs, temps,
                  ref_results)

# Write sensitivity results to file
writer.write_file(sens_coeffs, target_spcs, temps, rxn_names, ref_results,
                   filename='../bin/sens_results.xlsx')
