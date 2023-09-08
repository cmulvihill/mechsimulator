from os.path import join
from mechsimulator.parser import exp
from mechsimulator.parser import spc
from mechsimulator.parser import mech
from mechsimulator.parser import job
# could add correlation for optimization


def mult_files(path, filenames, filetype, opts=None):
    """ Parses multiple files of the same type

        :param path: path to directory containing files
        :type path: str
        :param filenames: filenames
        :type: list
        :param filetype: file type (e.g., 'exp')
        :type filetype: str
        :param opts: options for parsing
        :type opts: dict
        :return objs: a list of objects of the type indicated by filetype
        :rtype: list
    """

    objs = []
    for filename in filenames:
        obj = single_file(path, filename, filetype, opts=opts)
        objs.append(obj)

    return objs


def single_file(path, filename, filetype, opts=None):
    """ Loads a single object given a single filename

        :param filename: filename
        :type filename: str
        :param filetype: file type
        :type filetype: str
        :param opts: options for parsing
        :type opts: dict
        :return obj: object created from parsing the file
    """

    opts = opts or {}  # set to empty dict if None
    filename = join(path, filename)

    if filetype == 'exp':
        obj = exp.load_exp_set(filename)
    elif filetype == 'spc':
        quotechar = opts.get('quotechar')
        obj = spc.load_mech_spc_dct(filename, quotechar=quotechar)
    elif filetype == 'mech':
        obj = mech.load_solution_obj(filename)
    elif filetype == 'job':
        obj = job.load_job(filename, 'plot')
    else:
        raise NotImplementedError(f"filetype '{filetype}' is not allowed")

    return obj
