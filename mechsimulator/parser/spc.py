"""
Parses a spc.csv file containing species information to obtain a mech_spc_dct
"""

import csv
import copy
from rdkit import RDLogger
import rdkit.Chem as _rd_chem

ALLOWED_COLUMN_NAMES = (
    'name',
    'smiles',
    'inchi',
    'inchikey',
    'mult',
    'charge',
    'exc_flag',
    'sens'
)

# Prevents some weird valence error warnings
_LOGGER = RDLogger.logger()
_LOGGER.setLevel(RDLogger.ERROR)


def load_mech_spc_dct(spc_filename, quotechar=None):
    """ Obtains a single mech_spc_dct given a spc.csv filename

        :param spc_filename: filename of the spc.csv file to be read
        :type spc_filename: str
        :param quotechar: character used to optionally ignore commas; " or '
        :type quotechar: str
        :return mech_spc_dct: identifying information on species in a mech
        :rtype: dict {spc1: spc_dct1, spc2: ...}
    """

    with open(spc_filename, 'r') as file_obj:
        file_str = file_obj.read()

    mech_spc_dct = mech_spc_dct_str(file_str, quotechar=quotechar)

    return mech_spc_dct


def mech_spc_dct_str(file_str, quotechar=None):
    """ Obtains a single mech_spc_dct given a string parsed from a spc.csv file

        :param file_str: the string that was read directly from the .csv file
        :type file_str: str
        :param quotechar: the quotechar used to optionally ignore commas
        :type quotechar: str
        :return mech_spc_dct: identifying information on species in a mech
        :rtype: dict {spc1: spc_dct1, spc2: ...}
    """

    quotechar = quotechar or "'"

    # Check for incorrect quotechar usage
    if quotechar == '"':
        assert "'" not in file_str, (
            f'A quotechar input of double quotation marks was selected, but at '
            f'least one instance of a single quotation mark exists in the '
            f'csv file. Use only double quotation marks.')
    elif quotechar == "'":
        assert '"' not in file_str, (
            f'A quotechar input of single quotation marks was selected, but at '
            f'least one instance of a double quotation mark exists in the '
            f'csv file. Use only single quotation marks.')
    else:
        raise NotImplementedError(
            f'The quotechar {quotechar} is not allowed. Options are either '
            f'a single or double quotation mark.')

    # Split into lines
    lines = file_str.split('\n')
    if lines[-1] == '':
        del lines[-1]  # gets rid of the annoying last line that gets added

    # Build the mech_spc_dct line by line
    mech_spc_dct = {}
    for idx, line in enumerate(lines):
        if idx == 0:
            col_headers, num_cols = parse_first_line(line, quotechar=quotechar)
        else:
            cols = parse_line(line, idx, num_cols, quotechar=quotechar)
            spc_name, spc_dct = get_spc_dct(cols, col_headers)

            # Check that the species name was not already defined
            assert spc_name not in mech_spc_dct.keys(), (
                f'The species name {spc_name} appears in the csv file more than'
                f' once. The second time is on line {idx + 1}, {line}.')

            # Fill in the spc_dct and then add it to the mech_spc_dct
            spc_dct = fill_in_spc_dct(spc_dct)  # add some information
            mech_spc_dct[spc_name] = spc_dct

    return mech_spc_dct


def get_spc_dct(cols, col_headers):
    """ Reads the parsed contents of a single line and converts to a spc_dct

        :param cols: a list of the entries in the line
        :type cols: list
        :param col_headers: a list of the entries in the first line
        :type col_headers: list
        :return spc_name: the mechanism name for the species
        :rtype: str
        :return spc_dct: identifying information for a single species
        :rtype: dict
    """

    # Build the spc_dct for this species, column by column
    spc_dct = {}
    for idx, col in enumerate(cols):
        col_header = col_headers[idx]
        if col_header == 'name':
            spc_name = col
        # If charge or mult or exc_flag, convert to int if not empty
        elif col_header in ('charge', 'mult', 'exc_flag') and col != '':
            spc_dct[col_header] = int(col)
        else:
            spc_dct[col_header] = col

    return spc_name, spc_dct


