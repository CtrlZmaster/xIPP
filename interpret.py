"""
Project: IPP Project 1
File: interpret.py
Title: IPPcode19 interpreter
Description: This is an interpreter of IPPcode19 in XML representation
Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
"""

from copy import deepcopy
import getopt
import itertools
import sys
import re
import xml.etree.ElementTree as xml_et
import codecs

"""
Importing interpreter modules
"""
import modules.arguments as arguments
import modules.frameset as frameset
import modules.instructions as instructions
import modules.program as program
import modules.variables as variables


class Frame:
    '''Frame that holds variables

       @TODO Eliminate this entirely

       Variables are stored in a dictionary, where keys are variable names without the frame specification and values
       are instances of class Variable.
    '''
    def __init__(self, scope):
        '''Frame constructor

           Creates an empty frame.
           @param scope Takes the scope of the frame: local, global, temporary
        '''
        self.scope = scope
        self.vars = {}

    def set_var(self, identifier):
        '''Creates a new variable

           Creates an instance of class Variable on the frame.
           @param identifier Name of the variable (without frame)
        '''


    def update_var(self, identifier, value):
        '''Changes value of a variable

           Calls method of class Varibale on the variable from a dictionary.
           @param identifier Name of the variable (without frame)
           @param value Value to write
        '''
        try:
            self.vars[identifier].set_value(value)
        except KeyError:
            raise

    def get_var(self, identifier):
        '''Returns variable object

           Returns reference to the object from the variable dictionary.
           @param identifier Name of the variable (without frame)
           @return Instance of class Variable
        '''
        try:
            retval = self.vars[identifier]
        except KeyError:
            raise

        return retval










"""
SCRIPT EXECUTION POINT
"""
# Read arguments
args = arguments.Args()
args.parse()

# Implicitly false until set
if args.source_file is not False:
    try:
        source_file = open(args.source_file)
    except IOError:
        print("interpret.py: File with source code not found.", file=sys.stderr)
        sys.exit(11)

    # Reading code from a file
    try:
        xml_root = xml_et.parse(source_file).getroot()
    except xml_et.ParseError:
        print("interpret.py: Malformed XML.", file=sys.stderr)
        sys.exit(31)

    source_file.close()
    program = program.Program(xml_root)
else:
    # Reading code from stdin (source arg not set)
    source = sys.stdin.read()
    try:
        xml_root = xml_et.fromstring(source)
    except xml_et.ParseError:
        print("interpret.py: Malformed XML.", file=sys.stderr)
        sys.exit(31)

    program = program.Program(xml_root)

# Implicitly false until set
if args.input_file is not False:
    try:
        input_file = open(args.input_file)
    except IOError:
        print("interpret.py: File with input not found.", file=sys.stderr)
        sys.exit(11)

    program.set_input(input_file)

# Now we have a program instance with instructions
program.extract_instructions()

# Start the interpreter
program.execute()

# Close the input file if needed
if program.stdin_file is not None:
    program.stdin_file.close()

sys.exit(0)
