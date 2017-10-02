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
        sys.exit(status)
        
    def cmd(self, cmd, echo_output=True, show_cmd=False):
        """ Convenience method to run shell commands.
            Exit here if the command fails.
            Returns the command output as a string
        """
        echo_output=True
        show_cmd=True
        d=cli.run_shell_command_with_output(cmd, echo_output, show_cmd)
        if d["status"] != 0:
            self.fatal("Command failed: " + cmd + " output: " + str(d["output"]), d["status"])
        return d["output"]

    def get_grakn_docker_image(self):
        """ Get the Docker Image
        """
        cmd="docker pull graknlabs/grakn"
        cli.log.info("About to run: " + cmd )
        output=self.cmd(cmd, True, True)        
        cli.log.info("Ran: " + cmd + " Output: " + str(output))        
        
    def run_docker_container(self):
        """ Run the Container
        """
        # Fron https://hub.docker.com/r/graknlabs/grakn/
        # docker run -dt -v $(pwd)/db/:/grakn/db/ -p 4567:4567  -p 9042:9042 -p 9160:9160 --name GRAKN graknlabs/grakn
        
        container="GRAKN"
        image="graknlabs/grakn"        
        drive_mappings={}
        drive_mappings[ self.grakn_db_dir ] = "/grakn/db"        
        drive_mappings[ self.project_dir ] = "/project"
        opts=" -p 4567:4567 -p 9042:9042 -p 9160:9160"        
        args=None
        docker.start_container(container, image, drive_mappings, opts, args)
        
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
        procs=["GraknEngineServer","CassandraDaemon","redis-server"]
        status={}
        for proc in procs:
            d=self.get_process_pid_and_ports(proc)
            status[proc]=d
        return status

    def clean_grakn_db(self):
        """ Run a shell script that cleans the grakn DB (without stopping services)
        """
        script = os.path.join( "/", "project", "setup", "grakn", "local", "docker", "clean_grakn.sh" )
        cmd = """docker exec -it GRAKN /bin/bash -c '{0}' """.format(script)
        cli.log.info("About to run: " + cmd)
        pids=self.cmd( cmd )
        
    def run_grakn_script(self, grakn_script_dir, grakn_script):
        script = os.path.join( grakn_script_dir, grakn_script )
        cli.log.info("About to run gracl script: " + script)
        cmd = """docker exec -it GRAKN /bin/bash -c '/grakn/bin/graql.sh -f {0}' """.format(script)
        output=self.cmd( cmd )
        cli.log.info("Ran gracl script: " + script + " . Output: " + str(output))
        
    def test_grakn(self):
        grakn_script_dir = os.path.join("/project", "org_repository")
        self.run_grakn_script( grakn_script_dir, "ontology.gql") 
        self.run_grakn_script( grakn_script_dir, "test.gql" )
        self.run_grakn_script( grakn_script_dir, "test_query.gql" )
        
    def main(self,argv):        
        """ This is the main work routine
        """
        cli.setup_logging("/tmp/setup.out")
        os = cli.get_os_type()
        if (os not in ["mac"]):
            cli.fatal("Untested OS: " + os)
        cli.log.info("Starting Program")
        cli.log.info("ARGS:" + str(argv))
        self.cmd("ls / | head -5 # test ability to run shell commands")
        #       
        self.get_grakn_docker_image()
        self.run_docker_container()
        #
        cli.log.info( self.get_grakn_processes() )
        self.clean_grakn_db()
        cli.log.info( self.get_grakn_processes() )        
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



