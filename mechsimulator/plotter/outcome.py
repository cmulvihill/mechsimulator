import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter as Formatter
from mechsimulator.plotter import util
from mechsimulator.parser.exp import ALLOWED_UNITS

# Define some stuff for plot formatting
COLORS = ['Red', 'Blue', 'Green', 'Black', 'Magenta', 'Pink']
LINESTYLES = ['-', '--', '-.', ':']
REAC = {
    'st':           'ST',
    'rcm':          'RCM',
    'jsr':          'JSR',
    'pfr':          'PFR',
    'const_t_p':    'Const. TP',
    'free_flame':   'Free flame',
}
MEAS = {
    'abs':          'Absorption',
    'emis':         'Emission',
    'conc':         'Concentration',
    'ion':          'Ion',
    'pressure':     'Pressure',
    'idt':          'IDT',
    'outlet':       'Outlet',
    'lfs':          'Flame speed',
    'half_life':    'Half-life',
}


def single_set(set_ydata, set_xdata, exp_set, conds_src, mech_opts_lst=None):
    """ Plots results from a single set (i.e., any number of mechanisms). Also
        plots the experimental data if there are any

        :param set_ydata: the simulation results for a single set (i.e., for
            multiple mechanisms); shape=(nmechs, nconds, ntargs,
            ntimes) (the last dimension is omitted for some meas_types)
        :type set_ydata: numpy.ndarray
        :param set_xdata: the uniform x data used for all mechanisms; 1-D
        :type set_xdata: numpy.ndarray
        :param exp_set: exp_set object
        :type exp_set: dict
        :param conds_src: the source of the conditions; 'plot' or 'exps'
        :type conds_src: str
        :return figs_axes: list of figures with plots [(fig1, ax1), ...]
        :rtype: list
    """

    # Initialize some variables
    set_frmt = exp_set['plot_format']
    nmechs = len(set_ydata)
    if nmechs > 6:
        # Only 6 default colors defined at top of file...should fix this
        print('More than 6 mechanisms! This will cause plotting problems')

    # Build the empty figures and axes
    figs_axes = build_figs_axes(exp_set, set_frmt, conds_src, mech_opts_lst,
                                nmechs)

    # Loop over each mechanism and plot
    mech_xdata = set_xdata  # xdata is same for all mechs
    for mech_idx in range(nmechs):
        mech_ydata = set_ydata[mech_idx]
        mech_frmt = _mech_frmt(exp_set, set_frmt, conds_src, mech_idx=mech_idx)
        figs_axes = single_mech(mech_ydata, mech_xdata, figs_axes, mech_frmt,
                                exp_set, mech_idx=mech_idx)

    # Plot experimental data if present
    exp_ydata = exp_set['overall']['exp_ydata']
    exp_xdata = exp_set['overall']['exp_xdata']
    mech_frmt = _mech_frmt(exp_set, set_frmt, conds_src)
    figs_axes = single_mech(exp_ydata, exp_xdata, figs_axes, mech_frmt, exp_set)

    return figs_axes


def single_mech(mech_ydata, mech_xdata, figs_axes, mech_frmt, exp_set,
                mech_idx=None):
    """ Plots the results of a single mechanism on an existing set of figures

        :param mech_ydata: either the simulation results for a single mech or
            the experimental data
        :type mech_ydata: numpy.ndarray
        :param mech_xdata: the uniform x data used for all mechanisms; 1-D
        :type mech_xdata: numpy.ndarray
        :param figs_axes: figures to which plots are to be added
        :type figs_axes: list
        :param mech_frmt: formatting instructions for a single mech (or exps)
        :type mech_frmt: dict
        :return figs_axes: list of figures with plots; [(fig1, ax1), ...]
        :rtype: list
    """

    # Get info on how to organize the plots
    ngrps, nplts, plts_per_pg, pgs_per_grp = organize_set(
        mech_ydata, mech_frmt, exp_set)

    # Loop over each group of pages
    for grp_idx in range(ngrps):
        # Loop over pages in each group
        for pg_idx in range(pgs_per_grp):
            fig_idx = grp_idx * pgs_per_grp + pg_idx
            _, axs = figs_axes[fig_idx]
            # Loop over plots on each page
            for plt_idx_pg in range(plts_per_pg):
                plt_idx_grp = pg_idx * plts_per_pg + plt_idx_pg  # overall idx
                if plt_idx_grp < nplts:
                    plt_ydata = get_plt_ydata(mech_ydata, mech_frmt, grp_idx,
                                              plt_idx_grp, exp_set)
                    single_plot(plt_ydata, mech_xdata, axs[plt_idx_pg],
                                mech_frmt, plt_idx_pg, exp_set, mech_idx)

    return figs_axes


