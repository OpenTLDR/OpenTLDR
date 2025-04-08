# OpenTLDR Workflows

OpenTLDR is developed accross multiple source code repositories, this one "OpenTLDR" is intended to be the primary method that algorithm developers can use to explore the process, experiment with alternative ways to solve the problem, and evaluate them in an end-to-end manner. To facilitate this effort, the steps of the process are laid out in a series of Python Notebooks, each perfoming a specific piece of the process. It is important that they be executed in the expected way to ensure that they perform as designed. As such, it is useful to have a mechanism to document and automate the execution of any developer's version of an end-to-end process without human intervention and retarget that execution to various datasets. This is done using the Workflow.

## Specifying a Workflow

### A workflow as a Python data Structure
The default way to specify a workflow is as a python dictionary object, as is shown below:
<pre>
workflow = {
    "Output": "./READ_ONLY_OUTPUT",
    "Notebooks": [
        ["Step_0_Initialize.ipynb",{
            "message": "Successfully passed in parameters from Workflow.ipynb!",
            "data_repo_config": {'repo_type': 'files', 'path': './sample_data/reference'},
            }],
        ["Step_1_Ingest.ipynb", {
            "data_repo_config": {'repo_type': 'files', 'path': './sample_data/content'},
            }],
        ["Step_1a_MockUI.ipynb",{
            "data_repo_config": {'repo_type': 'files', 'path': './sample_data/request'},
            }],
        ["Step_2_Connect.ipynb",{
            "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "threshold_similarity": 0.6
            }],
        ["Step_3_Recommend.ipynb",{
            "recommendation_threshold": 0.6
        }],
        ["Step_4_Summarize.ipynb",{
            "llm_model_path": "./models/mistral-7b-openorca.Q4_0.gguf",
            "llm_prompt": "Given these facts: {knowledge} and the request: {request}. Concisely summarize this article: {content}"
            }],
        ["Step_5_Produce.ipynb",{}],
    ]}
</pre>

You can execute this workflow by instantiating the OpenTLDR Workflow object and calling the run() method, as follows:
<pre>
from opentldr import Workflow
my_workflow = Workflow(workflow)
my_workflow.run()
</pre>

In this format, it is also relatively easy to write code that changes parameters. For example, if you wished to run the workflow with a range of values for threshold similarity, you could loop over values and modify the workflow.
<pre>
from opentldr import Workflow
for parameter in [ 0.4, 0.5, 0.6, 0.7, 0.8 ]:

    # change the output directory so you keep all the run outputs
    workflow["Output"]="./OUTPUT_threshold_{p}".format(p=parameter)

    # update the parameter value used
    workflow["Notebooks"][3][1]["recommendation_threshold"]=parameter

    # run the workflow as specified
    my_workflow = Workflow(workflow)
    my_workflow.run()
</pre>

### Using a JSON file to specify the Workflow

Another way to specify the workflow is by creating a JSON file that contains the same structure as above, and reading in a workflow from JSON is performed like this:
<pre>
my_workflow = Workflow.from_file("./json_workflow.json")
</pre>

You can export the current specification from a Workflow to a JSON file so that it can be used at a later date or archived. This is useful when you want to ensure your process is repeatable because you can put the JSON file in version control and easily verify it is being used without modification.

<pre>
my_workflow.export_workflow("./exported_workflow.json")
</pre>

### Splitting up the Workflow

A third method for specifying a Workflow is to pass in the various parameters seperately. Here is an example of this:

<pre>
output_folder = "./READ_ONLY_OUTPUT"

notebook_order = [
    "Step_0_Initialize.ipynb",
    "Step_1_Ingest.ipynb",
    "Step_1a_MockUI.ipynb",
    "Step_2_Connect.ipynb",
    "Step_3_Recommend.ipynb",
    "Step_4_Summarize.ipynb",
    "Step_5_Produce.ipynb",
    "Step_6_Evaluate.ipynb"
    ]

variables_to_set={
    "message": "Successfully passed in parameters from variables_to_set_in Workflow.ipynb!",
    "data_repo_config": {'repo_type': 'files','path': './sample_data'}
    }

my_workflow = Workflow.from_vars(output_folder,notebook_order,variables_to_set)
my_workflow.run()  
</pre>

Note however, with the seperate method, ALL of the parameters are passed into each of the workflow notebooks. This may have some unexpected results. For example, the date repo here does not focus the importing to specific directories, so all the data may be re-loaded at multiple steps. Similarly, parameters with the same name in different notebooks will always be set to the same value.

The benefit of this approach is that it simplifies programaticallly generating new configurations, such as in the example below:

<pre>
for threshold in range(30,100,10):
    out_path=os.path.join(output_folder,"Threshold_{v}".format(v=threshold))
    variables_to_set["threshold_similarity"]=threshold/100.0
    Workflow.from_vars(out_path,notebook_order,variables_to_set).run()
</pre>
## Executing a Workflow

The workflow is executed by calling the Workflow.run() method. This intended to be a "hands-off" process. If any of the Notebooks crash during the running of the Workflow, you can view the version of the Notebook in the READ_ONLY_OUTPUT folder (or wherever you configured the Output path to be).

