from os.path import join
from cantera import ck2cti

# Path names
READ_PATH = '../lib/mechs/ckin'  # where to look for Chemkin mechanism
WRITE_PATH = '../lib/mechs/'  # where to write Cantera mechanism

# Filename(s) (might not all be used)
MECH_FILENAME = '230810_comb_dummy.ckin'
THERMO_FILENAME = '230810_comb_dummy.therm'
TRAN_FILENAME = '230810_comb_dummy.tran'

# Get the output filename
OUT_FILENAME = MECH_FILENAME.split('.')
OUT_FILENAME[-1] = 'cti'  # note: do not include period!
OUT_FILENAME = '.'.join(OUT_FILENAME)

# Add paths to filenames
MECH_FILENAME = join(READ_PATH, MECH_FILENAME)
THERMO_FILENAME = join(READ_PATH, THERMO_FILENAME)
TRAN_FILENAME = join(READ_PATH, TRAN_FILENAME)
OUT_FILENAME = join(WRITE_PATH, OUT_FILENAME)


# Run converter
ck2cti.convertMech(MECH_FILENAME,
                   # thermoFile=THERMO_FILENAME,  # comment if unused
                   # transportFile=TRAN_FILENAME,  # comment if unused
                   permissive=True, outName=OUT_FILENAME)