def single_plot(plt_ydata, mech_xdata, current_ax, mech_frmt, plt_idx_pg,
                exp_set, mech_idx):

    def _nlines(plt_ydata):
        """ Gets the number of lines on a single plot
        """
        ndims = np.ndim(plt_ydata)
        if ndims == 2:
            nlines = np.shape(plt_ydata)[0]
        else:  # ndims = 1
            nlines = 1

        return nlines

    # Load info; inefficient to load for every plot, but looks cleaner
    xlim = mech_frmt['xlim']
    ylim = mech_frmt['ylim']
    xscale = mech_frmt['xscale']
    yscale = mech_frmt['yscale']
    meas_type = exp_set['overall']['meas_type']

    # If on abs, flip order so total abs is first (i.e., the solid line)
    if meas_type == 'abs':
        plt_ydata = np.flip(plt_ydata, 0)

    # Loop over all lines and plot each
    nlines = _nlines(plt_ydata)
    labels = _labels(nlines, mech_idx, exp_set)
    for line_idx in range(nlines):
        single_line(plt_ydata, mech_xdata, line_idx, current_ax, mech_frmt,
                    labels)

    # Do some formatting on the entire plot
    if xlim is not None:
        current_ax.set_xlim(xlim)
    if ylim is not None:
        current_ax.set_ylim(ylim)
    current_ax.set_xscale(xscale)
    current_ax.set_yscale(yscale)
    if plt_idx_pg == 0 and nlines > 1:  # add legend on 1st plot if mult. lines
        current_ax.legend()


def single_line(plt_ydata, mech_xdata, line_idx, current_ax, mech_frmt, labels):
    """ Plots a single line on a plot

        Note: it's called "plt_ydata" because it might contain data for multiple
        lines (hence the line_idx input)
    """

    # Load some information
    xconv = mech_frmt['xconv']
    yconv = mech_frmt['yconv']
    color = mech_frmt['color']
    marker = mech_frmt['marker']
    order = mech_frmt['order']  # higher numbers go on top
    if xconv == 'inv':  # fix the case of inverse temperature
        mech_xdata = 1000 / mech_xdata
        xconv = 1

    # Get ydata for the current line
    ndims = np.ndim(plt_ydata)
    if ndims == 2:
        line_ydata = plt_ydata[line_idx]
    else:  # ndims = 1
        line_ydata = plt_ydata

    # Get linestyle based on marker formatting and line_idx
    if marker == '':  # if plotting a line
        linestyle = LINESTYLES[line_idx]
    else:  # if plotting points
        linestyle = ''

    # Get the line label and plot
    label = labels[line_idx]
    current_ax.plot(mech_xdata * xconv, line_ydata * yconv, label=label,
                    color=color, linestyle=linestyle, marker=marker,
                    zorder=order)


def _labels(nlines, mech_idx, exp_set):
    """ Gets the labels for all the lines on a single plot
    """

    meas_type = exp_set['overall']['meas_type']
    if nlines == 1:
        labels = [None]
    else:
        if meas_type == 'abs':
            if mech_idx is None:  # if on experimental data
                labels = ['Exp., total'] + [None] * (nlines - 1)
            else:
                active_spcs = copy.copy(exp_set['plot']['active_spc'])
                active_spcs.reverse()
                labels = ['Total'] + active_spcs
        else:
            print(f'Labels not implemented for meas_type {meas_type}')
            labels = [None] * nlines

    return labels


