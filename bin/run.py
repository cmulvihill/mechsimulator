""" Runs one or more job files

    Example: python run.py jobfile1 jobfile2 ...
"""

import sys
from mechsimulator import runner

assert len(sys.argv) > 1, 'At least one input must be given!'

JOB_FILES = sys.argv[1:]
runner.main.run_jobs(JOB_FILES)
