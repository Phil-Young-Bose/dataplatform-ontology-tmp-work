#!/usr/bin/env python

import os
import sys
import time
import inspect
import argparse

from dataplatform_pyutils import cli

class SetupGrakn:
    """ This Class manages a local Grakn setup
    """

    def __init__(self, grakn_work_dir):
        """ Class Constructor
        """ 
        self.grakn_work_dir = grakn_work_dir
        self.ensure_grakn_work_dir_exists()

    def ensure_grakn_work_dir_exists(self):
        if (self.grakn_work_dir != None):
            self.grakn_work_dir = grakn_work_dir
        else:
            self.grakn_work_dir = os.path.join(self.get_this_dir(), "..", "..", "..", "tmp", "grakn", "work_dir")
        cli.ensure_dir_exists(self.grakn_work_dir)
        
    def get_this_dir(self):
        """ Return the path to the directory holding this script
        """
        script_path = os.path.abspath(inspect.getsourcefile(lambda _: None))
        script_dir = os.path.dirname( script_path )
        return script_dir

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
            self.fatal("Command failed: " + cmd + " output: " + d["output"], d["status"])
        return d["output"]

    def get_process_pid_and_ports(self, proc_name):
        """ Given a process name, get the PID(s) matching that name and all PORT(s) on which that pid or pids listen
        """
        d={}
        pids=self.cmd("ps -ax -o pid,command | grep -v grep | grep '{0}' | perl -pe 's/^\s+//' | cut -d' ' -f 1".format(proc_name))
        if len(pids) > 0:
            d["pids"]=pids
            port_list=[]
            for pid in pids:
                ports=self.cmd("""lsof -Pan -p {0} -i | grep 'LISTEN' | perl -pe 's/.*:(.*?) \(LISTEN\)/$1/' | tr '\\n' ' '""".format(pid))
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

    def clear_grakn_db(self):
        cli.run_shell_command("yes | grakn.sh clean")
    
    def install_grakn_in_osx(self):    
        # Is it running?
        flag=False
        status=self.get_grakn_processes()
        if "GraknEngineServer" in status:
            if "pids" in status["GraknEngineServer"]:
                flag = True

        if flag == False:
            # Install as needed
            rc = cli.run_shell_command_with_output("which grakn.sh")["status"]
            if ( rc != 0 ):
                cli.log.info("Installing Grakn")                
                self.cmd("brew update")
                self.cmd("brew install grakn")
            # Start
            cli.log.info("Starting Grakn")
            cmd="cd {0} && grakn.sh start &".format(self.grakn_work_dir)
            cli.run_shell_command(cmd)
        else:            
            cli.log.info("Grakn is already running")

        cli.log.info("Wait for the server to be up")
        cmd="curl http://localhost:4567"
        cli.wait_for_command(cmd, 0.5, 60)
            
        status=self.get_grakn_processes()
        cli.log.info("STATUS: " + str(status))

    def run_grakn_script(self, grakn_script):
        cli.log.info("About to run gracl script: " + grakn_script)                
        output=self.cmd("graql.sh -f " + grakn_script)
        cli.log.info("Ran gracl script: " + grakn_script + " . Output: " + str(output))
        
    def test_grakn_in_osx(self):        
        self.run_grakn_script( os.path.join(self.get_this_dir(), "..", "..", "..", "..", "org_repository", "ontology.gql") )
        self.run_grakn_script( os.path.join(self.get_this_dir(), "..", "..", "..", "..", "org_repository", "test.gql") )
        self.run_grakn_script( os.path.join(self.get_this_dir(), "..", "..", "..", "..", "org_repository", "test_query.gql") )
        
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
        self.install_grakn_in_osx() # Start Grakn        
        #self.clear_grakn_db() # Erase the data (Stops services)
        #self.install_grakn_in_osx() # Start Grakn        
        
        self.test_grakn_in_osx()
        
if __name__ == "__main__":
    """ This provides a CLI interface to this code
    """
    argv=sys.argv[1:] 
    sg=SetupGrakn(None)
    sg.main(argv)   



