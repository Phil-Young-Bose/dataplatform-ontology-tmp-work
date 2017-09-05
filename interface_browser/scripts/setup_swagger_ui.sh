#!/bin/bash

# GOAL
#  Install and run SWAGGER UI
#
# RESOURCES
#   https://swagger.io/docs/swagger-tools/#swagger-ui-documentation-29

error_handler () {
    RC=$?
    echo "Error $RC, at $BASH_COMMAND, line ${BASH_LINENO[0]}"
    exit $RC
}
trap error_handler ERR

# Make the dir and return its absolute path
make_dir() {
    mkdir -p $1
    cd $1
    pwd
}

kill_proc(){
    PID=$(ps -o pid,cmd -eax | grep -v grep | grep "${1}" | head -1 | perl -pe 's/^(.*?) .*/$1/')
    if [[ $PID ]]; then
	echo "KILLING: PID=$PID PROC'=${1}'"
	kill -15 $PID
    fi
}

################################################################################

setup() {
    # Set paths relative to this script
    MY_PATH=$( cd $(dirname "$0") && pwd )

    PROJECT_PATH=$( make_dir "${MY_PATH}/../.." )    
    SWAGGER_PATH=$( make_dir "${PROJECT_PATH}/tmp/swagger" )

    PASSPORT_JAVA_DOC_PATH="/repos/bose-apis/generated/docs/passport_sdk/apidocs"
    PASSPORT_SWAGGER_DOC_FILE="/repos/bose-apis/generated/passport_full.json"
}

################################################################################

expose_passport_swagger_docs() {
    PASSPORT_SWAGGER_DOC_DIR=$(dirname ${PASSPORT_SWAGGER_DOC_FILE})
    #PASSPORT_SWAGGER_DOC_REL_FILE=basename ${PASSPORT_SWAGGER_DOC_FILE}    
    
    PORT="9001"
    PROC_NAME="expose_passport_swagger_docs"
    LOG="${PROC_NAME}.log"

    # Expose via HTTP
    cd $PASSPORT_JAVA_DOC_PATH
    kill_proc "PROC_NAME=${PROC_NAME}"
    PROC_NAME="${PROC_NAME}" http-server --cors -p ${PORT} 2>&1 > $LOG &
    sleep 0.5

    # View
    open "http://127.0.0.1:${PORT}/"
}

################################################################################

install_swagger_ui_osx(){
    cd $SWAGGER_PATH
    REPO="https://github.com/swagger-api/swagger-ui.git"
    DIR="${SWAGGER_PATH}/swagger-ui"
    if [ -d "${DIR}" ]; then
	echo "Repo exists, pulling"
	cd $DIR 
	git pull 
    else
	echo "Repo does not exist, cloning"
	git clone ${REPO}
    fi
}

run_swagger_ui_osx(){
    # Run Swagger UI (by opening a local browser, rendering the swagger-ui)
    SWAGGER_UI="${SWAGGER_PATH}/swagger-ui/dist/index.html"
    open "$SWAGGER_UI"
}

################################################################################

install_swagger_ui_docker(){
    # https://github.com/mrname/docker-swagger-ui
    
    cd $SWAGGER_PATH
    REPO="https://github.com/mrname/docker-swagger-ui.git"
    DIR="${SWAGGER_PATH}/docker-swagger-ui"
    if [ -d "${DIR}" ]; then
	echo "Repo exists, pulling"
	cd $DIR 
	git pull 
    else
	echo "Repo does not exist, cloning"
	git clone ${REPO}
    fi
}

run_swagger_ui_docker(){
    # https://github.com/mrname/docker-swagger-ui
    URL=""
    docker run -d --name swagger-ui -p 8888:8888 -e "API_URL=${URL}" -e "CACHE=0" sjeandeaux/docker-swagger-ui    
}

################################################################################

expose_and_view_passport_java_docs() {
    PORT="9000"
    PROC_NAME="expose_and_view_passport_java_docs"
    LOG="${PROC_NAME}.log"

    # Expose via HTTP
    cd $PASSPORT_JAVA_DOC_PATH
    kill_proc "PROC_NAME=${PROC_NAME}"
    # Run the process with a label, so that we can find it later
    "PROC_NAME=${PROC_NAME}" http-server --cors -p ${PORT} 2>&1 > $LOG &
    sleep 0.1

    # View
    open "http://127.0.0.1:${PORT}/"
}

################################################################################
# MAIN
################################################################################

setup

# expose_and_view_passport_java_docs

#install_swagger_ui_in_osx
install_swagger_ui_docker

#test_swagger_ui_docker
expose_passport_swagger_docs


