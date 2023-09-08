"""
Parses a Cantera-formatted .cti file to obtain a Cantera Solution object
"""

import cantera as ct


def load_solution_obj(mech_filename):
    """ Obtains a single Cantera Solution object given a Cantera .cti filename

        :param mech_filename: .cti filename
        :type mech_filename: str
        :return mech: Cantera Solution object describing a mixture/mechanism
        :rtype: cantera.Solution
    """

    print('mech_filename: ', mech_filename)
    mech = ct.Solution(mech_filename)
    mech.name = mech_filename  # stores filename in the Solution object

    return mech
