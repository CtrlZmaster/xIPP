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
            print("Error: Local frame stack is empty.", file=sys.stderr)
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
    def __init__(self, parsed_xml):
        self.parsed_program = parsed_xml
        self.instructions = []          # Array of instructions
        self.labels = {}                # Index names are labels and keys are instruction order values
        self.name = None
        self.description = None

    def extract_instructions(self):
        programs = self.parsed_program.getElementsByTagName("program")
        if programs.length is not 1:
            print("Error: Too many program elements.", file=sys.stderr)
            sys.exit(32)
        root_program = programs[0]
        self.name = root_program.getAttribute("name")
        self.description = root_program.getAttribute("description")

        instructions = root_program.getElementsByTagName("instruction")
        for idx, instruction in enumerate(instructions, start=1):
            # Get order number
            order = instruction.getAttribute("order")
            if not order:
                print("Error: Undefined order attribute.", file=sys.stderr)
                sys.exit(32)
            name = instruction.getAttribute("opcode")

            # Get opcode
            if not name:
                print("Error: Undefined opcode attribute.", file=sys.stderr)
                sys.exit(32)

            # Get argument 1 and its type if it's present
            arg1s = instruction.getElementsByTagName("arg1")
            if arg1s.length > 1:
                print("Error: Multiple arg1 elements.", file=sys.stderr)
                sys.exit(32)
            elif arg1s.length is 1:
                arg1 = arg1s[0]
                arg1_type = arg1.getAttribute("type")
                if not arg1_type:
                    print("Error: Undefined type attribute in argument 1 of instruction ", order, ".", file=sys.stderr)
                    sys.exit(32)
                arg1 = arg1.nodeValue

            # Get argument 2 and its type if it's present
            arg2s = instruction.getElementsByTagName("arg2")
            if arg2s.length > 1:
                print("Error: Multiple arg2 elements.", file=sys.stderr)
                sys.exit(32)
            elif arg2s.length is 1:
                arg2 = arg2s[0]
                arg2_type = arg2.getAttribute("type")
                if not arg2_type:
                    print("Error: Undefined type attribute in argument 2 of instruction ", order, ".", file=sys.stderr)
                    sys.exit(32)
                arg2 = arg2.nodeValue

            # Get argument 3 and its type if it's present
            arg3s = instruction.getElementsByTagName("arg3")
            if arg3s.length > 1:
                print("Error: Multiple arg3 elements.", file=sys.stderr)
                sys.exit(32)
            elif arg3s.length is 1:
                arg3 = arg3s[0]
                arg3_type = arg3.getAttribute("type")
                if not arg3_type:
                    print("Error: Undefined type attribute in argument 3 of instruction ", order, ".", file=sys.stderr)
                    sys.exit(32)
                arg3 = arg3.nodeValue

            self.instructions[order] = Instruction(name, arg1, arg2, arg3.nodeValue)


class Instruction:
    def __init__(self, name, arg1=None, arg2=None, arg3=None, arg1_type=None, arg2_type=None, arg3_type=None):
        self.name = name
        self.argv = []
        self.arg_types = []
        if arg1:
            self.argv.append(arg1)
            self.arg_types.append(arg1_type)
        if arg2:
            self.argv.append(arg2)
            self.arg_types.append(arg2_type)
        if arg3:
            self.argv.append(arg3)
            self.arg_types.append(arg3_type)

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
            'TYPE': "['var', 'symb']",
            # 3 ARGUMENTS
            'ADD': "['var','symb','symb']",
            'SUB': "['var','symb','symb']",
            'MUL': "['var','symb','symb']",
            'IDIV': "['var','symb','symb']",
            'LT': "['var','symb','symb']",
            'GT': "['var','symb','symb']",
            'EQ': "['var','symb','symb']",
            'AND': "['var','symb','symb']",
            'OR': "['var','symb','symb']",
            'NOT': "['var','symb','symb']",
            'STRI2INT': "['var','symb','symb']",
            'CONCAT': "['var','symb','symb']",
            'GETCHAR': "['var','symb','symb']",
            'SETCHAR': "['var','symb','symb']",
            'JUMPIFEQ': "['label','symb','symb']",
            'JUMPIFNEQ': "['label','symb','symb']"
        }
        try:
            # eval expands to a list assignment based on opcode
            self.expected_arg_types = eval(param_values[name])
        except KeyError:
            print("Error: Unknown instruction name.", file=sys.stderr)
            sys.exit(32)

        # PREEMPTIVE TYPE CONTROL


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

# Now we have a program instance
program.extract_instructions()