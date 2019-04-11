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
                print("interpret.py: Temporary frame is not defined.", file=sys.stderr)
                sys.exit(55)

            self.temporary_frame.set_var(identifier)

        elif scope == "LF":
            try:
                self.local_frame_stack[-1].set_var(identifier)
            except IndexError:
                print("interpret.py: Local frame stack is empty.", file=sys.stderr)
                sys.exit(55)

        else:
            print("interpret.py: Unrecognized scope.", file=sys.stderr)
            sys.exit(55)

    def update_var(self, name, value, order):
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            try:
                self.global_frame.update_var(identifier, value)
            except KeyError:
                print("interpret.py:", order, ": Variable ", identifier, " doesn't exist.", file=sys.stderr, sep='')
                sys.exit(54)

        elif scope == "TF":
            if self.temporary_frame is None:
                print("interpret.py:", order, ": Temporary frame is not defined.", file=sys.stderr, sep='')
                sys.exit(55)

            try:
                self.temporary_frame.update_var(identifier, value)
            except KeyError:
                print("interpret.py:", order, ": Variable ", identifier, " doesn't exist.", file=sys.stderr, sep='')
                sys.exit(54)

        elif scope == "LF":
            try:
                self.local_frame_stack[-1].update_var(identifier, value)
            except IndexError:
                print("interpret.py:", order, ": Local frame stack is empty.", file=sys.stderr, sep='')
                sys.exit(55)
            except KeyError:
                print("interpret.py:", order, ": Variable ", identifier, " doesn't exist.", file=sys.stderr, sep='')
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
                print("interpret.py:", order, ": Variable ", identifier, " doesn't exist in the temporary frame.",
                      file=sys.stderr, sep='')
                sys.exit(54)

            return retval

        elif scope == "LF":
            try:
                retval = self.local_frame_stack[-1].get_var(identifier)
            except KeyError:
                print("interpret.py:", order, ": Variable ", identifier, " doesn't exist in this local frame.",
                      file=sys.stderr, sep='')
                sys.exit(54)
            except IndexError:
                print("interpret.py:", order, ": Local frame stack is empty.", file=sys.stderr, sep='')
                sys.exit(55)

            return retval
        else:
            print("interpret.py:", order, ": Unrecognized scope.", file=sys.stderr, sep='')
            sys.exit(55)

    def push_temp(self, order):
        if self.temporary_frame is None:
            print("interpret.py:", order, ": Temporary frame is not defined.", file=sys.stderr, sep='')
            sys.exit(55)

        temp_copy = deepcopy(self.temporary_frame)
        self.local_frame_stack.append(temp_copy)
        self.temporary_frame = None

    def pop_local(self, order):
        try:
            self.temporary_frame = self.local_frame_stack.pop()
        except IndexError:
            print("interpret.py:", order, ": Local frame stack is empty.", file=sys.stderr, sep='')
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

       Ideas from https://stackoverflow.com/a/24519338 and https://stackoverflow.com/a/21301416
    '''
    escape_sequence_re = re.compile(r'\\([0-9]{3})', re.UNICODE | re.VERBOSE)

    def decode_match(match):
        return codecs.decode(chr(int(match.group(1))), 'unicode-escape')

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
        self.order_next = None          # For passing values to callstack (remembers last next instruction)
        self.order_jumpto = None        # For passing values from jump instructions to execution loop
        self.stdin_file = None          # A file object that contains a file when --input argument was given

    def set_input(self, stdin_file):
        self.stdin_file = stdin_file

    def extract_instructions(self):
        # Check program attributes
        program_attr = self.elem_program.attrib
        ## Language attribute
        try:
            language = program_attr.pop("language")
        except KeyError:
            print("interpret.py: Program element is missing a language attribute.", file=sys.stderr)
            sys.exit(32)
        if language != "IPPcode19":
            print("interpret.py: Program element contains an incorrect language attribute.", file=sys.stderr)
            sys.exit(32)
        ## Test for allowed attributes
        allowed_program_attr = {"language", "name", "description"}
        for program_attr in program_attr.keys():
            if program_attr not in allowed_program_attr:
                print("interpret.py: Invalid attribute in the program element.", file=sys.stderr)
                sys.exit(32)

        # Checking instructions
        for (idx, instruction) in enumerate(self.elem_program.findall("*"), start=1):
            # No instruction elements
            if instruction is None:
                print("interpret.py: No instruction elements found.", file=sys.stderr)
                sys.exit(32)

            # Check that only children are instruction elements
            if instruction.tag != "instruction":
                print("interpret.py: Invalid child element in the program element.", file=sys.stderr)
                sys.exit(32)

            # Extracting instruction attributes
            instruction_attr = instruction.attrib
            ## Get order number
            try:
                order = instruction_attr.pop("order")
            except KeyError:
                print("interpret.py:", idx, ": Undefined order attribute. (Order of element in document is "
                      "provided here)", file=sys.stderr, sep='')
                sys.exit(32)
            ### Convert to int and check value
            try:
                order = int(order)
            except ValueError:
                print("interpret.py:", idx, ": Order attribute contains an invalid value. (Order of element in "
                      "document is provided here)", file=sys.stderr, sep='')
                sys.exit(32)

            ## Get opcode
            try:
                opcode = instruction_attr.pop("opcode").upper()
            except KeyError:
                print("interpret.py:", order, ": Undefined opcode attribute in instruction ", order, '.',
                      file=sys.stderr, sep='')
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
                    print("interpret.py:", order, ": Too many, duplicate arguments or unrecognized child elements.",
                          file=sys.stderr, sep='')
                    sys.exit(32)

                # Checking argument attributes
                arg_attr = argument.attrib
                try:
                    attr_type = arg_attr.pop("type")
                except KeyError:
                    print("interpret.py:", order, ": Attribute type is missing.",
                          file=sys.stderr, sep='')
                    sys.exit(32)

                ## Element without text returns has text set to None - treating here
                arg_text = argument.text
                if arg_text is None:
                    arg_text = ""
                else:
                    # Repairing escape sequences that have escaped backslashes by xml.etree
                    arg_text = decode_escapes(arg_text)

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

                # Build label dictionary
                if opcode == "LABEL":
                    self.labels[arg1] = order

            self.instructions[order] = Instruction(order, opcode, arg1, arg2, arg3, arg1_type, arg2_type, arg3_type)

    def execute(self):
        instruction_keys = sorted(self.instructions.keys())
        instruction_key = min(instruction_keys)
        end = True

        while end:
            # Find next instruction key (can be bigger than +1) in case that call instruction is called
            try:
                self.order_next = instruction_keys[instruction_keys.index(instruction_key) + 1]
            except IndexError:
                end = False

            # Passing program instance because instructions need to change frames, variables, etc.
            self.instructions[instruction_key].execute(self)

            if self.order_jumpto is None:
                # Update instruction key with original next value
                instruction_key = self.order_next
            else:
                # Jump/return instruction was performed, next order is determined by order_jumpto
                instruction_key = self.order_jumpto
                self.order_jumpto = None


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
            print("interpret.py:", order, ": Unknown instruction name.", file=sys.stderr, sep='')
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
                    print("interpret.py:", self.order, ": Argument ", arg_num, " in instruction has incorrect type.",
                          file=sys.stderr, sep='')
                    sys.exit(52)

        self.check_arg_syntax()

    def check_arg_syntax(self):
        pass

    def read_var(self, program_instance, arg_idx, order):
        retval = program_instance.frameset.get_var(self.argv[arg_idx], order)
        if retval.type == "undefined":
            print("interpret.py:", self.order, ": Variable", self.argv[arg_idx], "is undefined.",
                  file=sys.stderr, sep='')
            sys.exit(56)

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
        program_instance.frameset.push_temp(self.order)

    def instr_popframe(self, program_instance):
        program_instance.frameset.pop_local(self.order)

    def instr_return(self, program_instance):
        try:
            jumpto = program_instance.callstack.pop()
        except IndexError:
            print("interpret.py:", self.order, ": Can't return, call stack is empty.",
                  file=sys.stderr, sep='')
            sys.exit(56)
        program_instance.order_jumpto = jumpto

    def instr_break(self, program_instance):
        print("Code position (from order attribute):", self.order, file=sys.stderr)
        print("GLOBAL FRAME:", file=sys.stderr)
        for name, value in program_instance.frameset.global_frame.vars.items():
            print("GF@", name, ": ", value, file=sys.stderr, sep='')
        print(file=sys.stderr)
        print("TEMPORARY FRAME:", file=sys.stderr)
        if program_instance.frameset.temporary_frame is None:
            print("Undefined", file=sys.stderr)
        else:
            for name, value in program_instance.frameset.global_frame.vars.items():
                print("TF@", name, ": ", value, file=sys.stderr, sep='')
        print(file=sys.stderr)

        frames_under = len(program_instance.frameset.local_frame_stack) - 1
        print("LOCAL FRAME:", file=sys.stderr)
        if frames_under < 0:
            print("Undefined", file=sys.stderr)
        else:
            print("Top frame (on top of", frames_under, "frames):", file=sys.stderr)
            local_frame = program_instance.frameset.local_frame_stack[-1]
            for name, value in local_frame.items():
                print("TF@", name, ": ", value, file=sys.stderr, sep='')

    # 1 ARGUMENT
    def instr_defvar(self, program_instance):
        program_instance.frameset.set_var(self.argv[0])

    def instr_call(self, program_instance):
        program_instance.callstack.append(program_instance.order_next)
        try:
            jumpto = program_instance.labels[self.argv[0]]
        except KeyError:
            print("interpret.py:", self.order, ": Label ", self.argv[0], " doesn't exist.",
                  file=sys.stderr, sep='')
            sys.exit(57)
        program_instance.order_jumpto = jumpto

    def instr_pushs(self, program_instance):
        # UNSUPPORTED
        pass

    def instr_pops(self, program_instance):
        # UNSUPPORTED
        pass

    def instr_write(self, program_instance):
        retval = self.read_symb(program_instance, 1, self.order)

        if retval is True:
            retval = "true"

        if retval is False:
            retval = "false"

        if retval is None:
            retval = "nil"

        print(retval, end='')

    def instr_label(self, program_instance):
        # DO NOTHING
        pass

    def instr_jump(self, program_instance):
        try:
            jumpto = program_instance.labels[self.argv[0]]
        except KeyError:
            print("interpret.py:", self.order, ": Label", self.argv[0], " doesn't exist.",
                  file=sys.stderr, sep='')
            sys.exit(57)
        program_instance.order_jumpto = jumpto

    def instr_exit(self, program_instance):
        retval = self.read_symb(program_instance, 1, self.order)
        if retval < 0 or retval > 49:
            print("interpret.py:", self.order, ": Invalid exit code.",
                  file=sys.stderr, sep='')
            sys.exit(57)

        sys.exit(retval)

    def instr_dprint(self, program_instance):
        print(self.read_symb(program_instance, 1, self.order), end='', file=sys.stderr)

    # 2 ARGUMENTS
    def instr_move(self, program_instance):
        value = self.read_symb(program_instance, 2, self.order)
        program_instance.frameset.update_var(self.argv[0], value, self.order)

    def instr_int2char(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        if isinstance(arg2, int):
            try:
                result = chr(arg2)
            except ValueError:
                print("interpret.py:", self.order, ": Argument 1 out of range - not a Unicode value.",
                      file=sys.stderr, sep='')
                sys.exit(58)
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last argument must be of type string.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_read(self, program_instance):
        if program_instance.stdin_file is not False:
            text = program_instance.stdin_file.readline()
            if text != "\n":
                # Not stripping "\n" because this is an empty line. When EOF is reached, "" is returned,
                # so it'd also interfere
                text.strip('\n')
        else:
            try:
                text = input()
            except EOFError or UnicodeError:
                text = ""

        # Text conversion
        # Save implicit value when text == ""
        type = self.argv[1]
        if type == "int":
            # Error string "" will also fail conversion, no need for separate if clause
            try:
                converted_int = int(text)
            except ValueError:
                converted_int = 0
            program_instance.frameset.update_var(self.argv[0], converted_int, self.order)
        elif type == "bool":
            if text == "":
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
            else:
                if text.lower() == "true":
                    program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
                elif text.lower() == "false":
                    program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
                else:
                    # Implicit value when conversion is unsuccessful
                    program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        elif type == "string":
            # Implicit value is the same as error value
            program_instance.frameset.update_var(self.argv[0], text, self.order)
        else:
            print("interpret.py:", self.order, ": Variable ", self.argv[0], " is undefined.",
                  file=sys.stderr, sep='')
            sys.exit(56)

    def instr_strlen(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        if isinstance(arg2, str):
            result = len(arg2)
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last argument must be of type string.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_type(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        if self.arg_types[1] == "var":
            result = program_instance.frameset.get_var(arg2, self.order).get_type()
            if result == "undefined":
                result = ""
        else:
            result = self.arg_types[1]

        program_instance.frameset.update_var(self.argv[0], result, self.order)

    def instr_not(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        if isinstance(arg2, bool):
            result = not arg2
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool or string.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    # 3 ARGUMENTS
    def instr_add(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 + arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_sub(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 - arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_mul(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            result = arg2 * arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_idiv(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, int) and isinstance(arg3, int):
            if arg3 == 0:
                print("interpret.py:", self.order, ": Division by zero.", file=sys.stderr, sep='')
                sys.exit(57)

            result = arg2 + arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_lt(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if (isinstance(arg2, int) and isinstance(arg3, int)) or \
           (isinstance(arg2, str) and isinstance(arg3, str)) or \
           (isinstance(arg2, bool) and isinstance(arg3, bool)):
            result = arg2 < arg3
            if result is True:
                program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
            else:
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool or string.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_gt(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if (isinstance(arg2, int) and isinstance(arg3, int)) or \
           (isinstance(arg2, str) and isinstance(arg3, str)) or \
           (isinstance(arg2, bool) and isinstance(arg3, bool)):
            result = arg2 > arg3
            if result is True:
                program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
            else:
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool or string.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_eq(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if (isinstance(arg2, int) and isinstance(arg3, int)) or \
           (isinstance(arg2, str) and isinstance(arg3, str)) or \
           (isinstance(arg2, bool) and isinstance(arg3, bool)) or \
           (arg2 is None and arg3 is None):
            result = arg2 == arg3
            if result is True:
                program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
            else:
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool, string or nil.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_and(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, bool) and isinstance(arg3, bool):
            result = arg2 and arg3
            if result is True:
                program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
            else:
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type bool.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_or(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, bool) and isinstance(arg3, bool):
            result = arg2 or arg3
            if result is True:
                program_instance.frameset.update_var(self.argv[0], "bool@true", self.order)
            else:
                program_instance.frameset.update_var(self.argv[0], "bool@false", self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type bool.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_stri2int(self, program_instance):
        string = self.read_symb(program_instance, 2, self.order)
        idx = self.read_symb(program_instance, 3, self.order)
        if isinstance(string, str) and isinstance(idx, int):
            try:
                result = ord(string[idx])
            except IndexError:
                print("interpret.py:", self.order, ": Last 2 arguments must be of type string.",
                      file=sys.stderr, sep='')
                sys.exit(58)
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type string.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_concat(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if isinstance(arg2, str) and isinstance(arg3, str):
            result = arg2 + arg3
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type string.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_getchar(self, program_instance):
        string = self.read_symb(program_instance, 2, self.order)
        idx = self.read_symb(program_instance, 3, self.order)
        if isinstance(string, str) and isinstance(idx, int):
            try:
                result = string[idx]
            except IndexError:
                print("interpret.py:", self.order, ": Last 2 arguments must be of type string.",
                      file=sys.stderr, sep='')
                sys.exit(58)
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type string.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_setchar(self, program_instance):
        string = self.read_var(program_instance, 1, self.order)
        idx = self.read_symb(program_instance, 2, self.order)
        char = self.read_symb(program_instance, 3, self.order)
        if isinstance(string, str) and isinstance(idx, int) and isinstance(char, str):
            try:
                result = string[:idx-1] + char[0] + string[idx:]
            except IndexError:
                print("interpret.py:", self.order, ": Last 2 arguments must be of type string and last string must be "
                      "non-empty.", file=sys.stderr, sep='')
                sys.exit(58)
            program_instance.frameset.update_var(self.argv[0], result, self.order)
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type string.", file=sys.stderr, sep='')
            sys.exit(53)

    def instr_jumpifeq(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if (isinstance(arg2, int) and isinstance(arg3, int)) or \
           (isinstance(arg2, str) and isinstance(arg3, str)) or \
           (isinstance(arg2, bool) and isinstance(arg3, bool)) or \
           (arg2 is None and arg3 is None):
            result = arg2 == arg3
            if result is True:
                try:
                    jumpto = program_instance.labels[self.argv[0]]
                except KeyError:
                    print("interpret.py:", self.order, ": Label", self.argv[0], " doesn't exist.",
                          file=sys.stderr, sep='')
                    sys.exit(57)
                program_instance.order_jumpto = jumpto
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool, string or nil.",
                  file=sys.stderr, sep='')
            sys.exit(53)

    def instr_jumpifneq(self, program_instance):
        arg2 = self.read_symb(program_instance, 2, self.order)
        arg3 = self.read_symb(program_instance, 3, self.order)
        if (isinstance(arg2, int) and isinstance(arg3, int)) or \
           (isinstance(arg2, str) and isinstance(arg3, str)) or \
           (isinstance(arg2, bool) and isinstance(arg3, bool)) or \
           (arg2 is None and arg3 is None):
            result = arg2 == arg3
            if result is False:
                try:
                    jumpto = program_instance.labels[self.argv[0]]
                except KeyError:
                    print("interpret.py:", self.order, ": Label", self.argv[0], " doesn't exist.",
                          file=sys.stderr, sep='')
                    sys.exit(57)
                program_instance.order_jumpto = jumpto
        else:
            print("interpret.py:", self.order, ": Last 2 arguments must be of type int, bool, string or nil.",
                  file=sys.stderr, sep='')
            sys.exit(53)


class Args:
    def __init__(self):
        self.source_file = False
        self.input_file = False
        self.help = False

    def parse(self):
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


"""
SCRIPT EXECUTION POINT
"""
args = Args()
args.parse()
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
    program = Program(xml_root)
else:
    # Reading code from stdin (source arg not set)
    source = sys.stdin.read()
    try:
        xml_root = xml_et.fromstring(source)
    except xml_et.ParseError:
        print("interpret.py: Malformed XML.", file=sys.stderr)
        sys.exit(31)

    program = Program(xml_root)

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

# Close the input file
if program.stdin_file is not None:
    program.stdin_file.close()

sys.exit(0)
