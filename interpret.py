"""
Project: IPP Project 1
File: interpret.py
Title: IPPcode19 interpreter
Description: This is an interpreter of IPPcode19 in XML representation
Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
"""

import argparse
import itertools
import sys
from xml.dom import minidom
import xml.etree.ElementTree as xml_et


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
        self.elem_program = parsed_xml  # Root element program as Element from ElementTree
        self.instructions = {}          # Dictionary of instructions - keys are their order values (iterate sorted)
        self.labels = {}                # Index names are labels and keys are instruction order values
        self.name = None
        self.description = None

    def extract_instructions(self):
        # Check program attributes
        program_attr = self.elem_program.attrib
        ## Language attribute
        try:
            language = program_attr.pop("language")
        except KeyError:
            print("Error: Program element is missing a language attribute.", file=sys.stderr)
            sys.exit(32)
        if language != "IPPcode19":
            print("Error: Program element contains an incorrect language attribute.", file=sys.stderr)
            sys.exit(32)
        ## Test for allowed attributes
        allowed_program_attr = {"language", "name", "description"}
        for program_attr in program_attr.keys():
            if program_attr not in allowed_program_attr:
                print("Error: Invalid attribute in the program element.", file=sys.stderr)
                sys.exit(32)

        # Checking instructions
        for (idx, instruction) in enumerate(self.elem_program.findall("*"), start=1):
            # No instruction elements
            if instruction is None:
                print("Error: No instruction elements found.", file=sys.stderr)
                sys.exit(32)

            # Check that only children are instruction elements
            if instruction.tag != "instruction":
                print("Error: Invalid element tag in a child element of the program.", file=sys.stderr)
                sys.exit(32)

            # Extracting instruction attributes
            instruction_attr = instruction.attrib
            ## Get order number
            try:
                order = instruction_attr.pop("order")
            except KeyError:
                print("Error: Undefined order attribute in instruction ", idx, '.', file=sys.stderr)
                sys.exit(32)
            ### Convert to int and check value
            try:
                order = int(order)
            except ValueError:
                print("Error: Order attribute in instruction ", idx, " contains an invalid value.", file=sys.stderr)
                sys.exit(32)

            if order < 1:
                print("Error: Order attribute in instruction ", order, " is not bigger than 0.", file=sys.stderr)
                sys.exit(32)

            ## Get opcode
            try:
                opcode = instruction_attr.pop("opcode")
            except KeyError:
                print("Error: Undefined opcode attribute in instruction ", order, '.', file=sys.stderr)
                sys.exit(32)

            # Getting and checking arguments - at baseline, none are defined
            arg1 = None
            arg1_type = None
            arg2 = None
            arg2_type = None
            arg3 = None
            arg3_type = None
            allowed_arg_tags = {'arg1': None, 'arg2': None, 'arg3': None}
            for argument in instruction.findall("*"):
                # Trying to pop from dictionary with arg tags - fails on unknown and duplicate elements
                try:
                    allowed_arg_tags.pop(argument.tag)
                except KeyError:
                    print("Error: Too many, duplicate arguments or unrecognized child element of instruction", order,
                          '.', file=sys.stderr)
                    sys.exit(32)

                # Checking argument attributes
                arg_attr = argument.attrib
                try:
                    attr_type = arg_attr.pop("type")
                except KeyError:
                    print("Error: Type missing in instruction ", order, ", arg"
                          '.', file=sys.stderr)
                    sys.exit(32)

                arg_text = argument.text  # Element without text returns has text set to None - treating here
                if arg_text is None:
                    arg_text = ""

                # Insert argument and type into the instruction
                if argument.tag == "arg1":
                    arg1 = arg_text
                    arg1_type = attr_type

                if argument.tag == "arg2":
                    arg2 = arg_text
                    arg2_type = attr_type

                if argument.tag == "arg3":
                    arg3 = arg_text
                    arg3_type = attr_type

            self.instructions[order] = Instruction(order, opcode, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type)


class Instruction:
    def __init__(self, order, name, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type):
        self.order = order
        self.name = name
        self.argv = []
        self.arg_types = []
        if arg1_type:
            self.argv.append(arg1)
            self.arg_types.append(arg1_type)
        if arg2_type:
            self.argv.append(arg2)
            self.arg_types.append(arg2_type)
        if arg3_type:
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
            'MOVE': "['var', 'symb']",
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
            # eval expands to a list assignment based on the opcode
            self.expected_arg_types = eval(param_values[name])
        except KeyError:
            print("Error: Unknown instruction name.", file=sys.stderr)
            sys.exit(32)

        # PREEMPTIVE TYPE CHECKING
        accepted_as_symb = {"int", "bool", "string", "nil", "var"}
        arg_num = 0
        for arg_type, expected_arg_type in itertools.zip_longest(self.arg_types, self.expected_arg_types):
            arg_num = arg_num + 1
            if arg_type != expected_arg_type:
                if expected_arg_type == "symb" and arg_type in accepted_as_symb:
                    pass
                else:
                    print("Error: Argument", arg_num, " in instruction ", self.order, "has incorrect type.",
                          file=sys.stderr)
                    sys.exit(53)


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
        xml_root = xml_et.parse(source_file).getroot()
        program = Program(xml_root)
else:
    # Reading code from stdin (source arg not set)
    source = sys.stdin.read()
    xml_root = xml_et.fromstring(source)
    program = Program(xml_root)

# Now we have a program instance
program.extract_instructions()


exit(0)