def get_plt_ydata(mech_ydata, mech_frmt, grp_idx, plt_idx_grp, exp_set):
    """ Get the ydata to plot for a single plot
    
        :param mech_ydata: 
        :param grp_idx:
        :param plt_idx_grp: 
        :param plt_idx_pg: 
        :return: 
    """

    def get_idxs(grp_idx, plt_idx_grp, exp_set, group_by):
        """ Gets indices for obtaining the ydata
        """
        meas_type = exp_set['overall']['meas_type']
        if meas_type == 'abs':
            nspcs = len(exp_set['plot']['active_spc'])
            if group_by == 'cond':
                cond_idx, wvlen_idx = grp_idx, plt_idx_grp
            else:  # 'target'
                cond_idx, wvlen_idx = plt_idx_grp, grp_idx
            start_idx = wvlen_idx * (nspcs + 1)  # +1 for total abs
            end_idx = start_idx + nspcs + 1
        else:
            if group_by == 'cond':
                cond_idx, start_idx = grp_idx, plt_idx_grp
            else:  # 'target'
                cond_idx, start_idx = plt_idx_grp, grp_idx
            end_idx = start_idx + 1

        return cond_idx, start_idx, end_idx

    group_by = mech_frmt['group_by']
    ndims = np.ndim(mech_ydata)
    if ndims == 3:
        cond_idx, start_idx, end_idx = get_idxs(grp_idx, plt_idx_grp, exp_set,
                                                group_by)
        plt_ydata = mech_ydata[cond_idx, start_idx:end_idx]
    else:  # ndims = 2
        plt_ydata = mech_ydata[:, plt_idx_grp]

    return plt_ydata


def organize_set(mech_ydata, mech_frmt, exp_set):
    """ Gets information on how to organize plots for the set
    """

    def _ngrps_nplts(mech_ydata, exp_set):
        """ Gets number of groups and number of plots per group
        """
        ndims = np.ndim(mech_ydata)
        group_by = mech_frmt['group_by']
        meas_type = exp_set['overall']['meas_type']
        # Depends on number of dimensions
        if ndims == 3:
            # Get the numbers of conditions and targets
            if meas_type == 'abs':
                nconds, _, _ = np.shape(mech_ydata)
                ntargs = len(exp_set['plot']['wavelength'])
            else:
                nconds, ntargs, _ = np.shape(mech_ydata)
            # Get the number of groups and plots
            if group_by == 'cond':
                ngrps, nplts = nconds, ntargs
            else:  # 'target'
                ngrps, nplts = ntargs, nconds  # flipped
        else:  # ndims = 2
            _, ntargs = np.shape(mech_ydata)
            ngrps, nplts = 1, ntargs  # all targets are treated as one group

        return ngrps, nplts

    ngrps, nplts = _ngrps_nplts(mech_ydata, exp_set)
    nrows, ncols = mech_frmt['rows_cols']
    plts_per_pg = nrows * ncols  # maximum number of plots per page
    pgs_per_grp = _pgs_per_grp(nplts, plts_per_pg)

    return ngrps, nplts, plts_per_pg, pgs_per_grp


