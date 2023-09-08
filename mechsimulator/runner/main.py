from mechsimulator.runner import util
from mechsimulator import parser
from mechsimulator import plotter

JOB_PATH = '../lib/jobs'
EXP_PATH = '../lib/exps'
MECH_PATH = '../lib/mechs'
SPC_PATH = '../lib/mechs'
OUT_PATH = '../lib/results'


def run_jobs(job_files, job_path=None):
    """ Runs multiple jobs

        :param job_files: list of job file names
        :type job_files: list [str]
        :param job_path: path where job files are located
        :type job_path: str
    """

    for job_file in job_files:
        run_job(job_file, job_path=job_path)


def run_job(job_file, job_path=None):
    """ Runs a single job

        :param job_file: job file name
        :type job_file: str
        :param job_path: path where job file is located
        :type job_path: str
    """

    job_path = job_path or JOB_PATH
    job_dct = parser.main.single_file(job_path, job_file, 'job')
    job_type = job_dct['job_type']

    # Not sure how other job types will work...
    if job_type == 'plot':
        # Get filenames and other info from the job_dct
        exp_filenames = job_dct['exp_filenames']
        mech_filenames = job_dct['mech_filenames']
        spc_filenames = job_dct['spc_filenames']
        calc_types = job_dct['calc_types']
        x_srcs = job_dct['x_srcs']
        cond_srcs = job_dct['cond_srcs']
        # Load objects using the filenames
        exp_sets = parser.main.mult_files(EXP_PATH, exp_filenames, 'exp')
        gases = parser.main.mult_files(MECH_PATH, mech_filenames, 'mech')
        mech_spc_dcts = parser.main.mult_files(SPC_PATH, spc_filenames, 'spc')
        util.check_inputs(job_dct, exp_sets)  # run some checks
        # Load the mech_opts_lst
        mech_opts_lst = util._mech_opts_lst(exp_sets[0], gases,
                                            job_dct['kwarg_dct'])
        # Run the plotter code
        figs_axes = plotter.main.mult_sets(exp_sets, gases, mech_spc_dcts,
                                           calc_types, x_srcs, cond_srcs,
                                           mech_opts_lst=mech_opts_lst)
        plotter.util.build_pdf(figs_axes)
    else:
        raise NotImplementedError(f"job_type {job_type}")
