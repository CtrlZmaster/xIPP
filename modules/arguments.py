import getopt
import sys

import modules.errors as IntError


class Args:
    '''Arguments class

       Implements argument parsing and opening necessary files.
    '''
    def __init__(self):
        '''Argument class constructor

        '''
        self.source_file = False
        self.input_file = False
        self.help = False

    def parse(self):
        '''Argument parser

           Parses the arguments and handles argument logic. Prints help if needed.
        '''
        try:
            arguments, tail = getopt.getopt(sys.argv[1:], "", ["help", "source=", "input="])
        except getopt.GetoptError:
            print("interpret.py: Unknown argument.", file=sys.stderr)
            sys.exit(10)

        for arg, value in arguments:
            if   arg == "--source":
                self.source_file = value
            elif arg == "--input":
                self.input_file = value
            elif arg == "--help":
                self.help = True
            else:
                # Unhandled options
                pass

        # Argument logic
        if self.help is True:
            if self.input_file is not False or self.source_file is not False:
                print("interpret.py: --help argument must be the only argument.", file=sys.stderr)
                sys.exit(10)
            self.print_help()

        if self.source_file is False and self.input_file is False:
            print("interpret.py: One of --source or --input argument is required.", file=sys.stderr)
            sys.exit(10)

    @staticmethod
    def print_help():
        '''Prints help

           Prints the help and ends the program successfully.
        '''
        print("USAGE:")
        print("python3.6 interpret.py (--help | --source=SOURCE | --input=INPUT)")
        print()
        print("DESCRIPTION:")
        print("This script interprets code from IPPcode19 XML representation. At least one ")
        print("of the options must be provided.")
        print()
        print("OPTIONS:")
        print("--help           Shows this help message and exit")
        print("--source=SOURCE  File SOURCE with the XML representation of IPPcode19 code")
        print("                 that will be interpreted.")
        print("--input=INPUT    Expects a text file INPUT that will be provided to the")
        print("                 script as its standard input. In that case, source code is")
        print("                 read from stdin.")

        sys.exit(0)

