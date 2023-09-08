import numpy as np
import matplotlib.pyplot as plt
from mechsimulator.plotter import outcome
from mechsimulator.plotter import sens
from mechsimulator.plotter import pathways
from mechsimulator.plotter import util
from mechsimulator import simulator
from mechsimulator import parser
from mechsimulator import writer

# NOTE: should add this to default sim_opts! Of course, is it really a sim_opt?
NRXNS = 25  # used for plotting of sensitivity and ROP


def mult_sets_filenames(exp_filenames, mech_filenames, spc_csv_filenames,
                        calc_types, x_srcs, cond_srcs, headers=True,
                        **kwargs):

    # Load objects by parsing files
    exp_sets = parser.main.mult_files(exp_filenames, 'exp')
    gases = parser.main.mult_files(mech_filenames, 'mech')
    mech_spc_dcts = parser.main.mult_files(spc_csv_filenames, 'spc')

    # Create the mech options list by reading any optional keywords
    # mech_opts_lst = simulator.util._mech_opts_lst(exp_sets[0], gases, kwargs)
    mech_opts_lst = None  # filler; will delete this entire function eventually, I think

    # Pass the objects to the mult_sets function
    figs_axes = mult_sets(exp_sets, gases, mech_spc_dcts, calc_types, x_srcs,
                          cond_srcs, mech_opts_lst=mech_opts_lst,
                          headers=headers)

    return figs_axes


def mult_sets(exp_sets, gases, mech_spc_dcts, calc_types, x_srcs,
              cond_srcs, mech_opts_lst=None, headers=True):
    """ Plots any number of sets (against any number of mechanisms)

        :param exp_sets:
        :param gases:
        :param mech_spc_dcts:
        :param calc_types:
        :param x_srcs:
        :param cond_srcs:
        :param mech_opts_lst:
        :return:
    """

    # Initialize figure list
    figs_axes = _header_pgs(exp_sets, gases, calc_types, x_srcs,
                            cond_srcs, mech_opts_lst=mech_opts_lst,
                            headers=headers)
    # Loop over each experimental set
    for idx, exp_set in enumerate(exp_sets):
        set_figs_axes = single_set(
            exp_set, gases, mech_spc_dcts, calc_types[idx], x_srcs[idx],
            cond_srcs[idx], mech_opts_lst=mech_opts_lst)
        figs_axes.extend(set_figs_axes)

    return figs_axes


def single_set(exp_set, gases, mech_spc_dcts, calc_type, x_src,
               cond_src, mech_opts_lst=None):
    """ Plots a single set (i.e., with any number of mechanisms)

        :param exp_set:
        :param gases:
        :param mech_spc_dcts:
        :param calc_type:
        :param x_src:
        :param cond_src:
        :param mech_opts_lst:
        :return:
    """

    if calc_type == 'outcome':
        # Calculate the simulation data
        set_ydata, set_xdata = simulator.main.single_set(
            exp_set, gases, mech_spc_dcts, 'outcome', x_src, cond_src,
            mech_opts_lst=mech_opts_lst)
        # Plot the data
        figs_axes = outcome.single_set(set_ydata, set_xdata, exp_set,
                                       cond_src, mech_opts_lst=mech_opts_lst)
        # Send the data to the writer
        if exp_set['overall']['meas_type'] in parser.exp_checker.POINT_MEAS_TYPES:
            writer.sim_data.write_mech_results(exp_set, set_ydata)
        else:
            writer.sim_data.write_mech_results_time(exp_set, set_ydata, set_xdata)

    elif calc_type == 'sens':
        # Calculate the sensitivity coefficients
        set_sens, set_xdata = simulator.main.single_set(
            exp_set, gases, mech_spc_dcts, 'sens', x_src, cond_src,
            mech_opts_lst=mech_opts_lst)
        # Sort the sensitivity coefficients
        sorted_set_sens, sorted_set_rxns = simulator.sort_sens.sort_single_set(
            set_sens, gases)
        # Remove endpoints if a JSR; super hacky :(
        if exp_set['overall']['reac_type'] == 'jsr':
            sorted_set_sens[:, :, 0, :] = np.nan
            sorted_set_sens[:, :, -1, :] = np.nan
        # Calculate the reference results (having to do this twice; once inside
        # sens and once here. Could do once and then pass to the sens code)
        set_ref_results, _ = simulator.main.single_set(
            exp_set, gases, mech_spc_dcts, 'outcome', x_src, cond_src,
            mech_opts_lst=mech_opts_lst)
        # Plot the data
        figs_axes = sens.single_set(sorted_set_sens[:, :NRXNS],
                                    set_xdata,
                                    sorted_set_rxns[:, :NRXNS],
                                    set_ref_results, exp_set, cond_src)
        # Send the data to the writer
        if exp_set['overall']['meas_type'] in ('idt',):
            targs = exp_set['plot']['idt_targ'][0]
        else:
            targs = exp_set['spc'].keys()
        # targs = ['pressure',]
        writer.new_sens.mult_mechs(sorted_set_sens, sorted_set_rxns, targs,
                                   set_xdata, set_ref_results)

    elif calc_type == 'pathways':
        # Obtain the end states of each simulation; has shape (nmechs, nconds)
        set_end_tpx, set_xdata = simulator.main.single_set(
            exp_set, gases, mech_spc_dcts, 'pathways', x_src, cond_src,
            mech_opts_lst=mech_opts_lst)
        figs_axes = pathways.single_set(
            set_end_tpx, set_xdata, exp_set, cond_src, gases)
    else:
        raise NotImplementedError(f"calc_type {calc_type} not implemented!")

    return figs_axes


