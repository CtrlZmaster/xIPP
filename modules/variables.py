from copy import deepcopy
import getopt
import itertools
import sys
import re
import xml.etree.ElementTree as xml_et
import codecs


class Variable:
    '''Class implementing variable

       This class doesn't conatin the variable's name - itþs stored as the key in variable dictionary that is defined
       in a frame. It stores variable's value and type - IPPcode19 supports dynamic typing.
    '''
    def __init__(self):
        '''Variable constructor

           Undefined variable has empty string value when undefined. The fact that is undefined is stored in the type
           as "undefined". Types can be int, string, bool and nil. They are changed dynamically when the value changes.
           Value is stored as a Python variable - not in IPPcode19 syntax.
        '''
        self.value = ""
        self.type = "undefined"

    def set_value(self, value):
        '''Changes variable's value

           @param value Desired value in IPPcode19 syntax
        '''
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
        '''Checks the variable type

           @return Type of the variable - int, string, bool, nil
        '''
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
