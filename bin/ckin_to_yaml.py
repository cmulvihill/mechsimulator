from os.path import join
from cantera import ck2yaml

# Path names
READ_PATH = '../lib/mechs/ckin'  # where to look for Chemkin mechanism
WRITE_PATH = '../lib/mechs/'  # where to write Cantera mechanism

# Filename(s) (might not all be used)
MECH_FILENAME = 'think_v1.0_CRM.ckin'
THERMO_FILENAME = 'think_v1.0_CRM.therm'
TRAN_FILENAME = '230810_comb_dummy.tran'

# Get the output filename
OUT_FILENAME = MECH_FILENAME.split('.')
OUT_FILENAME[-1] = 'yaml'  # note: do not include period!
OUT_FILENAME = '.'.join(OUT_FILENAME)

# Add paths to filenames
MECH_FILENAME = join(READ_PATH, MECH_FILENAME)
THERMO_FILENAME = join(READ_PATH, THERMO_FILENAME)
TRAN_FILENAME = join(READ_PATH, TRAN_FILENAME)
OUT_FILENAME = join(WRITE_PATH, OUT_FILENAME)

# Run converter
ck2yaml.convert_mech(MECH_FILENAME,
                   thermo_file=THERMO_FILENAME,  # comment if unused
                   # transport_file=TRAN_FILENAME,  # comment if unused
                   permissive=True, 
                   out_name=OUT_FILENAME,
                    )
