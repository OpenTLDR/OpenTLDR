import os
import json

#
#   nbtweak
#
#   Tweaks the contents of a python notebook to support minimizing changes
#   in git repo and that people need to make in their own environments

start = "."
virtual_env = "opentldr-env"

def getAllNotebooks(current:str) -> list[str]:
    if os.path.exists(current) and os.access(current,os.R_OK):
        if os.path.isdir(current):
            list=[]
            for child in os.listdir(current):
                if child == "READ_ONLY_OUTPUT":
                    continue # skip things in this directory
                full_path=os.path.join(current, child)
                list.extend(getAllNotebooks(full_path))
            return list
        else:
            if current.endswith(".ipynb") and os.access(current,os.W_OK):
                return [current]
            else:
                return []
    else:
        if not os.path.exists(current):
            print("Doesn't exist: {name}.".format(name=current))
        
        if not os.access(current,os.R_OK):
            print("Cannot read: {name}.".format(name=current))
        return []    

for nb_path in getAllNotebooks(start):
    data=dict()

    print("Tweaking: {}".format(nb_path))

    # read notbooks file into json dict
    with open(nb_path, "r") as nb:
        data = json.load(nb)

    # setting the environment
    data["metadata"]["kernelspec"]["display_name"]= virtual_env

    # clearing the outputs
    for cell in data["cells"]:
        if 'outputs' in cell.keys():
            cell['outputs'] = []
        if 'execution_count' in cell.keys():
            cell['execution_count'] = None

    # write the notebook file back out
    with open(nb_path, "w") as nb:
        nb.write(json.dumps(data, indent=4))