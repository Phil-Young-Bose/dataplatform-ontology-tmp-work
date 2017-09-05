# GOAL
#   Idempotent script to "do everything" we need to build and run the browser

#
MY_PATH=$( cd $(dirname "$0") && pwd )

#./setup_google_cloud_sdk_for_python.sh
#./setup_local_schema.org.sh

${MY_PATH}/setup_local_grakn.sh
