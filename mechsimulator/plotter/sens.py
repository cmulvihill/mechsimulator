import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib import cm
from mechsimulator.plotter import util

LINES = ['-', '--', '-.', ':']


def single_set(set_sens_coeffs, set_xdata, set_rxn_names, set_ref_results,
               exp_set, conds_source, mech_names=None):
    """ Plots sensitivity coefficients for a single exp_set. Each mechanism gets
        its own set of pages, and each condition/target combination gets its own
        page (only applicable to time-resolved sens coeffs)

        Note: no sorting is done; things are plotted in the given order

        :param set_sens_coeffs:
        :param set_xdata:
        :param set_ref_results:
        :param set_rxn_names: I think this is an array of the rxn names for each mechanism
        :param exp_set:
        :param conds_source:
        :param mech_names:
        :return:
    """

    # Initialize some variables
    set_frmt = exp_set['plot_format']
    num_mechs = len(set_rxn_names)
    mech_names = mech_names or [f'mech {idx + 1}' for idx in range(num_mechs)]

    # Loop over each mechanism and plot
    set_figs_axes = []
    for mech_idx in range(num_mechs):
        # Get the values for the current mechanisms
        mech_sens_coeffs = set_sens_coeffs[mech_idx]
        mech_ref_results = set_ref_results[mech_idx]
        mech_rxn_names = set_rxn_names[mech_idx]
        # Initialize empty figures
        mech_figs_axes = build_mech_figs_axes(
            exp_set, mech_names, set_frmt, conds_source)
        # Plot on the axes and store them
        mech_figs_axes = single_mech(
            mech_sens_coeffs, mech_ref_results, mech_rxn_names, set_xdata,
            mech_figs_axes)
        set_figs_axes.extend(mech_figs_axes)

    return set_figs_axes


def single_mech(mech_sens_coeffs, mech_ref_results, mech_rxn_names, xdata,
                mech_figs_axes):
    """ Plots sensitivity coefficients of a single mechanism. Each
        condition/target combination gets its own page

        :param mech_sens_coeffs:
        :param mech_ref_results:
        :param mech_rxn_names:
        :param xdata:
        :param mech_figs_axes:
        :return:
    """

    # Load some information
    ndims = np.ndim(mech_sens_coeffs)
    assert ndims in (3, 4), (
        f"'sens_coeffs' should have 3 or 4 dimensions, not {ndims}")
    colors = cm.rainbow(np.linspace(1, 0, len(mech_rxn_names)))

    # Get numbers of conditions and targets
    if ndims == 4:
        _, num_conds, num_targets, _ = np.shape(mech_sens_coeffs)
    else:  # ndims = 3
        _, num_conds, num_targets = np.shape(mech_sens_coeffs)

    # Get information on how the plots are to be organized
    if ndims == 4:
        num_grps = num_conds  # number of plotting groups
        num_plts = num_targets  # number of plots per group
    else:  # ndims = 3
        num_grps = 1  # for ndims = 3, all targets are plotted as one group
        num_plts = num_targets

    # Loop over each condition and target, creating a plot for each
    for grp_idx in range(num_grps):
        for plt_idx in range(num_plts):
            # Extract values for this species from the arrays
            if ndims == 4:  # time-resolved
                target_sens_coeffs = mech_sens_coeffs[:, grp_idx, plt_idx]
                target_ref_results = mech_ref_results[grp_idx, plt_idx]
                target_rxn_names = mech_rxn_names[:, grp_idx, plt_idx]
            else:  # ndims = 3; not time-resolved
                target_sens_coeffs = mech_sens_coeffs[:, :, plt_idx]
                target_ref_results = mech_ref_results[:, plt_idx]
                target_rxn_names = mech_rxn_names[:, plt_idx]
            # Get the current figure and axes
            fig_idx = grp_idx * num_targets + plt_idx
            fig_axes = mech_figs_axes[fig_idx]
            # Plot
            fig_axes = plot_single_target(target_sens_coeffs, target_rxn_names,
                                          target_ref_results, fig_axes, xdata,
                                          colors)
            mech_figs_axes[fig_idx] = fig_axes

    return mech_figs_axes


def plot_single_target(target_sens_coeffs, target_rxn_names, target_ref_results,
                       fig_axes, xdata, colors):
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

    axes = fig_axes[1]
    for rxn_idx, rxn in enumerate(target_rxn_names):
        rxn_sens_coeffs = target_sens_coeffs[rxn_idx]
        rxn_name = target_rxn_names[rxn_idx]
        axes[0].plot(xdata, rxn_sens_coeffs, label=rxn_name,
                    color=colors[rxn_idx], linestyle=LINES[rxn_idx % 4])
    axes[0].legend(fontsize=7, bbox_to_anchor=(1.0, 1.01))
    axes[1].plot(xdata, target_ref_results)  # plot ref_results

    return fig_axes


def build_mech_figs_axes(exp_set, mech_name, set_frmt, conds_source):
    """ Builds a list of figures and axes for a single mechanism (each
        condition/target combination gets its own page)
    """

    # Don't know what to do with the mech_name input yet...

    # Load some information
    xunit = set_frmt['xunit']
    yunit = set_frmt['yunit']
    rows = 5
    columns = 3

    # Get the titles and axis labels
    cond_titles, xlabel, _ = util.get_cond_titles(exp_set, conds_source,
                                                  xunit=xunit)
    target_titles, ylabel, _ = util.get_targ_titles(exp_set, yunit=yunit)
    num_grps = len(cond_titles)
    num_plts = len(target_titles)  # plots per group; each plot gets a page

    # Create a page for each condition/target combination
    mech_figs_axes = []
    for grp_idx in range(num_grps):
        for plt_idx in range(num_plts):
            fig = plt.figure(figsize=(11, 8.5))
            title = f'{cond_titles[grp_idx]}\n{target_titles[plt_idx]}'
            fig.suptitle(title, y=0.96, fontsize=20)
            grid = plt.GridSpec(rows, columns, wspace=0.3)
            axes = []
            axes.append(plt.subplot(grid[0:(rows - 1), 0:(columns - 1)]))
            axes[0].set_xticklabels([])
            plt.yticks(fontsize=8)
            # plt.ylabel('Sensitivity coefficient', fontsize=14)
            axes[0].yaxis.set_major_formatter(FormatStrFormatter('%0.2E'))
            axes.append(plt.subplot(grid[(rows - 1):rows, 0:(columns - 1)]))
            # plt.xlabel('Temperature (K)', fontsize=14)
            # plt.ylabel('Mole fraction', fontsize=14)
            plt.yticks(fontsize=8)
            axes[1].yaxis.set_major_formatter(FormatStrFormatter('%0.2E'))
            mech_figs_axes.append([fig, axes])

    return mech_figs_axes
