import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib import cm
from mechsimulator.simulator import sens as sim_sens
from mechsimulator.plotter import util

LINES = ['-', '--', '-.', ':']

def single_set():
    pass


def single_mech(sens_coeffs, num_top_rxns, rxn_names, target_spcs, temps,
                ref_results, filename='sens_plots.pdf'):

    # Get the sorted sens values and the sorted rxn names
    sorted_idxs = sim_sens.get_sorted_idxs(sens_coeffs)
    sorted_sens_coeffs = sim_sens.get_sorted_sens_coeffs(sens_coeffs, sorted_idxs)
    sorted_rxn_names = sim_sens.get_sorted_rxn_names(sorted_idxs, rxn_names)

    # Get values for the indicated number of top rxns
    sorted_sens_coeffs = sorted_sens_coeffs[:num_top_rxns]
    sorted_rxn_names = sorted_rxn_names[:num_top_rxns]

    figs = []
    for spc_idx, spc in enumerate(target_spcs):
        # Extract values for this species from the arrays
        spc_sorted_sens_coeffs = sorted_sens_coeffs[:, :, spc_idx]
        spc_sorted_rxn_names = sorted_rxn_names[:, spc_idx]
        spc_ref_results = ref_results[:, spc_idx]
        # Plot
        fig, axs = build_fig_and_axs(spc)
        fig, axs = plot_single_spc(spc_sorted_sens_coeffs, spc_sorted_rxn_names,
                                   spc_ref_results, fig, axs, temps,
                                   num_top_rxns)
        figs.append(fig)

    util.build_pdf(figs, filename=filename)

    return figs


def plot_single_spc(spc_sens_coeffs, spc_rxn_names, spc_ref_results, fig, axs,
                    temps, num_top_rxns):
    """ Plots the

        :param spc_sens_coeffs: array of sens coeffs at all temps for one spc
        :type spc_sens_coeffs: Numpy array of shape (num_rxns, num_temps)
        :param spc_rxn_names: array of rxn names in the order of spc_sens_coeffs
        :type spc_rxn_names: Numpy array of shape (num_rxns,), with dtype=object
        :param spc_ref_results: reference results at all temps for one spc
        :type spc_ref_results: Numpy array of shape (num_temps,)
        :param fig: the figure object containing the axes
        :type fig: PyPlot figure object
        :param axs: list containing the two axis objects
        :type axs: list [ax1, ax2]
    """
    COLORS = cm.rainbow(np.linspace(0, 1, num_top_rxns))
    for rxn_idx, rxn in enumerate(spc_rxn_names):
        rxn_sens_coeffs = spc_sens_coeffs[rxn_idx, :]
        rxn_name = spc_rxn_names[rxn_idx]
        axs[0].plot(temps, rxn_sens_coeffs, label=rxn_name,
                    color=COLORS[rxn_idx], linestyle=LINES[rxn_idx % 4])
    axs[0].legend(fontsize=7, bbox_to_anchor=(1.0, 1.01))
    axs[1].plot(temps, spc_ref_results)  # add the species concentration plot

    return fig, axs


def build_fig_and_axs(spc):
    """ Builds a figure and axes for the species (each spc gets its own page)

        :param spc: name of the species that goes with the fig and axes
        :type spc: str
        :return fig: figure for the species
        :rtype: MatPlotLib figure object
        :return axes: list of MatPlotLib
        :rtype: list of length 2
    """
    rows = 5
    columns = 3
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle(f'{spc}', y=0.96, fontsize=20)
    grid = plt.GridSpec(rows, columns, wspace=0.3)
    axs = []
    # First axis
    axs.append(plt.subplot(grid[0:(rows-1), 0:(columns-1)]))
    axs[0].set_xticklabels([])
    plt.yticks(fontsize=8)
    plt.ylabel('Sensitivity coefficient', fontsize=14)
    axs[0].yaxis.set_major_formatter(FormatStrFormatter('%0.2E'))
    # Second axis
    axs.append(plt.subplot(grid[(rows-1):rows, 0:(columns-1)]))
    plt.xlabel('Temperature (K)', fontsize=14)
    plt.ylabel('Mole fraction', fontsize=14)
    plt.yticks(fontsize=8)
    axs[1].yaxis.set_major_formatter(FormatStrFormatter('%0.2E'))

    return fig, axs
