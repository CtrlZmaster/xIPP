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
import re
import xml.etree.ElementTree as xml_et
import codecs


class FrameSet:
    def __init__(self):
        self.local_frame_stack = []
        self.global_frame = Frame("global")
        self.temporary_frame = None

    def init_temporary_frame(self):
        self.temporary_frame = Frame("temporary")

    def set_var(self, name):
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            self.global_frame.set_var(identifier)

        elif scope == "TF":
            if self.temporary_frame is None:
                print("Error: Temporary frame is not defined.", file=sys.stderr)
                sys.exit(55)

            self.temporary_frame.set_var(identifier)

        elif scope == "LF":
            try:
                self.local_frame_stack[-1].set_var(identifier)
            except IndexError:
                print("Error: Local frame stack is empty.", file=sys.stderr)
                sys.exit(55)

        else:
            print("Error: Unrecognized scope.", file=sys.stderr)
            sys.exit(55)

    def update_var(self, name, value, order):
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            try:
                self.global_frame.update_var(identifier, value)
            except KeyError:
                print("interpret.py:", order, ": Variable", identifier, "doesn't exist.")
                sys.exit(54)

        elif scope == "TF":
            if self.temporary_frame is None:
                print("Error: Temporary frame is not defined.", file=sys.stderr)
                sys.exit(55)

            try:
                self.temporary_frame.update_var(identifier, value)
            except KeyError:
                print("interpret.py:", order, ": Variable", identifier, "doesn't exist.")
                sys.exit(54)

    def get_var(self, name, order):
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            try:
                retval = self.global_frame.get_var(identifier)
            except KeyError:
                print("interpret.py:", order, ": Variable", identifier, "doesn't exist in the global frame.",
                      file=sys.stderr)
                sys.exit(54)

            return retval

        elif scope == "TF":
            if self.temporary_frame is None:
                print("interpret.py:", order, ": Temporary frame is not defined.", file=sys.stderr)
                sys.exit(55)

            try:
                retval = self.temporary_frame.get_var(identifier)
            except KeyError:
                print("interpret.py:", order, ": Variable", identifier, "doesn't exist in the temporary frame.",
                      file=sys.stderr)
                sys.exit(54)

            return retval

        elif scope == "LF":
            try:
                retval = self.local_frame_stack[-1].get_var(identifier)
            except KeyError:
                print("Error: Variable", identifier, "doesn't exist in this local frame.", file=sys.stderr)
                sys.exit(54)
            except IndexError:
                print("Error: Local frame stack is empty.", file=sys.stderr)
                sys.exit(55)

            return retval
        else:
            print("Error: Unrecognized scope.", file=sys.stderr)
            sys.exit(55)

    def push_temp(self):
        if self.temporary_frame is None:
            print("Error: Temporary frame is not defined.", file=sys.stderr)
            sys.exit(55)

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

    def set_var(self, identifier):
        self.vars[identifier] = Variable()

    def update_var(self, identifier, value):
        try:
            self.vars[identifier].set_value(value)
        except KeyError:
            raise

    def get_var(self, identifier):
        try:
            retval = self.vars[identifier]
        except KeyError:
            raise

        return retval


class Variable:
    def __init__(self):
        self.value = ""
        self.type = "undefined"

    def set_value(self, value):
        self.value = value
        if isinstance(value, str):
            self.type = "string"

        if isinstance(value, int):
            self.type = "int"

        if value in {"bool@true", "bool@false"}:
            self.type = "bool"

        if value is "nil@nil":
            self.type = "nil"

    def get_type(self):
        if self.type == "var":
            if isinstance(self.value, str):
                self.type = "string"

            if isinstance(self.value, int):
                self.type = "int"

            if isinstance(self.value, bool):
                self.type = "bool"

            if self.value is None:
                self.type = "nil"
        else:
            return self.type

    def get_value(self):
        return self.value


def decode_escapes(s):
    '''Helper function that reverses escaping done by xml.etree

    Obtained from: https://stackoverflow.com/a/24519338
    '''
    escape_sequence_re = re.compile(r'\\[0-9]{3}', re.UNICODE | re.VERBOSE)

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return escape_sequence_re.sub(decode_match, s)


class Program:
    def __init__(self, parsed_xml):
        self.elem_program = parsed_xml  # Root element program as Element from ElementTree
        self.instructions = {}          # Dictionary of instructions - keys are their order values (iterate sorted)
        self.labels = {}                # Index names are labels and keys are instruction order values
        self.name = None
        self.description = None
        self.frameset = FrameSet()
        self.callstack = []             # List of return indices from call instructions to return instructions

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
                print("interpret.py:", idx, "(in document order): Order attribute contains an invalid value.",
                      file=sys.stderr)
                sys.exit(32)

            if order < 1:
                print("interpret.py:", order, ": Order attribute is not bigger than 0.", file=sys.stderr)
                sys.exit(32)

            ## Get opcode
            try:
                opcode = instruction_attr.pop("opcode").upper()
            except KeyError:
                print("interpret.py:", order, ": Undefined opcode attribute in instruction ", order, '.', file=sys.stderr)
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

                ## Element without text returns has text set to None - treating here
                arg_text = decode_escapes(argument.text)
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

    def execute(self):
        for instruction_key in self.instructions.keys():
            # Passing program instance because instructions need to change frames, variables, etc.
            self.instructions[instruction_key].execute(self)


