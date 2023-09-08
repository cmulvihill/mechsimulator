import os
import cantera as ct
from PyPDF2 import PdfFileMerger, PdfFileReader
from mechsimulator.plotter import util


def single_set(set_end_tpx, set_xdata, exp_set, conds_source, gases,
               mech_names=None):

    element = 'C'
    cond_titles, xlabel, xquant = util.get_cond_titles(exp_set, conds_source)
    print(cond_titles)

    # Loop over each mechanism and plot
    mech_xdata = set_xdata  # xdata is same for all mechs in set
    for mech_idx, gas in enumerate(gases):
        mech_end_tpx = set_end_tpx[mech_idx]
        single_mech(mech_end_tpx, mech_xdata, gas, element, mech_idx)

    return []


def single_mech(mech_end_tpx, mech_xdata, gas, element, mech_idx):

    nconds = len(mech_end_tpx)

    # Create a separate PDF for each condition
    for cond_idx in range(nconds):
        end_tpx = mech_end_tpx[cond_idx]
        cond_x = mech_xdata[cond_idx]
        single_cond(end_tpx, cond_x, gas, element, cond_idx)

    # Collate all the PDFs
    merged_obj = PdfFileMerger()
    merged_filename = _temp_pdf_name(mech_idx, 'mech')
    for cond_idx in range(nconds):
        merged_obj.append(PdfFileReader(_temp_pdf_name(cond_idx, 'cond')))
    merged_obj.write(merged_filename)


def single_cond(end_tpx, cond_x, gas, element, cond_idx):
    """ Plots the pathway diagram for a single condition (i.e., a single page)

        :param end_tpx:
        :param cond_x:
        :param gas:
        :param element:
        :param cond_idx:
        :return:
    """

    # Set thermodynamic state and generate the pathways diagram
    gas.TPX = end_tpx
    diagram = ct.ReactionPathDiagram(gas, element)

    # Do some formatting
    diagram.show_details = True
    diagram.font = 'CMU Serif Roman'
    diagram.threshold = 0.001
    diagram.dot_options = 'node[fontsize=20,shape="box"]'
    diagram.title = (f'Reaction path diagram following {element}\n'
                     f'Temperature: {cond_x} K'
                     # f'Time: {end_time_s * 1000} ms '
                     )
    diagram.scale = -1  # -1 normalizes, while 1 leaves raw values

    # Write temporary files; will be written to calling script's directory
    dot_filename = 'temp_dotfile.dot'
    pdf_filename = _temp_pdf_name(cond_idx, 'cond')
    diagram.write_dot(dot_filename)
    os.system('dot {0} -Gdpi=300 -Tpdf -o{1}'.format(dot_filename,
                                                     pdf_filename))


def _temp_pdf_name(idx, type):
    return f'temp_pdf_{type}_{idx}.pdf'
