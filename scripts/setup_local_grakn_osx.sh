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

install_and_start_grakn_in_osx(){    
    brew update
    brew install grakn
    
    grakn.sh start

    # Quickstart setup
    # https://grakn.ai/pages/documentation/get-started/quickstart-tutorial.html
    graql.sh -f /repos/grakn/grakn-dist/src/examples/basic-genealogy.gql
}


show_processes(){
    show_process_pid_and_ports "GraknEngineServer"
    show_process_pid_and_ports "CassandraDaemon"
    show_process_pid_and_ports "redis-server"   
}

# This is idempotent
install_and_start_grakn_in_osx

show_processes


