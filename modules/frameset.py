from copy import deepcopy
import getopt
import itertools
import sys
import re
import xml.etree.ElementTree as xml_et
import codecs

import modules.variables as variables

class FrameSet:
    '''Holds all frames

       This class implements global and temporary frame. It also contains local frame stack. Frames are implemented as
       separate classes. Global frame is the only defined frame at program start.
    '''
    def __init__(self):
        '''Frameset constructor

           Initializes global frame and creates empty local frame stack and undefined temporary frame.
        '''
        self.local_frame_stack = []
        self.global_frame = {}
        self.temporary_frame = None

    def init_temporary_frame(self):
        '''Initializes the temporary frame

            Creates a new instance of a temporary frame. Rewrites the existing temporary frame.
        '''
        self.temporary_frame = {}

    def define_var(self, name):
        '''Defines a variable

           Creates an empty variable on a frame defined in variable's name. This function calls a function with the
           same name defined in class frame.
           @param name Name of variable in format (TF|LF|GF)@<var_name>
        :return:
        '''
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            frame = self.global

        elif scope == "TF":
            if self.temporary_frame is None:
                print("interpret.py: Temporary frame is not defined.", file=sys.stderr)
                sys.exit(55)
            else:
                frame = self.temporary_frame


        elif scope == "LF":
            try:
                frame = self.local_frame_stack[-1]
            except IndexError:
                print("interpret.py: Local frame stack is empty.", file=sys.stderr)
                sys.exit(55)

        else:
            print("interpret.py: Unrecognized scope.", file=sys.stderr)
            sys.exit(55)

        # And now create a variable on that frame
        try:
            frame[identifier]
        except KeyError:
            frame[identifier] = variables.Variable()
            return

        raise KeyError

    def update_var(self, name, value):
        '''Change value of a variable

           Changes value of a variable on the frame defined in variable's name. Any value is supported, current type
           of variable is unimportant.
           @TODO Change value to accept Pythonic value, raise exceptions
           @param name Name of variable in format (TF|LF|GF)@<var_name>
           @param value Value to be written to the variable (in IPPcode19 syntax)
        '''
        exploded = name.split('@', maxsplit=1)
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

    def get_var(self, name):
        '''Get variable's value

           Function returns an instance of class Variable that was created during parsing and it's saved in the frame
           defined in variable's name.
           @param name Name of variable in format (TF|LF|GF)@<var_name>
           @param order Order tag of the invoking instruction - used for error reporting
           @return Variable instance of class Variable
        '''
        exploded = re.split(r'@', name, maxsplit=1)
        scope = exploded[0]
        identifier = exploded[1]

        if scope == "GF":
            try:
                retval = self.global_frame.vars[identifier]
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
        '''Places temporary frame on top of local frame stack

           Copies the temporary frame to the top of the local frame stack. Variable names donþt need to be updated,
           as they are stored without a frame name.
           @param order Order tag of the invoking instruction - used for error reporting
        '''
        if self.temporary_frame is None:
            print("interpret.py:", order, ": Temporary frame is not defined.", file=sys.stderr, sep='')
            sys.exit(55)

        temp_copy = deepcopy(self.temporary_frame)
        self.local_frame_stack.append(temp_copy)
        self.temporary_frame = None

    def pop_local(self, order):
        '''Pops local frame into the temporary frame

           Takes the top local frame and replaces the temporary frame with it.
           @param order Order tag of the invoking instruction - used for error reporting
        '''
        try:
            self.temporary_frame = self.local_frame_stack.pop()
        except IndexError:
            print("interpret.py:", order, ": Local frame stack is empty.", file=sys.stderr, sep='')
            sys.exit(55)
