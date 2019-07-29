from copy import deepcopy
import getopt
import itertools
import sys
import re
import xml.etree.ElementTree as xml_et
import codecs

import modules.frameset as frameset
import modules.instructions as instr


class Program:
    '''Program class

       Program class holds instructions parsed from the xml. To handle jumps, it contains dictionary of labels - keys
       are labels and values are instruction jump tags. Method execute is used as main loop of the interpreter, so
       frameset and subsequently frames and variables are stored here for easy access. Member variables order_next
       and order_jumpto are used to interchange order tags when instructions change control flow - this is a result
       of flawed design.
    '''
    def __init__(self, parsed_xml):
        '''Program constructor

           Creates a new program instance.
           @param parsed_xml Used to pass ElementTree created by the XML parser
        '''
        self.elem_program = parsed_xml       # Root element program as Element from ElementTree
        self.instructions = {}               # Dictionary of instructions - keys are their order values (iterate sorted)
        self.labels = {}                     # Index names are labels and keys are instruction order values
        self.name = None                     # DEPRECATED: Value of attribute name in element program
        self.description = None              # DEPRECATED: Value of attribute description in element program
        self.frameset = frameset.FrameSet()  # Frameset instance taht contains frames and variables
        self.callstack = []                  # List of return indices from call instructions to return instructions
        self.order_next = None               # For passing values to callstack (remembers last next instruction)
        self.order_jumpto = None             # For passing values from jump instructions to execution loop
        self.stdin_file = None               # A file object that contains a file when --input argument was given

    def set_input(self, stdin_file):
        '''Input file

           Saves a file object with inputs for READ instructions so it can be easily accessed.
           @param stdin_file A file object with inputs for READ instruction
        '''
        self.stdin_file = stdin_file

    def extract_instructions(self):
        '''XML parser and checker

           This method reads the ElementTree and checks that is syntactically correct. This implementation supports
           instructions out-of-order and with non-following order attributes. XML should strictly follow the specifi-
           cation, invalid values and unsupported elements raise an error. XML comments are allowed.
        '''
        # Check program attributes
        program_attr = self.elem_program.attrib
        ## Language attribute
        try:
            language = program_attr.pop("language")
        except KeyError:
            print("interpret.py: Program element is missing a language attribute.", file=sys.stderr)
            sys.exit(32)
        if language.lower() != "ippcode19":
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
            allowed_arg_tags = ['arg1', 'arg2', 'arg3']
            arg_dict = {}
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

                # Check attribute type and convert to lowercase

                ## Element without text has text set to None - treating here
                arg_text = argument.text
                if arg_text is None:
                    arg_text = ""

                # Insert argument and type into the instruction
                arg_dict[argument.tag] = (arg_text, attr_type)

                # Build label dictionary
                if opcode == "LABEL":
                    self.labels[arg_dict["arg1"]] = order

            self.instructions[order] = instr.Instruction(order, self, opcode, arg_dict)
            #TODO? Deal with duplicate order tags

    def execute(self):
        '''Main interpreter loop

           This method implements executing the instructions in the interpreter.
        '''
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


def decode_escapes(s):
    '''Helper function that reverses escaping done by xml.etree

       Ideas from https://stackoverflow.com/a/24519338 and https://stackoverflow.com/a/21301416
       @param s String to be unescaped
       @return Unescaped string
       @pre String cannot be empty
    '''
    escape_sequence_re = re.compile(r'\\([0-9]{3})', re.UNICODE | re.VERBOSE)

    def decode_match(match):
        return codecs.decode(chr(int(match.group(1))), 'unicode-escape', 'ignore')

    return escape_sequence_re.sub(decode_match, s)