def build_figs_axes(exp_set, set_frmt, conds_src, mech_opts_lst, nmechs):
    """ Initializes figures with empty axes

        :param exp_set: exp_set object
        :type exp_set: dict
        :param mech_names: mechanism nicknames
        :type mech_names: list
        :param set_frmt: plot options
        :type set_frmt: dict
        :param conds_src: the source of the conditions; 'plot' or 'exps'
        :type conds_src: str
        :return figs_axes: list of figures with plots [(fig1, ax1), ...]
        :rtype: list
    """

    def create_figs(grp_titles, plt_titles, xlabel, ylabel, mech_names):
        """ Create the figures/axes given the group and plot titles

            :param grp_titles: titles for each group of plots
            :type grp_titles: list
            :param plt_titles: titles for the plots within each group
            :type plt_titles: list
            :param xlabel: label for the x axis
            :type xlabel: str
            :param ylabel: label for the y axis
            :type ylabel: str
        """

        # Load/calculate various data
        nrows, ncols = set_frmt['rows_cols']
        plts_per_pg = nrows * ncols
        ngrps = len(grp_titles)
        plts_per_grp = len(plt_titles)
        pgs_per_grp = _pgs_per_grp(plts_per_grp, plts_per_pg)

        # Loop over each group and build the figures and axes
        figs_axes = []
        for grp_idx in range(ngrps):
            # Loop over each page within the group
            for pg_idx in range(pgs_per_grp):
                fig = plt.figure(figsize=(8.5, 11))
                axes = []
                # Loop over each plot on the page
                for plt_idx_pg in range(plts_per_pg):
                    plt_idx_grp = pg_idx * plts_per_pg + plt_idx_pg
                    if plt_idx_grp < plts_per_grp:
                        axis = fig.add_subplot(nrows, ncols, plt_idx_pg + 1)
                        plt_title = plt_titles[plt_idx_grp]
                        plt.title(plt_title, fontsize=10, loc='center', y=0.97)
                        plt.xticks(fontsize=8)
                        plt.yticks(fontsize=8)
                        plt.subplots_adjust(wspace=0.38, hspace=0.23)
                        axis.yaxis.set_major_formatter(Formatter('%0.2E'))
                        axes.append(axis)
                    if plt_idx_pg == 0:  # if first plot of page, add page title
                        title = grp_titles[grp_idx]
                        title += f'\n(pg. {pg_idx + 1} of {pgs_per_grp})'
                        fig.suptitle(title, y=0.99, fontsize=16)

                add_headers(exp_set, mech_names)
                add_footers(xlabel, ylabel)
                figs_axes.append([fig, axes])

        return figs_axes

    # Load some information
    group_by = set_frmt['group_by']
    xunit = set_frmt['xunit']
    yunit = set_frmt['yunit']

    # Get the mech_names from mech_opts_lst
    mech_names = util._mech_names(mech_opts_lst, nmechs)

    # Get the titles and axis labels
    cond_titles, xlabel, _ = util.get_cond_titles(exp_set, conds_src,
                                                  xunit=xunit)
    targ_titles, ylabel, _ = util.get_targ_titles(exp_set, yunit=yunit)

    # Set the titles according to the grouping method
    if group_by == 'cond':
        grp_titles = cond_titles
        plt_titles = targ_titles
    else:  # 'target'
        grp_titles = targ_titles
        plt_titles = cond_titles

    # Create the figures and axes
    figs_axes = create_figs(grp_titles, plt_titles, xlabel, ylabel, mech_names)

    return figs_axes


def add_headers(exp_set, mech_names):
    """ Adds header text to a figure
    """

    # Make some text describing the legends
    header_x_positions = [0.06, 0.37, 0.68]
    header_y_positions = [0.9, 0.92]
    for mech_idx, mech_name in enumerate(mech_names):
        header = f'{COLORS[mech_idx % len(COLORS)]} lines: {mech_name}'
        if mech_idx < 3:  # three mechs per row
            y_idx = 0
        else:
            y_idx = 1
        plt.figtext(header_x_positions[mech_idx % 3], header_y_positions[y_idx],
                    header, fontsize=12, color=COLORS[mech_idx % len(COLORS)])

    # Make some text describing the experimental set
    source = exp_set['overall']['source']
    description = exp_set['overall']['description']
    reac_type = exp_set['overall']['reac_type']
    meas_type = exp_set['overall']['meas_type']
    plt.figtext(0.01, 0.98, f'Source: {source}', fontsize=10)
    plt.figtext(0.01, 0.96, f'Description: {description}', fontsize=10)
    plt.figtext(0.77, 0.98, f'Reac. type: {REAC[reac_type]}', fontsize=10)
    plt.figtext(0.77, 0.96, f'Meas. type: {MEAS[meas_type]}', fontsize=10)