class Instruction:
    """Instruction representation

       Implements
    """

    accepted_const = {"int", "bool", "string", "nil"}

    def __init__(self, order, name, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type):
        """Instruction constructor

           Takes
        """
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

        self.check_arg_syntax()

    def check_arg_syntax(self):
        pass

    def read_var(self, program_instance, arg_idx, order):
        retval = program_instance.frameset.get_var(self.argv[arg_idx], order)
        if retval.type == "undefined":
            print("Error: Variable", self.argv[arg_idx], "is undefined.", file=sys.stderr)
            exit(56)

        retval = retval.value

        return retval

    def read_symb(self, program_instance, arg_idx, order):
        '''Helper function that reads expected symbol argument

           @program_instance Instance of a program class - for getting variables
           @arg_idx Index of the desired argument (1-3)
           @return Value of a variable or a constant
        '''
        arg_idx = arg_idx - 1
        retval = ""
        if self.arg_types[arg_idx] == "var":
            retval = self.read_var(program_instance, arg_idx, order)
        elif self.arg_types[arg_idx] in self.accepted_const:
            retval = self.argv[arg_idx]

            if self.arg_types[arg_idx] == "int":
                retval = int(retval)

            if self.arg_types[arg_idx] == "nil":
                retval = None

            if self.arg_types[arg_idx] == "bool":
                if retval == "true":
                    retval = True

                if retval == "false":
                    retval = False

        return retval

    def execute(self, program_instance):
        """Interpretation caller

           This function calls instr_* functions that do the actual interpretation. Every instruction is independent,
           so they can be executed separately.

           @arg program_instance program instance is passed because some instructions change the control flow or modify
                                 its member variables (e.g. frame stack)
        """
        eval("self.instr_" + self.name.lower() + "(program_instance)")

    # 0 ARGUMENTS
    def instr_createframe(self, program_instance):
        program_instance.frameset.init_temporary_frame()

    def instr_pushframe(self, program_instance):
        program_instance.frameset.push_temp()

    def instr_popframe(self, program_instance):
        program_instance.frameset.pop_local()

    def instr_return(self, program_instance):
        pass

    def instr_break(self, program_instance):
        pass

    # 1 ARGUMENT
    def instr_defvar(self, program_instance):
        program_instance.frameset.set_var(self.argv[0])

    def instr_call(self, program_instance):
        pass

    def instr_pushs(self, program_instance):
        pass

    def instr_pops(self, program_instance):
        pass

    def instr_write(self, program_instance):
        retval = self.read_symb(program_instance, 1, self.order)

        if retval is True:
            retval = "bool@true"

        if retval is False:
            retval = "bool@false"

        if retval is None:
            retval = "nil@nil"

        print(retval, end='')

    def instr_label(self, program_instance):
        pass

    def instr_jump(self, program_instance):
        pass

    def instr_exit(self, program_instance):
        pass

    def instr_dprint(self, program_instance):
        pass

    # 2 ARGUMENTS
    def instr_move(self, program_instance):
        value = self.read_symb(program_instance, 2, self.order)
        program_instance.frameset.update_var(self.argv[0], value, self.order)

    def instr_int2char(self, program_instance):
        pass

    def instr_read(self, program_instance):
        pass

    def instr_strlen(self, program_instance):
        pass

    def instr_type(self, program_instance):
        pass

    # 3 ARGUMENTS
    def instr_add(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 + arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Variable must be of type int.", file=sys.stderr)
            exit(53)

    def instr_sub(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 - arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Variable must be of type int.", file=sys.stderr)
            exit(53)

    def instr_mul(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 * arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Variable must be of type int.", file=sys.stderr)
            exit(53)

    def instr_idiv(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            if arg3 == 0:
                print("interpret.py:", self.order, ": Division by zero.", file=sys.stderr)
                exit(57)

            result = arg2 + arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Variable must be of type int.", file=sys.stderr)
            exit(53)

    def instr_lt(self, program_instance):
        pass

    def instr_gt(self, program_instance):
        pass

    def instr_eq(self, program_instance):
        pass

    def instr_and(self, program_instance):
        pass

    def instr_or(self, program_instance):
        pass

    def instr_not(self, program_instance):
        pass

    def instr_stri2int(self, program_instance):
        pass

    def instr_concat(self, program_instance):
        pass

    def instr_getchar(self, program_instance):
        pass

    def instr_setchar(self, program_instance):
        pass

    def instr_jumpifeq(self, program_instance):
        pass

    def instr_jumpifneq(self, program_instance):
        pass


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
        try:
            xml_root = xml_et.parse(source_file).getroot()
        except xml_et.ParseError:
            print("Error: Malformed XML.", file=sys.stderr)
            sys.exit(31)

        program = Program(xml_root)
else:
    # Reading code from stdin (source arg not set)
    source = sys.stdin.read()
    try:
        xml_root = xml_et.fromstring(source)
    except xml_et.ParseError:
        print("Error: Malformed XML.", file=sys.stderr)
        sys.exit(31)

    program = Program(xml_root)

# Now we have a program instance with instructions
program.extract_instructions()

# Start the interpreter
program.execute()

exit(0)
