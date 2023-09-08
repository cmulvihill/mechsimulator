from mechsimulator.parser import exp
from mechsimulator.parser import spc
from mechsimulator.simulator import run_plot_OLD
from mechsimulator.plotter import comparisons
from mechsimulator.plotter import util
from mechsimulator.writer import sim_data

excel_filename = '../bin/data/Tran_JSR_mdot.xlsx'
mech_filenames = [
    # '../../dee/mechanisms/Tran_v1.cti',
    # '../../dee/mechanisms/Tran_v2.cti',
    # '../../dee/mechanisms/Tran_fresh.cti',
    # '../../dee/mechanisms/Tran_v53.cti',
    # '../../dee/mechanisms/Tran_v54.cti',

    '../../dee/mechanisms/Danilack_thermal_stereo_v8.cti',
]

mech_nicknames = ['fresh',
                  # 'v2',
                  # 'fresh',
                  # 'v53',
                  # 'v54',
]
spc_csv_filenames = [
# 'data/Danilack_species.csv',
# 'data/Danilack_species.csv',
'data/Danilack_species.csv',

# 'data/Tran_species.csv',
# 'data/Tran_species.csv',
# 'data/Tran_species.csv',
# 'data/Tran_species.csv',
# 'data/Tran_species.csv',
# 'data/Tran_species.csv',
]

# Read the exp_set
exp_set = exp.read_exp_file(excel_filename)
print(exp_set)


# Get the Cantera Solution objects
mechs = util.load_solution_objs(mech_filenames)

# Read the spc_ident_dcts
mech_spc_dcts = spc.mech_spc_dcts_from_filenames(spc_csv_filenames)

# Run the simulations
outputs = run_plot_OLD.mult_mechs(exp_set, mechs, mech_spc_dcts)

# Create the plots
figs_axes = comparisons.plot_single_set_jsr(outputs, mech_nicknames, exp_set)

# Produce a PDF
comparisons.build_pdf(figs_axes)

# Write simulation results to Excel
sim_data.write_mech_results(exp_set, outputs, mech_nicknames)

# Write exp data to Excel (sorted by species instead of condition)
sim_data.write_exp_data(exp_set)
