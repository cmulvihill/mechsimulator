import pandas as pd
import yaml

# Allowed job_types and their required sheet types
ALLOWED_JOB_TYPES = {
    'plot': ('exp', 'mech'),
}

# Allowed sheet_types and their required headers
ALLOWED_SHEET_TYPES = {
    'exp':  ('exp_filenames', 'calc_types', 'x_srcs', 'cond_srcs'),
    'mech': ('mech_filenames', 'spc_filenames'),
}


# Uncomment to use Yaml
def read_sheet(job_data, sheet_type):
    # Define required data for the given sheet type
    reqd_data = ALLOWED_SHEET_TYPES[sheet_type]

    # Use job_file to get the relevant section (it's actually the YAML data)
    sheet_data = job_data.get(sheet_type, {})  # Gets everything for the sheet_type (exp or mech) out of the yaml file into sheet_data

    # Check that required data are present
    for reqd_datum in reqd_data:
        assert reqd_datum in sheet_data, (
            f"In job data, required datum '{reqd_datum}' is missing from "
            f"section {sheet_type}."
        )

    # Initialize sheet_dct
    sheet_dct = {}
    if sheet_type == 'mech':            # if on a mechanism sheet, add kwarg_dct field
        sheet_dct['kwarg_dct'] = {}     # Stores optional fields

    # Store values in the sheet_dct
    for key, vals in sheet_data.items():        # Loops through each key, value pair in sheet_data
        if key in reqd_data:
            sheet_dct[key] = vals               # Add required fields
        elif sheet_type == 'mech':
            sheet_dct['kwarg_dct'][key] = vals

    return sheet_dct


# Uncomment for Yaml
def load_job(job_file, job_type):

    print(f"Reading job file '{job_file}'...")

    # Check that the job type is allowed and get the required sheet types
    assert job_type in ALLOWED_JOB_TYPES, (
        f"The job_type '{job_type}' is not allowed. Options are: "
        f"{ALLOWED_JOB_TYPES.keys()}")
    sheet_types = ALLOWED_JOB_TYPES[job_type]

    # Load the YAML file
    with open(job_file, 'r') as f:     # Opens the yaml file in read mode and ensures that it is closed properly
        job_data = yaml.safe_load(f)   # Puts everything from the file into a dictionary using only simple (safe) data structures that a yaml file would typically contain

    job_dct = {'job_type': job_type}  # Initialize with the job type

    # Loop over each sheet type and read it, storing in job_dct
    for sheet_type in sheet_types:
        assert sheet_type in job_data, ( 
            f"In job file '{job_file}', sheet '{sheet_type}' is missing. This "
            f"is required for job_type '{job_type}'")
        sheet_dct = read_sheet(job_data, sheet_type) 
        job_dct.update(sheet_dct)

    return job_dct