from mechsimulator.simulator import sens as sim
from mechsimulator.parser import sens as parser
from mechsimulator.plotter import sens as plotter


filename = 'sens_results_v70_450_900.xlsx'
num_top_rxns = 25  # number of rxns to plot
start_temp = 470
end_temp = 700

# Read the file
sens_coeffs, rxn_names, target_spcs, temps, ref_results = parser.read_file(
    filename)

# Get the filtered results
filt_sens_coeffs, filt_temps, filt_ref_results = sim.get_filtered_results(
    sens_coeffs, temps, ref_results, start_temp, end_temp)

# Plot the results
plotter.plot_sens(filt_sens_coeffs, num_top_rxns, rxn_names, target_spcs,
               filt_temps, filt_ref_results)
