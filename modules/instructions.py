import itertools
import sys
import re
import

class Instruction:
    """Instruction representation

       Implements the instruction syntax checking and the actual implementation of every instruction in methods instr_*.
    """

    accepted_const = {"int", "bool", "string", "nil"}  # Strings that are accepted as type

    def __init__(self, order, program_ref, name, arg_dict):
        """Instruction constructor

           Takes the order tag for error reporting, opcode and arguments along with types from the XML.
           @TODO Pass args as a list of pairs [[value1, type1],...]
        """
        self.program = program_ref
        self.order = order
        self.name = name
        self.argv = []
        self.arg_types = []
        for arg in arg_dict:
            self.argv.append(arg)

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

        self.check_arg_syntax()

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
                    sys.exit(32)
            # Repairing escape sequences that have escaped backslashes by xml.etree (has to be done after syntax check)
            if arg_type == "string":
                self.argv[arg_num - 1] = decode_escapes(self.argv[arg_num - 1])



    def check_arg_syntax(self):
        '''Performs syntax checking on symbols

           Checks syntax of constant values and variable names. Variables are not checked on runtime.
        '''

        def check_var(var):
            '''Helper for function check_arg_syntax - checks variable.

               @returns true if values match types or value of incorrect operand.
            '''
            if re.fullmatch(r"(GF|TF|LF)@([a-zA-Z]|[_\-$&%*])[\w\-$&%*]*", var) is None:
                print("interpret.py:", self.order, ": Variable/constant ", var, " has incorrect syntax.",
                      file=sys.stderr, sep='')
                sys.exit(32)

        def check_symb(symb):
            '''Helper for function check_arg_syntax - checks symbols.

               @returns True if values match types or value of incorrect operand.
            '''
            # Can represent variable or constant
            # Checking format of an immediate value - string, int, bool

            if re.fullmatch(r"([^#\\]|(\w)|(\\[0-9]{3}))*", symb) is not None or \
               re.fullmatch(r"[+-]?[0-9]+", symb) is not None or \
               re.fullmatch(r"true|false", symb) is not None or \
               re.fullmatch(r"nil", symb) is not None:
                pass
            else:
                check_var(symb)

        def check_label(label):
            '''Helper for function check_arg_syntax - checks label.

               @returns true if values match types or value of incorrect operand.
            '''

            if re.fullmatch(r"[_\-$&%*](\w|[\-$&%*])*", label) is None:
                print("interpret.py:", self.order, ": Label ", label, " has incorrect syntax.",
                      file=sys.stderr, sep='')
                sys.exit(32)

        def check_type(v_type):
            '''Helper for function check_arg_syntax - checks data type name.

               @returns True if values match types or value of incorrect operand.
            '''
            if v_type == "string" or v_type == "int" or v_type == "bool":
                return True
            else:
                print("interpret.py:", self.order, ": Type ", type, " is not recognized.",
                      file=sys.stderr, sep='')
                sys.exit(32)

        # Resolve which function to call based on expected_type
        for arg, exp_type in itertools.zip_longest(self.argv, self.expected_arg_types):
            if exp_type == "label":
                return check_label(arg)
            elif exp_type == "var":
                return check_var(arg)
            elif exp_type == "symb":
                return check_symb(arg)
            elif exp_type == "type":
                return check_type(arg)

    def read_var(self, program_instance, arg_idx, order):
        '''Get value of a variable

           Gets the value of a variable on runtime. Checks if it's defined otherwise raises an error.
           @param program_instance Instance of a program (to access variables)
           @param arg_idx Selects variable from given argument index (1-3)
           @param order Order tag of invoking instruction (for error reporting)
           @return Pythonic variable value
        '''
        arg_idx = arg_idx - 1
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
                try:
                    retval = int(retval)
                except ValueError:
                    print("interpret.py:", self.order, ": Argument ", arg_idx + 1, " is not an integer.",
                          file=sys.stderr, sep='')
                    sys.exit(52)

            if self.arg_types[arg_idx] == "nil" and self.argv[arg_idx] == "nil":
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
        try:
            program_instance.frameset.set_var(self.argv[0])
        except KeyError:
            print("interpret.py:", self.order, ": Label ", self.argv[0], " doesn't exist.",
                  file=sys.stderr, sep='')
            sys.exit(52)

    def instr_call(self, program_instance):
        program_instance.callstack.append(program_instance.order_next)
        try:
            jumpto = program_instance.labels[self.argv[0]]
        except KeyError:
            print("interpret.py:", self.order, ": Label ", self.argv[0], " doesn't exist.",
                  file=sys.stderr, sep='')
            sys.exit(52)
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
        if program_instance.stdin_file is not None:
            text = program_instance.stdin_file.readline()
            if text != "\n":
                # Not stripping "\n" because this is an empty line. When EOF is reached, "" is returned,
                # so it'd also interfere
                text = text[:-1]
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
