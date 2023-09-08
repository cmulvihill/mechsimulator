import pandas as pd

# Allowed job_types and their required sheet types
ALLOWED_JOB_TYPES = {
    'plot': ('exp', 'mech'),
}

# Allowed sheet_types and their required headers
ALLOWED_SHEET_TYPES = {
    'exp':  ('exp_filenames', 'calc_types', 'x_srcs', 'cond_srcs'),
    'mech': ('mech_filenames', 'spc_filenames'),
}


def load_job(job_file, job_type):

    print(f"Reading job file '{job_file}'...")

    # Check that the job type is allowed and get the required sheet types
    assert job_type in ALLOWED_JOB_TYPES, (
        f"The job_type '{job_type}' is not allowed. Options are: "
        f"{ALLOWED_JOB_TYPES.keys()}")
    sheet_types = ALLOWED_JOB_TYPES[job_type]

    # Loop over each sheet and read it, storing in the job_dct
    job_dct = {'job_type': job_type}  # initialize with the job type
    #sheet_names = pd.ExcelFile(job_file).sheet_names
    sheet_names = pd.ExcelFile(job_file, engine='openpyxl').sheet_names
    for sheet_type in sheet_types:
        assert sheet_type in sheet_names, (
            f"In job file '{job_file}', sheet name '{sheet_type} missing. This "
            f"is required for job_type '{job_type}'")
        sheet_dct = read_sheet(job_file, sheet_type)
        job_dct.update(sheet_dct)

    return job_dct


def read_sheet(job_file, sheet_type):

    # Define required data and read Excel file
    reqd_data = ALLOWED_SHEET_TYPES[sheet_type]
    df = pd.read_excel(job_file, sheet_name=sheet_type, header=0,
                       engine='openpyxl')

    # Check that required data are present
    for reqd_datum in reqd_data:
        assert reqd_datum in df, (
            f"In job file '{job_file}', reqd datum '{reqd_datum}' missing from "
            f"sheet {sheet_type}.")

    # Initialize sheet_dct
    sheet_dct = {}
    if sheet_type == 'mech':  # if on a mechanism sheet, add kwarg_dct field
        sheet_dct['kwarg_dct'] = {}

    # Read each column and store values in the sheet_dct
    for col in df.columns:
        vals = list(df[col])
        if col in reqd_data:
            sheet_dct[col] = vals
        elif sheet_type == 'mech':
            sheet_dct['kwarg_dct'][col] = vals

    return sheet_dct
