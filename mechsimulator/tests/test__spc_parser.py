import os
from mechsimulator import parser

PATH = os.path.dirname(os.path.realpath(__file__))
DAT_PATH = os.path.join(PATH, 'data')


def test_Tran():
    filename = 'Danilack_species.csv'
    filepath = os.path.join(DAT_PATH, filename)
    mech_spc_dct = spc.mech_spc_dct_from_filename(filepath)
    print(mech_spc_dct)


def test_from_filename():
    filename = 'species_0.csv'
    filepath = os.path.join(DAT_PATH, filename)
    mech_spc_dct = spc.mech_spc_dct_from_filename(filepath)


def test_aramco():

    filename = 'aramco3.csv'
    filepath = os.path.join(DAT_PATH, filename)
    mech_spc_dct = parser.main.mult_files([filepath], 'spc', {'quotechar': "'"})


if __name__ == '__main__':
    # test_Tran()
    # test_from_filename()
    test_aramco()


# Note: this currently returns some unknown error:
# ERROR: Unrecognized bond type: 0

# I think this must be from some rdkit thing. If I only leave the first species,
# I get no such error. Need to add some exceptions to catch rdkit errors.
