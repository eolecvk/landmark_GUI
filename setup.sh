#!/bin/bash
sudo apt-get install python3-tk
python3 -m venv .venv --prompt fs
source .venv/bin/activate
pip install --upgrade pip
pip install pillow matplotlib natsort