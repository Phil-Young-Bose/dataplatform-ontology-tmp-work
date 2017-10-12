#!/usr/bin/env python

import os
import sys
import time
import inspect
import argparse

from dataplatform_pyutils import cli
from dataplatform_pyutils import docker

class SetupGrakn:
    """ This Class manages a local Grakn setup
    """

    def __init__(self, project_dir, grakn_db_dir):
        """ Class Constructor
        """
        self.project_dir = project_dir        
        self.grakn_db_dir = grakn_db_dir
        
    def report(self,msg):
        """ Log the given message, with emphasis
        """
        spacer="----------------------------------------"
        cli.log.info(spacer)
        cli.log.info(msg)    
        cli.log.info(spacer)

    def fatal(self, msg, status):
        self.report(msg)
        cli.log.info("Fatal: Exiting")        
        sys.exit(status)
        
    def cmd(self, cmd, echo_output=True, show_cmd=False):
        """ Convenience method to run shell commands.
            Exit here if the command fails.
            Returns the command output as a string
        """
        echo_output=True
        show_cmd=True
        d=cli.run_shell_command_with_output(cmd, echo_output, show_cmd)
        if (not d["status"] == 0): # The hash may not contain "status", on failure
            self.fatal("Command failed: " + cmd + " output: " + str(d["output"]), 1)
        return d["output"]

    def get_grakn_docker_image(self):
        """ Get the Docker Image
        """
        cli.log.info("Getting Grakn Docker image")                        
        cmd="docker pull graknlabs/grakn"
        cli.log.info("About to run: " + cmd )
        output=self.cmd(cmd, True, True)        
        cli.log.info("Ran: " + cmd + " Output: " + str(output))        
        
    def get_process_pid_and_ports(self, proc_name):
        """ Given a process name, get the PID(s) matching that name and all PORT(s) on which that pid or pids listen
        """
        d={}
        cmd = """docker exec -it GRAKN /bin/bash -c 'ps eax -o pid,command | grep -v grep | grep {0}' | perl -pe 's/^\s+//' | cut -d' ' -f 1""".format(proc_name)
        cli.log.info("About to run: " + cmd)
        pids=self.cmd( cmd )
        if len(pids) > 0:
            d["pids"]=pids
            port_list=[]
            for pid in pids:
                cmd = """docker exec -it GRAKN /bin/bash -c 'lsof -Pan -p {0} -i' | grep 'LISTEN' | perl -pe 's/.*:(.*?) \(LISTEN\)/$1/' | tr '\\n' ' '""".format(pid)
                ports = self.cmd( cmd )
                for port in ports:
                    port_list.append(port)
            d["ports"]=port_list
        return d
        
    def get_grakn_processes(self):
        """ Return a dictionary with the status of the procs matching the strings known to be associated with the app
        """
        cli.log.info("Getting Grakn process status")                                
        procs=["GraknEngineServer","CassandraDaemon","redis-server"]
        status={}
        for proc in procs:
            d=self.get_process_pid_and_ports(proc)
            status[proc]=d
        return status
        
    def is_grakn_running(self):
        """ Return 0 if Grakn status reports running, -1 otherwise
        """
        cli.log.info("Is Grakn process running")        
        # Return 0 if all services report up
        cmd="""echo '/grakn/bin/grakn.sh status | egrep "running|foreground" | wc -l' | docker exec -i GRAKN bash"""
        d=cli.run_shell_command_with_output(cmd)
        cli.log.info("Grakn Status Results: " + str(d))
        isUp=False
        try:
            if ( d["output"][0] == '3' ):
                isUp=True
        except NameError:
            pass
        if ( isUp == True ):
            cli.log.info("Grakn seems to be up")
            return 0
        else:            
            cli.log.info("Grakn servics seem to be down")
            return -1            

    def wait_for_grakn_to_start(self):
        """ Return 0 if Grakn status reports running, after waiting a bit, -1 otherwise
        """
        cli.log.info("Waiting for Grakn to start")        
        container="GRAKN"
        log_str="Web Dashboard available"
        sleep_interval = 2
        iterations = 30
        cli.log.info("Watching the Grakn container logs for: '" + log_str + "'")        
        docker.wait_for_log_output(container, log_str, sleep_interval, iterations)
        return 0
        
    def start_docker_container(self):
        """ Run the Container
        """
        cli.log.info("Starting Grakn container")
        # Fron https://hub.docker.com/r/graknlabs/grakn/
        # docker run -dt -v $(pwd)/db/:/grakn/db/ -p 4567:4567  -p 9042:9042 -p 9160:9160 --name grakn graknlabs/grakn
        container="GRAKN"
        image="graknlabs/grakn"        
        drive_mappings={}
        drive_mappings[ self.grakn_db_dir ] = "/grakn/db"        
        drive_mappings[ self.project_dir ] = "/project" # Map in this project, so we can easily run scripts in the Docker container
        opts=" -p 4567:4567 -p 9042:9042 -p 9160:9160"        
        args=None
        docker.start_container(container, image, drive_mappings, opts, args)

    def start_grakn_services(self):
        """ Invoke the start script
        """
        cli.log.info("Starting Grakn services")        
        docker_cmd = "/grakn/bin/grakn.sh start"
        cmd = """docker exec -it GRAKN /bin/bash -c '{0}' """.format(docker_cmd)
        cli.log.info("About to run: " + cmd)
        #output=self.cmd(cmd, True, True)
        output=cli.run_shell_command_with_output(cmd, False, False)["output"]
        cli.log.info("Ran: " + cmd + " Output: " + str(output))        
        
    def stop_grakn_services(self):
        cli.log.info("Stopping Grakn services")                
        docker_cmd = "/grakn/bin/grakn.sh stop"
        cmd = """docker exec -it GRAKN /bin/bash -c '{0}' """.format(docker_cmd)
        cli.log.info("About to run: " + cmd)
        output=self.cmd(cmd, True, True)        
        cli.log.info("Ran: " + cmd + " Output: " + str(output))

    def restart_grakn_services(self):
        """ Restarting services in the Docker Container seems to always fail
            Some services (e.g. Cassandra) fail to come up again
        """
        # TODO: get restart to work
        self.fatal("Restarting services in the Docker Container does not work properly. Cassandra SNAFU. PURGE instead!",1)
        """
        cli.log.info("Restarting Grakn services")
        cli.log.info( self.get_grakn_processes() )        
        self.stop_grakn_services()
        cli.log.info( self.get_grakn_processes() )
        loop=1
        while ( not self.is_grakn_running() == 0 ):
            cli.log.info("Re-starting Grakn services")            
            self.start_grakn_services()
            loop += 1
            if ( loop >= 3 ):
                break
        cli.log.info("Grakn should be up")
        cli.log.info( self.get_grakn_processes() )
        """
        
    def clean_grakn_db(self):
        """ Run a shell script that cleans the grakn DB (without stopping services)
        """
        cli.log.info("Cleaning Grakn")                
        script = os.path.join( "/", "project", "setup", "grakn", "local", "docker", "clean_grakn.sh" )
        cmd = """docker exec -it GRAKN /bin/bash -c '{0}' """.format(script)
        cli.log.info("About to run: " + cmd)
        pids=self.cmd( cmd )
        
    def run_grakn_script(self, grakn_script_dir, grakn_script):        
        script = os.path.join( grakn_script_dir, grakn_script )
        cli.log.info("About to run gracl script: " + script)
        cmd = """docker exec -it GRAKN /bin/bash -c '/grakn/bin/graql.sh -n -f {0}' """.format(script)
        output=self.cmd( cmd )
        cli.log.info("Ran gracl script: " + script + " . Output: " + str(output))
        
    def test_grakn(self):
        """ Run some clean tests
        """
        self.clean_grakn_db()
        #
        grakn_script_dir = os.path.join("/project", "org_repository")
        self.run_grakn_script( grakn_script_dir, "ontology.gql") 
        self.run_grakn_script( grakn_script_dir, "test.gql" )
        self.run_grakn_script( grakn_script_dir, "test_query.gql" )

    def ensure_grakn_is_running(self):
        """ Make sure Grakn is running 
        """
        self.report("Ensuring Grakn is running")        
        if (self.is_grakn_running() == 0):
            cli.log.info("Grakn is already running")
        else:
            cli.log.info("Grakn is not running")            
            self.get_grakn_docker_image()            
            self.start_docker_container()
            if ( self.wait_for_grakn_to_start() == 0 ):
                cli.log.info("Grakn started")
            else:
                self.fatal("Grakn failed to start",1)                                
        #cli.log.info( self.get_grakn_processes() )

    def stop_docker_container(self):
        """ Stop the Docker container for the app
        """
        cli.log.info("Stopping Grakn container")
        cmd = """docker stop GRAKN"""
        d=cli.run_shell_command_with_output(cmd, False, False)
        cli.log.info("Command: " + cmd + " output: " + str(d))
        
    def remove_docker_container(self):
        """ Remove the Docker container for the app
        """
        cli.log.info("Removing Grakn container")        
        cmd = """docker container rm GRAKN"""
        d=cli.run_shell_command_with_output(cmd, False, False)
        cli.log.info("Command: " + cmd + " output: " + str(d))
        
    def remove_grakn_db_dir(self):
        cli.log.info("Removing Grakn db dir")
        #Be safe. Only delete the dir if it contains an expected string
        grakn="grakn"
        if (grakn in self.grakn_db_dir):
            cli.ensure_dir_does_not_exist(self.grakn_db_dir)
        else:
            self.fatal("Error: it does not seem safe to delete dir:" + self.grakn_db_dir + " as it does not contain:" + grakn,1)
        
    def purge_grakn(self):
        """ Stop and remove the Docker container and all temp/db files
        """
        self.report("Purging Grakn")
        self.stop_docker_container()
        self.remove_docker_container()
        self.remove_grakn_db_dir()
            
    def main(self,argv):        
        """ This is the main work routine
        """
        cli.setup_logging("/tmp/setup.out")        
        os = cli.get_os_type()
        if (os not in ["mac"]):
            self.fatal("Untested OS: " + os,1)
        cli.log.info("Starting Program")
        cli.log.info("ARGS:" + str(argv))
        self.cmd("ls / | head -5 # test ability to run shell commands")
        if (not self.is_grakn_running() == 0):
            cli.log.info("Grakn is not (fully) up. Prep before starting it.")            
            ###self.restart_grakn_services() # Restarting services in the Docker container fails
            self.purge_grakn()
        self.ensure_grakn_is_running()
        self.test_grakn()
                
if __name__ == "__main__":
    """ This provides a CLI interface to this code
    """

    # Calculate local paths
    script_path = os.path.abspath(inspect.getsourcefile(lambda _: None))
    script_dir = os.path.dirname( script_path )
    project_dir = os.path.abspath( os.path.join(script_dir, "..", "..", "..", "..") )
    grakn_db_dir = os.path.abspath( os.path.join(project_dir, "tmp", "grakn", "docker", "db_dir") )
    
    cli.ensure_dir_exists(project_dir)
    cli.ensure_dir_exists(grakn_db_dir)            
    
    argv=sys.argv[1:] 
    sg=SetupGrakn(project_dir, grakn_db_dir)
    sg.main(argv)   



