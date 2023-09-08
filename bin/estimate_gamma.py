"""
This script is for estimating the specific heat ratio (i.e., gamma) at
specific conditions. This is useful for converting RCM pressure profiles to
volume profiles
"""

import os
import cantera as ct


# ----------------------------------- INPUTS -----------------------------------

CTI_FNAME = 'combined.yaml'
MECH_PATH = '../lib/mechs'
TEMP = 750  # K
PRESSURE = 20  # atm
MIX = {'C4-808zqE': 0.03135, 'O2': 0.2038, 'N2': 0.76485}  # {spc: mole_frac, ...}


# ------------------------------------ RUN -------------------------------------

# Load solution object
FULL_FNAME = os.path.join(MECH_PATH, CTI_FNAME)
GAS = ct.Solution(FULL_FNAME)
GAS.TPX = TEMP, PRESSURE, MIX

# Get gamma
GAMMA = GAS.cp_mass / GAS.cv_mass
print(f'gamma: {GAMMA:.3f}')
