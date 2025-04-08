#!/bin/bash

echo "Setting up Python environment"
VENVNAME="opentldr-collectors"

echo ""
echo "Createing a virtual environment:"
python3 -m venv ~/.virtualenvs/$VENVNAME

echo ""
echo "Activating the virtual environment and upgradeing pip"
source ~/.virtualenvs/$VENVNAME/bin/activate
python3 -m pip install --upgrade pip

echo ""
echo "Installing requirements packages:"
python3 -m pip install -r ./requirements.txt

echo ""
echo "Adding venv to ipykernel for Jupyter:"
echo ""
echo "Adding venv to ipykernel for Jupyter:"
python3 -m pip install ipykernel
python3 -m ipykernel install --user --name=$VENVNAME

echo ""
echo "Creating .env file using default settings... *** You should edit these if needed"
cp ./DefaultDotEnv ./.env

echo ""
echo "*** You will need to set your Jupyter Kernel in each notebook to $VENVNAME"

echo "to set the virtual environment in this terminal run:"
echo "% source ~/.virtualenvs/$VENVNAME/bin/activate"
