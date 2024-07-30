# OpenTLDR Live Workflow
There are three modes in which the OpenTLDR Playground can be run:
- Interactive Notebooks: This mode is intended for researchers modifying the analytic workflow
- Workflows: You can create a wide range of workflows in which to run the analytics
- Live: The workflow can be run iteratively every day to automatically produce TLDRs

**MOST users will not need to run in the Live mode, but the scripts are provided to do this if needed.**

## live_run_workflow.sh
This is a shell script that starts the live_workflow.py and logs the output.
Note that by default this will expect to use the Python Virtual Environment created in setup.sh and an S3 bucket.
The output is sent to stdout and to a log-yourdatehere.txt file.

## live_workflow.py
This is a Python script that sets up and runs a daily workflow. This is an example of using the workflow that is very similar to that in Workflow.ipynb with a few exceptions:
- Today: this script defaults to loading data labeled with the date, which is either the real world date (by default) or one of the dates for which the sample_data covers (which are set betweeen 2000-01-01 and 2000-01-08 to make them easy to use).
- Data: this script checks if there is an S3 Bucket configured, if so it will use that, otherwise it fails over to using the local sample_data/sim_live directory.
- Cleaning: normally, Step0_Initialize would delete the entire KG each time (i.e., clean_policy = "fresh") but when running iteratively daily, you only want to use a  clean_policy = "live" that will clear out the previous content and transient workflow objects, while keeping the existing Requests and TLDR data (note these are the what the OpenTLDR - UserInterface depends on).

## sample_data/sim_live
These are the same files as in the default sample_data folder, except organized by four dates for testing a live workflow.
Note, if you use the live_workflow.py without modification it defaults to the real "today" - if you want to use these files, you want to uncomment out one of the dates that matches the contents of this directory (or which ever data repo you are using).

## READ_ONLY_OUTPUT / {date_here}
The Live workflow uses the same OpenTLDR Playground Notebooks as the normal execution. However, this workflow is configured to copy the output notebooks to a dated directory so that they do not overwrite each other. Please remember that these are intended to be READ ONLY - changes to these do not propagate back to the original notebooks and will be lost the next time the same workflow is executed.