def add_footers(xlabel, ylabel):
    """ Adds footer text to a figure
    """

    footnote1 = f'Y-axis: {ylabel}\n'
    footnote2 = f'X-axis: {xlabel}\n'
    footnotes = footnote1 + footnote2
    plt.figtext(0.11, 0.06, footnotes, fontsize=10, va="top", ha="left")


def _mech_frmt(exp_set, set_frmt, conds_src, mech_idx=None):
    """ Gets plot formatting directions for one mech (or the experimental data)

        :param exp_set: exp_set object
        :type exp_set: dict
        :param set_frmt: formatting directions for entire set
        :type set_frmt: dict
        :param conds_src: the source of the conditions; 'plot' or 'exps'
        :type conds_src: str
        :param mech_idx: index of the current mechanism, or None if experiment
        :type mech_idx: int
        :return mech_frmt: formatting instructions for a single mech (or exps)
        :rtype: dict
    """

    def get_conv_factors(units, quant):
        """ Get the factor to convert a quantity from the internal units to the
            desired units. Note: Celsius and Fahrenheit are not allowed (this is
            enforced in the parser)
        """

        if units is not None:
            allowed_units = ALLOWED_UNITS[quant][0]
            conv_factors = ALLOWED_UNITS[quant][1]
            assert units in allowed_units, (
                f"'{units}' are not allowed units for the quantity '{quant}'")
            idx = allowed_units.index(units)
            conv_factor = 1 / conv_factors[idx]  # conv_factor is the inverse
        else:
            conv_factor = 1

        return conv_factor

    # Initialize the dict with some general information
    mech_frmt = {'rows_cols': set_frmt['rows_cols'],
                 'group_by': set_frmt['group_by'],
                 'xlim': set_frmt['xlim'],
                 'ylim': set_frmt['ylim'],
                 'xscale': set_frmt['xscale'],
                 'yscale': set_frmt['yscale'],
                 }

    # Get the conversion factors
    xunit = set_frmt['xunit']
    yunit = set_frmt['yunit']
    _, _, xquant = util.get_cond_titles(exp_set, conds_src)
    _, _, yquant = util.get_targ_titles(exp_set)
    mech_frmt['xconv'] = get_conv_factors(xunit, xquant)
    mech_frmt['yconv'] = get_conv_factors(yunit, yquant)
    if exp_set['overall']['meas_type'] in ('idt', 'half_life'):
        mech_frmt['xconv'] = 'inv'  # so that inverse temp can be plotted

    # Get color, marker, and order; depends on whether simulation or experiment
    exp_on_top = set_frmt['exp_on_top']
    if mech_idx is not None:  # if mech_idx exists, it's a simulation
        mech_frmt['color'] = COLORS[mech_idx % len(COLORS)]
        mech_frmt['marker'] = ''
        mech_frmt['order'] = mech_idx

    else:  # if mech_idx is None, it's an experiment
        mech_frmt['color'] = set_frmt['exp_color']
        # If indicated, plot points
        if set_frmt['plot_points']:
            mech_frmt['marker'] = '.'
        # Otherwise, plot lines
        else:
            mech_frmt['marker'] = ''
        # Put the experiment either in front or in back
        if exp_on_top:
            mech_frmt['order'] = 1e3  # bigger than any possible number of mechs
        else:
            mech_frmt['order'] = -1  # negative to go behind all

    return mech_frmt


def _pgs_per_grp(plts_per_grp, plts_per_pg):
    """ Calculates the number of pages per group
    """

    if plts_per_grp % plts_per_pg == 0:  # if perfectly divisible, just divide
        pgs_per_grp = int(plts_per_grp / plts_per_pg)
    else:  # otherwise, add one (since int rounds down)
        pgs_per_grp = int(plts_per_grp / plts_per_pg) + 1

    return pgs_per_grp
