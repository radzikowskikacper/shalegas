#!/bin/bash

source $1/bin/activate
$1/bin/pip install -r pip_prod.requirements
deactivate
