#!/bin/bash

echo "Setting up Python environment"
VENVNAME="opentldr-env"

commandOutput=$(python3 -m venv ~/.virtualenvs/$VENVNAME)
if [[ $? -ne 0 ]]; then
    echo ""
    echo "Installing python-venv, you will be prompted for sudo password:"
    sudo apt install -y python3.12-venv
fi 

echo ""
echo "Createing a virtual environment:"
python3.12 -m venv ~/.virtualenvs/$VENVNAME

echo ""
echo "Activating the virtual environment and upgradeing pip"
source ~/.virtualenvs/$VENVNAME/bin/activate
python3 -m pip install --upgrade pip

echo ""
echo "Installing requirements packages:"
python3 -m pip install -r ./requirements.txt
python3 -m pip install -r ./User_Interface/requirements.txt
python3 -m pip install -r ./Collectors/requirements.txt

echo ""
echo "Adding venv to ipykernel for Jupyter:"
python3 -m pip install ipykernel
python3 -m ipykernel install --user --name=$VENVNAME

echo ""
echo "Creating .env file using default settings... *** You should edit these if needed"
cp ./DefaultDotEnv ./.env
cp ./User_Interface/DefaultDotEnv ./User_Interface/.env
cp ./Collectors/DefaultDotEnv ./Collectors/.env

if [ ! -f ./LLM_Models/mistral-7b-openorca.gguf2.Q4_0.gguf ]; then
    echo ""
    echo "Adding default ./LLM_Models for LLM... "
    mkdir ./LLM_Models

    echo ""
    echo "Downloading a GPT4ALL model into the ./models folder... may take a bit..."
    cd ./LLM_Models
    curl -O https://gpt4all.io/models/gguf/mistral-7b-openorca.gguf2.Q4_0.gguf
    cd ..
fi

echo ""
echo "*** You will need to set your Jupyter Kernel in each notebook to $VENVNAME"

echo "*** You will need to start the NEO4J server - see the script start_neo4j.sh"

echo "to set the virtual environment in this terminal run:"
echo "% source ~/.virtualenvs/$VENVNAME/bin/activate"
