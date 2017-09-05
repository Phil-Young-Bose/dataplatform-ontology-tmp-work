# GOAL
#  Install Grakn
#
# RESOURCES
#  https://grakn.ai/pages/documentation/get-started/quickstart-tutorial.html


MY_PATH=$( cd $(dirname "$0") && pwd )

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

show_process_pid_and_ports() {
    PROC="$1"
    PID=$(ps -ax -o pid,command | grep -v grep | grep "$PROC" | cut -d' ' -f 1)
    PORTS=$(lsof -Pan -p ${PID} -i | grep 'LISTEN' | perl -pe 's/.*:(.*?) \(LISTEN\)/$1/' | tr '\n' ' ') 
    echo "PROC:${PROC} PID:${PID} PORTS:${PORTS}"
}

heading() {
    SEP="--------------------------------------------------------------------------------"
    echo -e "\n${SEP}\n${1}\n${SEP}"
}

# GRAKNLABS Docker. Single image...
install_and_start_grakn_in_docker(){
    TMP_PATH=$(cd "${MY_PATH}/../tmp" && pwd)
    GRAKN_DB_PATH=$( make_dir "${TMP_PATH}/graknlabs_docker/db" )

    docker pull graknlabs/grakn
    #docker run -dt -v $(pwd)/db/:/grakn/db/ -p 4567:4567  -p 9042:9042 -p 9160:9160 --name GRAKN graknlabs/grakn

    docker stop GRAKN
    docker rm GRAKN    
    docker run -dt -v ${GRAKN_DB_PATH}/:/grakn/db/ -p 4567:4567  -p 9042:9042 -p 9160:9160 --name GRAKN graknlabs/grakn    
}


# This is idempotent
install_and_start_grakn_in_docker