def fill_in_spc_dct(spc_dct):
    """ Looks at various identifiers in a spc_dct and fills in missing values

        :param spc_dct: identifying information for a single species
        :type: dict
        :return filled_spc_dct: identifying information for a single species
            that may now be supplemented with some information that was missing
        :rtype: dict
    """

    filled_spc_dct = copy.deepcopy(spc_dct)

    # Add SMILES or InChI if missing
    if 'inchi' not in filled_spc_dct or filled_spc_dct['inchi'] == '':
        filled_spc_dct['inchi'] = to_inchi(from_smiles(
            filled_spc_dct['smiles']))

    elif 'smiles' not in filled_spc_dct:
        filled_spc_dct['smiles'] = to_smiles(from_inchi(
            filled_spc_dct['inchi']))

    # Add charge and exc_flag if missing; assume 0 for both
    if 'charge' not in filled_spc_dct or filled_spc_dct['charge'] == '':
        filled_spc_dct['charge'] = 0
    if 'exc_flag' not in filled_spc_dct or filled_spc_dct['exc_flag'] == '':
        filled_spc_dct['exc_flag'] = 0

    return filled_spc_dct


def parse_first_line(first_line, quotechar="'"):
    """ Parse the first line in the spc.csv file

        :param first_line: a string with the contents of the first line in the
            csv file
        :type first_line: str
        :param quotechar: the quotechar used to optionally ignore commas
        :type quotechar: str
        :return headers: a list of the entries in the first line
        :rtype: list
        :return num_cols: the number of columns indicated by the first line
        :rtype: int
    """

    # Remove the UTF encoding if present
    if '\ufeff' in first_line:
        first_line = first_line.replace('\ufeff', '')

    # Parse the line
    headers = next(csv.reader([first_line], quotechar=quotechar))
    num_cols = len(headers)

    # Check that all column names are allowed
    for col_header in headers:
        assert col_header in ALLOWED_COLUMN_NAMES, (
            f'The column header {col_header} is not allowed. Options are'
            f' {ALLOWED_COLUMN_NAMES}.')
    # Check that at least one of the required chemical identifiers was provided
    assert 'inchi' in headers or 'smiles' in headers, (
        "At least one of the following chemical identifiers must be included in"
        " the csv file header: 'inchi' or 'smiles'.")
    # Check that the multiplicity was provided
    assert 'mult' in headers, (
        "The multiplicity, 'mult', must be included in the csv file header.")
    # Check that the name was provided
    assert 'name' in headers, (
        "The species name, 'name', must be included in the csv file header.")

    return headers, num_cols


def parse_line(line, idx, num_cols, quotechar="'"):
    """ Parse a line in the spc.csv file (other than the first line)

        :param line: a string with the contents of a single line in the csv file
        :type line: str
        :param idx: the index of the line
        :type idx: int
        :param num_cols: the number of columns in the csv file
        :type num_cols: int
        :param quotechar: the quotechar used to optionally ignore commas
        :type quotechar: str
        :return cols: a list of the entries in the line
        :rtype: list
    """

    cols = next(csv.reader([line], quotechar=quotechar))
    assert len(cols) == num_cols, (
        f'Line {idx + 1}, {line}, has {len(cols)} columns. The first line '
        f'in the csv file indicates {num_cols} columns are needed.')

    return cols


def from_inchi(ich, print_debug=False):
    """ Generate an RDKit molecule object from an InChI string.

        :param ich: InChI string
        :type ich: str
        :param print_debug: control the printing of a debug message
        :type print_debug: bool
        :rtype: RDKit molecule object
    """

    rdm = _rd_chem.inchi.MolFromInchi(ich, treatWarningAsError=False)
    if rdm is None and print_debug:
        print('rdm fails for {} by returning {}'.format(ich, rdm))

    return rdm


def to_inchi(rdm, options='', with_aux_info=False):
    """ Generate an InChI string from an RDKit molecule object.

        :param rdm: molecule object
        :type rdm: RDKit molecule object
        :param options:
        :type options: str
        :param with_aux_info: include auxiliary information
        :type with_aux_info: bool
        :rtype: str
    """

    if with_aux_info:
        ret = _rd_chem.inchi.MolToInchiAndAuxInfo(rdm, options=options)
    else:
        ret = _rd_chem.inchi.MolToInchi(rdm, options=options)

    return ret


def from_smiles(smi, print_debug=False):
    """ Generate an RDKit molecule object from a SMILES string.

        :param smi: SMILES string
        :type smi: str
        :param print_debug: control the printing of a debug message
        :type print_debug: bool
        :rtype: RDKit molecule object
    """

    rdm = _rd_chem.MolFromSmiles(smi)
    if rdm is not None and print_debug:
        print('rdm fails for {} by returning {}'.format(smi, rdm))

    return rdm


def to_smiles(rdm):
    """ Generate a SMILES string from an RDKit molecule object.

        :param rdm: molecule object
        :type rdm: RDKit molecule object
        :rtype: str
    """
    return _rd_chem.MolToSmiles(rdm)
