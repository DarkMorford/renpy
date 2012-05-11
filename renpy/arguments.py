# Copyright 2004-2011 Tom Rothamel <pytom@bishoujo.us>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This file handles argument parsing. Argument parsing takes place in 
# two phases. In the first phase, we only parse the arguments that are
# necessary to load the game, and run the init phase. The init phase
# can register commands and arguments. These arguments are parsed at 
# the end of the init phase, before the game begins running, and can 
# decide if the game runs or some other action occurs.

import os
import argparse 
import renpy


# A map from command name to a (function, flag) tuple. The flag is true if the
# function will parse command line arguments, and false otherwise. 
commands = { }

class ArgumentParser(argparse.ArgumentParser):
    """
    Creates an argument parser that is capable of parsing the standard Ren'Py
    arguments, as well as arguments that are specific to a sub-command. 
    """
    
    def __init__(self, second_pass=True, description=None):
        """
        Creates an argument parser.
        
        `second_pass`
            True if this is the second pass through argument parsing. (The pass
            that parses sub-commands.)
            
        `description`
            If supplied, this will be used as a description of the subcommand
            to run.
        """
    
        self.group = self

        argparse.ArgumentParser.__init__(self, description="The Ren'Py visual novel engine.", add_help=False)
        
        self.add_argument(
            "basedir", default=None, nargs='?', 
            help="The base directory containing of the project to run. This defaults to the directory containing the Ren'Py executable."
            )
        
        command_names = ", ".join(sorted(commands))
        
        self.add_argument(
            "command",
            help="The command to execute. Available commands are: " + command_names + ". Defaults to 'run'.",
            default="run",
            nargs='?')
        
        self.add_argument(
            "--savedir", dest='savedir', default=None, metavar="DIRECTORY",
            help="The directory where saves and persistent data are placed.")
    
        self.add_argument(
            '--trace', dest='trace', action='store', default=0, type=int, metavar="LEVEL",
            help="The level of trace Ren'Py will log to trace.txt. (1=per-call, 2=per-line)")

        self.add_argument(
            "--version", action='version', version=renpy.version,
            help="Displays the version of Ren'Py in use.")
        
        self.add_argument("--lint", action="store_const", dest="command", const="lint", help=argparse.SUPPRESS)
        
        if second_pass:
            self.add_argument("-h", "--help", action="help", help="Displays this help message, then exits.")

            command = renpy.game.args.command #@UndefinedVariable
            self.group = self.add_argument_group("{0} command".format(command), description)
            
    def add_argument(self, *args, **kwargs):
        if self.group is self:
            argparse.ArgumentParser.add_argument(self, *args, **kwargs)
        else:
            self.group.add_argument(*args, **kwargs)
            
            

def run():
    """
    The default command, that (when called) leads to normal game startup.
    """
          
    ap = ArgumentParser(description="Runs the current project normally.")
            
    ap.add_argument(
        '--profile-display', dest='profile_display', action='store_true', default=False,
        help="If present, Ren'Py will report the amount of time it takes to draw the screen.")

    ap.add_argument(
        '--debug-image-cache', dest='debug_image_cache', action='store_true', default=False,
        help="If present, Ren'Py will log information regarding the contents of the image cache.")

    ap.add_argument(
        '--warp', dest='warp', default=None,
        help='This takes as an argument a filename:linenumber pair, and tries to warp to the statement before that line number.')

    args = renpy.game.args = ap.parse_args()
    
    if args.profile_display: #@UndefinedVariable
        renpy.config.profile = True

    if args.debug_image_cache:
        renpy.config.debug_image_cache = True

    return True

#    op.add_option('--rmpersistent', dest='rmpersistent', action='store_true',
#                  help="Deletes the persistent data, and exits.")

    # ap.set_defaults(function=None)


def compile(): #@ReservedAssignment
    """
    This command is used to quit without doing anything.
    """

    takes_no_arguments("Recompiles the game script.")
    
    return False

def rmpersistent():
    """
    This command is used to delete the persistent data.
    """

    takes_no_arguments("Deletes the persistent data.")

    try:
        os.unlink(renpy.config.savedir + "/persistent")
    except:
        pass

    return False


def register_command(name, function):
    """
    Registers a command that can be invoked when Ren'Py is run on the command
    line. When the command is run, `function` is called with no arguments.
    
    If `function` needs to take additional command-line arguments, it should
    instantiate a renpy.arguments.ArgumentParser(), and then call parse_args
    on it. Otherwise, it should call renpy.arguments.takes_no_arguments().
    
    If `function` returns true, Ren'Py startup proceeds normally. Otherwise,
    Ren'Py will terminate when function() returns.
    """
    
    commands[name] = function

def bootstrap():
    """
    Called during bootstrap to perform an initial parse of the arguments, ignoring
    unknown arguments. Returns the parsed arguments, and a list of unknown arguments.
    """
    
    global rest
    
    ap = ArgumentParser(False)
    args, _rest = ap.parse_known_args()
    return args

def pre_init():
    """
    Called before init, to set up argument parsing.
    """
    
    global subparsers    
    
    register_command("run", run)
    register_command("lint", renpy.lint.lint)
    register_command("compile", compile)
    register_command("rmpersistent", rmpersistent)
    register_command("dump", renpy.dump.command)
    
    
def post_init():
    """
    Called after init, but before the game starts. This parses a command
    and its arguments. It then runs the command function, and returns True
    if execution should continue and False otherwise. 
    """

    command = renpy.game.args.command #@UndefinedVariable

    if command not in commands:
        ArgumentParser().error("Command {0} is unknown.".format(command))
    
    return commands[command]()

def takes_no_arguments(description=None):
    """
    Used to report that a command takes no arguments. 
    """
    
    ArgumentParser(description=description).parse_args()
    
    