"""
Project: IPP Project 1
File: interpret.py
Title: IPPcode19 interpreter
Description: This is an interpreter of IPPcode19 in XML representation
Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
"""

import argparse
import sys
from xml.dom import minidom


class FrameSet:
    def __init__(self):
        self.local_frame_stack = []
        self.global_frame = Frame("global")
        self.temporary_frame = Frame("temporary")

    def push_temp(self):
        self.local_frame_stack.append(self.temporary_frame)
        self.temporary_frame = None

    def pop_local(self):
        try:
            self.temporary_frame = self.local_frame_stack.pop()
        except IndexError:
            print("Error: Cannot execute POPFRAME. Local frame stack is empty.", file=sys.stderr)
            sys.exit(55)


class Frame:
    def __init__(self, scope):
        self.scope = scope
        self.vars = {}


class Variable:
    def __init__(self):
        self.value = ""
        self.type = "undefined"

    def set_value(self, value):
        self.value = value
        self.type = type(value)

    def get_type(self):
        return self.type

    def get_value(self):
        return self.value


class Program:
    def __init__(self, xml_dom):
        self.parsed_program = xml_dom
        self.instructions = []          # Array of instructions
        self.labels = {}                # Index names are labels and keys are instruction indices


class Instruction:
    def __init__(self, name, arg1=None, arg2=None, arg3=None):
        self.name = name
        self.argv = []
        if arg1:
            self.argv.append(arg1)
        if arg2:
            self.argv.append(arg2)
        if arg3:
            self.argv.append(arg3)

        param_values = {
            # 0 ARGUMENTS
            'CREATEFRAME': "[]",
            'PUSHFRAME': "[]",
            'POPFRAME': "[]",
            'RETURN': "[]",
            'BREAK': "[]",
            # 1 ARGUMENT
            'DEFVAR': "['var']",
            'CALL': "['label']",
            'PUSHS': "['symb']",
            'POPS': "['var']",
            'WRITE': "['symb']",
            'LABEL': "['label']",
            'JUMP': "['label']",
            'EXIT': "['symb']",
            'DPRINT': "['symb']",
            # 2 ARGUMENTS
            'MOVE': "['var', 'symb']'",
            'INT2CHAR': "['var', 'symb']",
            'READ': "['var', 'type']",
            'STRLEN': "['var', 'symb']",
            'TYPE': "['var', 'symb']"
            # 3 ARGUMENTS
        }
        try:
            self.expected_args = eval(param_values[name])
        except IndexError:
            print("Error: Unknown instruction name.", file=sys.stderr)
            sys.exit(32)


class Args:
    @staticmethod
    def parse():
        parser = argparse.ArgumentParser(prog="python3.6 interpret.py",
                                         description="This script interprets code from IPPcode19 XML representation."
                                         )
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--source",
                            help="File with the XML representation of IPPcode19 code that will be interpreted.")
        group.add_argument("--input",
                            help="Expects a text file that will be provided to the script as its standard input. \
                            In that case, source code is read from stdin.")
        return parser.parse_args()



"""
SCRIPT EXECUTION POINT
"""
args = Args.parse()

if args.source is not False:
    with open(args.source) as source_file:
        # Reading code from a file
        xml_dom = minidom.parse(source_file)
        program = Program(xml_dom)
else:
    # Reading code from stdin (source arg not set)
    source = sys.stdin.read()
    xml_dom = minidom.parseString(source)
    program = Program(xml_dom)

