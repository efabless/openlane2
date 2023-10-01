#!/bin/sh
set -e
python3 -m openlane --version
if [ "$?" != "0" ]; then
    echo "Failed to run 'python3 -m openlane --version'."
    exit -1
fi

command=run
if [ "$1" == "eject" ]; then
    command=eject
fi
python3 -m openlane.steps $command\
    --config ./config.json\
    --state-in ./state_in.json