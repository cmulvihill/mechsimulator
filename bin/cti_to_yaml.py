import inspect
from os.path import join
from cantera import cti2yaml

# Path names
READ_PATH = '../lib/mechs/'  # where to look for .cti mechanism
WRITE_PATH = '../lib/mechs/'  # where to write .yaml mechanism

# Filename(s) (might not all be used)
MECH_FILENAME = 'mulvihill_n2o_burke.cti'

# Get the output filename
OUT_FILENAME = MECH_FILENAME.split('.')
OUT_FILENAME[-1] = 'yaml'  # note: do not include period!
OUT_FILENAME = '.'.join(OUT_FILENAME)

# Add paths to filenames
MECH_FILENAME = join(READ_PATH, MECH_FILENAME)
OUT_FILENAME = join(WRITE_PATH, OUT_FILENAME)

# Run converter
cti2yaml.convert(MECH_FILENAME,
                   #permissive=True, 
                   #out_name=OUT_FILENAME,
                    )