def _header_pgs(exp_sets, gases, calc_types, x_srcs, cond_srcs,
               mech_opts_lst=None, vspace=0.04, title_offset=0.1,
               start_offset=0.2, headers=True):
    """ Creates header pages

    :param exp_sets:
    :param gases:
    :param calc_types:
    :param x_srcs:
    :param cond_srcs:
    :param mech_opts_lst:
    :param vspace:
    :param title_offset:
    :param start_offset:
    :return:
    """

    if headers:
        set_header = _set_header(exp_sets, calc_types, x_srcs, cond_srcs,
                                 vspace, title_offset, start_offset)
        mech_header = _mech_header(gases, vspace, title_offset, start_offset,
                                   mech_opts_lst=mech_opts_lst)
        header_pgs = set_header + mech_header
    else:
        header_pgs = []

    return header_pgs


def _mech_header(gases, vspace, title_offset, start_offset, mech_opts_lst=None):

    # Load/set some information
    nlines = len(gases)  # number of lines is the number of mechs
    npgs = int(nlines * vspace / (1 - start_offset) + 1)  # +1 b/c rounding down
    lines_per_pg = int((1 - start_offset) / vspace - 1)  # -1 for header line
    mech_names = util._mech_names(mech_opts_lst, nlines)
    col_posns = (0.1, 0.5)
    col_names = ('Mech. nickname', 'Mech. filename')

    # Loop over each page
    figs_axes = []
    for pg_idx in range(npgs):
        fig = plt.figure(figsize=(8.5, 11))
        # Write the page title and column headers
        pg_title = f'Mechanism information (pg. {pg_idx + 1} of {npgs})'
        plt.figtext(0.5, (1 - title_offset), pg_title, fontsize=16, ha='center')
        for col_idx, col_name in enumerate(col_names):
            col_posn = col_posns[col_idx]
            plt.figtext(col_posn, (1 - start_offset), col_name, fontsize=14)
        # Write each line in the information section
        for line_idx_pg in range(lines_per_pg):
            line_idx_ovrll = pg_idx * lines_per_pg + line_idx_pg  # overall idx
            if line_idx_ovrll < nlines:
                mech_name = mech_names[line_idx_ovrll]
                filename = gases[line_idx_ovrll].name
                # Note: the +1 is to account for the column header line
                line_vloc = 1 - (start_offset + (line_idx_pg + 1) * vspace)
                plt.figtext(col_posns[0], line_vloc, mech_name, fontsize=12)
                plt.figtext(col_posns[1], line_vloc, filename, fontsize=12)
        # Store the current page, putting None as the axis
        figs_axes.append((fig, None))

    return figs_axes


def _set_header(exp_sets, calc_types, x_srcs, cond_srcs, vspace,
                title_offset, start_offset):

    # Load/set some information
    nlines = len(exp_sets)  # number of lines is the number of exp_sets
    npgs = int(nlines * vspace / (1 - start_offset) + 1)  # +1 b/c rounding down
    lines_per_pg = int((1 - start_offset) / vspace - 1)  # -1 for header line
    col_posns = (0.03, 0.25, 0.5, 0.65, 0.8)
    col_names = ('Source', 'Description', 'Calc. type', 'X source',
                 'Cond. source',)

    # Loop over each page
    figs_axes = []
    for pg_idx in range(npgs):
        fig = plt.figure(figsize=(8.5, 11))
        # Write the page title and column headers
        pg_title = f'Experiment information (pg. {pg_idx + 1} of {npgs})'
        plt.figtext(0.5, (1 - title_offset), pg_title, fontsize=16, ha='center')
        for col_idx, col_name in enumerate(col_names):
            col_posn = col_posns[col_idx]
            plt.figtext(col_posn, (1 - start_offset), col_name, fontsize=14)
        # Write each line in the information section
        for line_idx_pg in range(lines_per_pg):
            line_idx_ovrll = pg_idx * lines_per_pg + line_idx_pg  # overall idx
            if line_idx_ovrll < nlines:
                exp_set = exp_sets[line_idx_ovrll]
                source = exp_set['overall']['source']
                description = exp_set['overall']['description']
                calc_type = calc_types[line_idx_ovrll]
                x_src = x_srcs[line_idx_ovrll]
                cond_src = cond_srcs[line_idx_ovrll]
                # Note: the +1 is to account for the column header line
                line_vloc = 1 - (start_offset + (line_idx_pg + 1) * vspace)
                plt.figtext(col_posns[0], line_vloc, source, fontsize=12)
                plt.figtext(col_posns[1], line_vloc, description, fontsize=12)
                plt.figtext(col_posns[2], line_vloc, calc_type, fontsize=12)
                plt.figtext(col_posns[3], line_vloc, x_src, fontsize=12)
                plt.figtext(col_posns[4], line_vloc, cond_src, fontsize=12)
        # Store the current page, putting None as the axis
        figs_axes.append((fig, None))

    return figs_axes
