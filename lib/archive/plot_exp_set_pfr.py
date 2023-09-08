from mechsimulator.parser import exp
from mechsimulator.parser import spc
from mechsimulator.simulator import full_set
from mechsimulator.plotter import comparisons
from mechsimulator.plotter import util
from mechsimulator.writer import sim_data

# excel_filename = 'data/Tran_JSR.xlsx'
excel_filename = '../bin/data/Wargadalam 2000.xlsx'
mech_filenames = ['data/Glarborg.cti']

mech_nicknames = ['80-20 (v73)',]
spc_csv_filenames = ['data/Glarborg_species.csv',
]

# Read the exp_set
exp_set = exp.read_exp_file(excel_filename)
print(exp_set)

# Get the Cantera Solution objects
mechs = util.load_solution_objs(mech_filenames)

# Read the spc_ident_dcts
spc_ident_dcts = spc.get_spc_ident_dcts(spc_csv_filenames)

# Run the simulations
outputs = full_set.mult_mechs_plotting(exp_set, mechs, spc_ident_dcts)

# Create the plots
figs_axes = comparisons.plot_single_set_jsr(outputs, mech_nicknames, exp_set)

# Produce a PDF
comparisons.build_pdf(figs_axes)

# Write simulation results to Excel
sim_data.write_mech_results(exp_set, outputs, mech_nicknames)

# Write exp data to Excel (sorted by species instead of condition)
sim_data.write_exp_data(exp_set)






