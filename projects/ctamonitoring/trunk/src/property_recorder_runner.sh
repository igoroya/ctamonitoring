#!/bin/bash

#
# Igor Oya, DESY Zeuthen
# Starts the standalone property recorder as a singleton in the machine
#
# created: 08.12.2015
#
# If you have trouble to start the script and you are sure there is no other standalone_recorder.py process running
# please remove the directory /tmp/property_recorder.lock


#####################
#  Configuration
#
# Standalone recorder location 
export recorder_script=${INTROOT}/lib/python/site-packages/ctamonitoring/property_recorder/standalone_recorder.py
#Configuration parameters
#Check 'python standalone_recorder.py -h' for more options and further details

export default_timer_trigger='60'
export backend_type='MONGODB'
export backend_config="{'database':'ctamonitoring'}"
#####################


# Make the process a singleton in the system
if ! mkdir /tmp/property_recorder.lock 2>/dev/null; then
    echo "The standalone property recorder is already running, exiting." >&2
    exit 1
fi



python $recorder_script -v --default_timer_trigger ${default_timer_trigger}  --backend_type ${backend_type} --backend_config ${backend_config}


rmdir /tmp/property_recorder.lock
