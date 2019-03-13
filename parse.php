<?php
/*
 * Project: IPP Project 1
 * File: parse.php
 * Title: Lexical and syntax analyser of IPPcode19
 * Description: This script performs lexical and syntax analysis of IPPcode19 language.
 * Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
 */

/*******************************************************************************************
* MAIN
* This is executed first.
******************************************************************************************/
// Argument handling
$arg_array = check_args();

// Pass statistics (by reference) to source_code class and begin processing the code
$source = new source_code($arg_array);

$source->process();

// Successful termination
exit(0);

/******************************************************************************************/


/*******************************************************************************************
 * 2019 IMPLEMENTATION
 * I based my script on the script from last year with significant change to the object
 * model and some portions were rewritten entirely.
 ******************************************************************************************/

/*******************************************************************************************
 * SOURCE CODE
 * This class handles loading IPPcode19 from STDIN and acts as a main class.
 ******************************************************************************************/
class source_code {
  private $stats;             // An instance of stats
  private $cur_line;          // Original line from stdin being processed
  private $code_line;         // Line without white-space chars on both ends and comments
  private $cur_line_num = 0;  // Line number in original file
  private $arg_array;         // Argument array returned by getopt

  /*****************************************************************************************
   * Constructor fills the $arg_array memeber variable from $arg_array argument and creates
   * an instance of a stats class that will be used to record statistics.
   ****************************************************************************************/
  public function __construct($arg_array) {
    $this->stats = new stats();
    $this->arg_array = $arg_array;
  }

  /*****************************************************************************************
   * MAIN FUNCTION that reads file line-by-line.
   ****************************************************************************************/
  public function process() {
    // Flag
    $header_found = false;

    // Checked instructions are stored in this linked list
    $instruction_list = new SplDoublyLinkedList;

    // Reading from stdin
    for($i = 1; ($this->cur_line = fgets(STDIN)) !== false; $i++) {
      //fwrite(STDERR, "Iteration $i, line: $line->text\n"); //DIAG
      $this->cur_line_num = $i;

      // Clean the line and update in class
      $this->code_line = $this->clean_line();

      if($this->code_line === false) {
        // No instruction found on this line, skip it
        continue;
      }

      // If header wasn't found yet and current line contains ".IPPcode19", header
      // is marked as found, the script is terminated otherwise
      if(!$header_found) {
        if($this->check_header()) {
          $header_found = true;
          continue;
        }
        else {
          // Throw error: non-comformant header
          $phpLine = __LINE__ + 1;
          fwrite(STDERR,"Line $this->cur_line_num: Header doesn't contain \".IPPcode19\". Thrown at parse.php:$phpLine.\n");
          exit(21);
        }
      }
      $instruction = $this->divide();
      $instruction_list->push($instruction);
    }

    // Check that header was found before the file ended
    if($header_found == false) {
      $phpLine = __LINE__ + 1;
      fwrite(STDERR,"Line $this->cur_line_num: Header \".IPPcode19\" was not found. Thrown at parse.php:$phpLine.\n");
      exit(21);
    }

    $xml = new xml_out();
    $xml->init();
    $xml->start_program();

    // Iterating through list of instructions
    for($instruction_list->rewind(); $instruction_list->valid(); $instruction_list->next()) {
      // list->key() starts at 0
      $xml->new_instruction($instruction_list->key() + 1, $instruction_list->current());
      // Every instruction must be written on a single line, so number of code lines
      // is the same as number of instructions
      $this->stats->add_code();
      // Special statistics for certain instructions
      switch(strtolower($instruction_list->current()->get_opcode())) {
        case "label":
          $this->stats->add_label();
          break;
        case "jump": case "jumpifeq": case "jumpifneq":
          $this->stats->add_jump();
      }
    }

    $xml->end_program();
    $xml->write();

    // Nothing is written when file is undefined
    $this->stats->write_file($this->arg_array);
  }

  // Returns a line cleaned from comments and newline character,
  // false when the line contained only comment or whitespace chars
  private function clean_line() {
    // Find comments first
    $exploded = preg_split("/#/u", $this->cur_line);

    if(count($exploded) == 1) {
      // No '#' sign was present
      if($exploded[0] == "\n" || $exploded[0] == "\r\n") {
        // Empty line
        return false;
      }
      else {
        // Trimming the new line character
        $trimmed = preg_replace ('/(\n)|(\r\n)$/', "", $exploded[0]);
        return $trimmed;
      }
    }

    if(preg_match('/^(\s)*$/', $exploded[0]) === 1) {
      // First string matched for white spaces, next string is located after '#',
      // so it can be safely discarded as a comment
      $this->stats->add_comment();
      return false;
    }
    else {
      // First string might contain an instruction, next are comments
      $this->stats->add_comment();
      return $exploded[0];
    }
  }

  private function check_header() {
    if(preg_match('/^\s*.IPPcode19\s*$/i', $this->code_line) == 1) {
      return true;
    }
    else {
      return false;
    }
  }

  private function divide() {
    $lexemes = preg_split("/(\s)+/u", $this->code_line);

    // If instruction is followed only by whitespaces, this produces
    // one empty string at the end
    if($lexemes[count($lexemes) - 1] == "") {
      array_pop($lexemes);
    }

    // If instruction is preceded only by whitespaces, this produces
    // one empty string at the beginning
    if($lexemes[0] == "") {
      array_shift($lexemes);
    }

    // Checking instruction word
    $type_arr = rules::check_instruct($lexemes[0]);
    // Returns false when wrong opcode was detected
    if($type_arr === false) {
      $phpLine = __LINE__ + 1;
      fwrite(STDERR,"Line $this->cur_line_num: Unrecognized instruction. Thrown at parse.php:$phpLine.\n");
      exit(22);
    }
    switch(count($type_arr)) {
      case 0:
        $instruction = new instruction_0_op($this->cur_line_num, $lexemes);
        break;
      case 1:
        $instruction = new instruction_1_op($this->cur_line_num, $lexemes, $type_arr);
        break;
      case 2:
        $instruction = new instruction_2_op($this->cur_line_num, $lexemes, $type_arr);
        break;
      case 3:
        $instruction = new instruction_3_op($this->cur_line_num, $lexemes, $type_arr);
        break;
    }

    // Check number of lexemes
    if(count($type_arr) + 1 != count($lexemes)) {
      // Find char_num where operand starts
      $err_char_num = mb_strpos($this->cur_line, $lexemes[count($type_arr)]) + 1;

      // Throw error - too much lexemes to be a valid instruction
      $phpLine = __LINE__ + 1;
      fwrite(STDERR,"$this->cur_line_num:$err_char_num: Incorrect number of operands. Thrown at parse.php:$phpLine.\n");
      exit(23);
    }
    // Checks operand syntax
    if(($offending_value = rules::check_vals($instruction)) !== true) {
      // Find char_num where operand starts
      $err_char_num = mb_strpos($this->cur_line, $offending_value) + 1;

      // Throw error - wrong operand type
      $phpLine = __LINE__ + 1;
      fwrite(STDERR,"$this->cur_line_num:$err_char_num: Syntax error in this operand. Thrown at parse.php:$phpLine.\n");
      exit(23);
    }
    // var_dump($instruction); //DIAG
    // Replacing type symbol with type of constant or "var"
    $instruction->update_symb();
    // var_dump($instruction); //DIAG
    return $instruction;
  }


}

/*******************************************************************************************
 * INSTRUCTION (with) 0 OPERANDS
 * Base class for instructions with more operands
 * Holds an instruction when syntax analysis is done.
 ******************************************************************************************/
class instruction_0_op {
  protected $line_num;              // Line number in original file
  protected $opcode_char_num;       // Char number in original file - UNUSED
  protected $opcode;                // Opeartion code (instruction word)

  /*****************************************************************************************
   * Constructor fills in opcode and original line number, instruction word is checked here,
   * but preselection is made based on number of lexemes. Argument $line_num takes number
   * of line from the original file and $lexemes is array of lexemes with size of 1. Returns
   * new object on success, false when instruction word is incorrect.
   ****************************************************************************************/
  public function __construct($line_num, $lexemes) {
    $this->line_num = $line_num;
    $this->opcode = $lexemes[0];
  }
  /*****************************************************************************************
   * Returns instruction word.
   ****************************************************************************************/
  public function get_opcode() {
    return $this->opcode;
  }

  /*****************************************************************************************
   * Returns array of operands.
   * Returns false for compatibility in this class. Overriden in child classes.
   ****************************************************************************************/
  public function get_ops() {
    return false;
  }

  /*****************************************************************************************
   * Returns array of operand types.
   * Returns false for compatibility in this class. Overriden in child classes.
   ****************************************************************************************/
  public function get_types() {
    return false;
  }

  /*****************************************************************************************
   * Changes operand type symbol to a constant or a variable depending on value.
   * Returns false for compatibility in this class. Overriden in child classes.
   ****************************************************************************************/
  public function update_symb() {
    return false;
  }
}

/*******************************************************************************************
 * INSTRUCTION (with) 1 OPERAND
 * Child class of instructions with 0 operands
 * Holds an instruction when syntax analysis is done.
 ******************************************************************************************/
class instruction_1_op extends instruction_0_op {
  protected $arg1_val;     // Adds a value of argument 1
  protected $arg1_type;    // Adds a type of argument 1

  /*****************************************************************************************
   * Constructor fills in opcode and original line number, instruction word is checked here,
   * but preselection is made based on number of lexemes. Argument $line_num takes number
   * of line from the original file and $lexemes is array of lexemes with size of 1. Returns
   * new object on success, false when instruction word is incorrect.
   ****************************************************************************************/
  public function __construct($line_num, $lexemes, $type_arr) {
    //var_dump($lexemes); //DIAG
    $this->line_num = $line_num;
    $this->opcode = $lexemes[0];
    $this->fill_vals($lexemes[1]);
    $this->fill_types($type_arr[0]);
  }

  /*****************************************************************************************
   * Sets types of arguments. Arguments should contain strings with types defined
   * by instructions. Types are used for syntax analysis.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_types($type1) {
    $this->arg1_type = $type1;
  }

  /*****************************************************************************************
   * Sets values of arguments. Arguments should contain strings with values from source
   * code without any modification. They will be checked and modified for XML later.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_vals($val1) {
    $this->arg1_val = $val1;
  }

  /*****************************************************************************************
   * Returns array of operand values.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_ops() {
    return array($this->arg1_val);
  }

  /*****************************************************************************************
   * Returns array of operand types.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_types() {
    return array($this->arg1_type);
  }

  /*****************************************************************************************
   * Changes operand type symbol to a constant or a variable depending on value.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function update_symb() {
    if($this->arg1_type == "symb") {
      $clean = preg_split("/@/u", $this->arg1_val);
      if($clean[0] == "int" || $clean[0] == "bool" || $clean[0] == "string" || $clean[0] == "nil") {
        $this->arg1_val = $clean[1]; // Part after @
        $this->arg1_type = $clean[0]; // Part before @
      }
      else {
        $this->arg1_type = "var";
      }
    }
  }
}

/*******************************************************************************************
 * INSTRUCTION (with) 2 OPERANDS
 * Child class of instructions with 1 operand
 * Holds an instruction when syntax analysis is done.
 ******************************************************************************************/
class instruction_2_op extends instruction_1_op {
  protected $arg2_val;
  protected $arg2_type;

  /*****************************************************************************************
   * Constructor fills in opcode and original line number, instruction word is checked here,
   * but preselection is made based on number of lexemes. Argument $line_num takes number
   * of line from the original file and $lexemes is array of lexemes with size of 1. Returns
   * new object on success, false when instruction word is incorrect.
   ****************************************************************************************/
  public function __construct($line_num, $lexemes, $type_arr) {
    //var_dump($lexemes); //DIAG
    $this->line_num = $line_num;
    $this->opcode = $lexemes[0];
    $this->fill_vals($lexemes[1], $lexemes[2]);
    $this->fill_types($type_arr[0], $type_arr[1]);
  }

  /*****************************************************************************************
   * Sets types of arguments. Arguments should contain strings with types defined
   * by instructions. Types are used for syntax analysis.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_types($type1, $type2 = null) {
    instruction_1_op::fill_types($type1);
    $this->arg2_type = $type2;
  }

  /*****************************************************************************************
   * Sets values of arguments. Arguments should contain strings with values from source
   * code without any modification. They will be checked and modified for XML later.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_vals($val1, $val2 = null) {
    instruction_1_op::fill_vals($val1);
    $this->arg2_val = $val2;
  }

  /*****************************************************************************************
   * Returns array of operand values.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_ops() {
    return array($this->arg1_val, $this->arg2_val);
  }

  /*****************************************************************************************
   * Returns array of operand types.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_types() {
    return array($this->arg1_type, $this->arg2_type);
  }

  /*****************************************************************************************
   * Changes operand type symbol to a constant or a variable depending on value.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function update_symb() {
    instruction_1_op::update_symb();
    if($this->arg2_type == "symb") {
      $clean = preg_split("/@/u", $this->arg2_val);
      if($clean[0] == "int" || $clean[0] == "bool" || $clean[0] == "string" || $clean[0] == "nil") {
        $this->arg2_val = $clean[1]; // Part after @
        $this->arg2_type = $clean[0]; // Part before @
      }
      else {
        $this->arg2_type = "var";
      }
    }
  }
}

/*******************************************************************************************
 * INSTRUCTION (with) 3 OPERANDS
 * Child class of instructions with 2 operands
 * Holds an instruction when syntax analysis is done.
 ******************************************************************************************/
class instruction_3_op extends instruction_2_op {
  protected $arg3_val;
  protected $arg3_type;

  /*****************************************************************************************
   * Constructor fills in opcode and original line number, instruction word is checked here,
   * but preselection is made based on number of lexemes. Argument $line_num takes number
   * of line from the original file and $lexemes is array of lexemes with size of 1. Returns
   * new object on success, false when instruction word is incorrect.
   ****************************************************************************************/
  public function __construct($line_num, $lexemes, $type_arr) {
    //var_dump($lexemes); //DIAG
    $this->line_num = $line_num;
    $this->fill_vals($lexemes[1], $lexemes[2], $lexemes[3]);
    $this->fill_types($type_arr[0], $type_arr[1], $type_arr[2]);
  }

  /*****************************************************************************************
   * Sets types of arguments. Arguments should contain strings with types defined
   * by instructions. Types are used for syntax analysis.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_types($type1, $type2 = null, $type3 = null) {
    instruction_2_op::fill_types($type1, $type2);
    $this->arg3_type = $type3;
  }

  /*****************************************************************************************
   * Sets values of arguments. Arguments should contain strings with values from source
   * code without any modification. They will be checked and modified for XML later.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  protected function fill_vals($val1, $val2 = null, $val3 = null) {
    instruction_2_op::fill_vals($val1, $val2);
    $this->arg3_val = $val3;
  }

  /*****************************************************************************************
   * Returns array of operand values.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_ops() {
    return array($this->arg1_val, $this->arg2_val, $this->arg3_val);
  }

  /*****************************************************************************************
   * Returns array of operand types.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function get_types() {
    return array($this->arg1_type, $this->arg2_type, $this->arg3_type);
  }

  /*****************************************************************************************
   * Changes operand type symbol to a constant or a variable depending on value.
   * Overriden in child classes due to different number of arguments.
   ****************************************************************************************/
  public function update_symb() {
    instruction_2_op::update_symb();
    if($this->arg3_type == "symb") {
      $clean = preg_split("/@/u", $this->arg3_val);
      if($clean[0] == "int" || $clean[0] == "bool" || $clean[0] == "string" || $clean[0] == "nil") {
        $this->arg3_val = $clean[1]; // Part after @
        $this->arg3_type = $clean[0]; // Part before @
      }
      else {
        $this->arg3_type = "var";
      }
    }
  }
}

/*********************************************************************************************
 * OPERAND RULES
 * Class methods check syntax of operands in instances of instructions.
 ********************************************************************************************/
class rules {
  /*******************************************************************************************
   * Method checks syntax of instruction words and returns array with types of arguments.
   ******************************************************************************************/
  public function check_instruct($inst_word) {
    switch(strtolower($inst_word)) {
      // Instructions without 0 operands
      case "createframe":
      case "pushframe":
      case "popframe":
      case "return":
      case "break":
        $type_arr = array();
        break;

      // Instructions with 1 operand
      case "defvar":
      case "pops":
        $type_arr = array("var");
        break;
      case "call":
      case "label":
      case "jump":
        $type_arr = array("label");
        break;
      case "pushs":
      case "write":
      case "dprint":
        $type_arr = array("symb");
        break;

      // Instructions with 2 operands
      case "move":
      case "int2char":
      case "strlen":
      case "type":
        $type_arr = array("var", "symb");
        break;
      case "read":
        $type_arr = array("var", "type");
        break;

      // Instructions with 3 operands
      case "add":
      case "sub":
      case "mul":
      case "idiv":
      case "lt": case "gt": case "eq":
      case "and": case "or": case "not":
      case "stri2int":
      case "concat":
      case "getchar":
      case "setchar":
        $type_arr = array("var", "symb", "symb");
        break;
      case "jumpifeq":
      case "jumpifneq":
        $type_arr = array("label", "symb", "symb");
        break;
      default:
        return false;
    }
    return $type_arr;
  }

  /*******************************************************************************************
   * This method checks syntax of instruction's operands.
   * Returns true if values match types or offending value.
   ******************************************************************************************/
  public function check_vals($instruction) {
    $ops = $instruction->get_ops();
    $types = $instruction->get_types();

    switch(get_class($instruction)) {
      case "instruction_3_op":
        if(self::check_val($ops[2], $types[2]) !== true) {
          return $ops[2];
        }
      case "instruction_2_op":
        if(self::check_val($ops[1], $types[1]) !== true) {
          return $ops[1];
        }
      case "instruction_1_op":
        if(self::check_val($ops[0], $types[0]) !== true) {
          return $ops[0];
        }
    }
    return true;
  }

  /*******************************************************************************************
   * Helper for function check_vals - checks pair $value and $type.
   * Returns true if values match types or value of incorrect operand.
   ******************************************************************************************/
  private function check_val($value, $type) {
    switch($type) {
      case "label":
        return self::check_label($value);
        break;
      case "var":
        return self::check_var($value);
        break;
      case "symb":
        return self::check_symb($value);
        break;
      case "type":
        return self::check_type($value);
        break;
    }
  }

  /*******************************************************************************************
   * Helper for function check_val - checks symbols.
   * Returns true if values match types or value of incorrect operand.
   ******************************************************************************************/
  private function check_symb($symb) {
    // Can represent variable or constant
    // Checking format of an immediate value - string, int, bool
    //fwrite(STDERR, $this->args[$i]); //DIAG
    if( preg_match("/^string@(?:[^\s\\#]|(\\[0-9]{3}))*$/u", $symb) == 1 ||
        preg_match("/^int@[+-]?[0-9]+$/u", $symb) == 1 ||
        preg_match("/^bool@(true|false)$/u", $symb) == 1 ||
        preg_match("/^nil@nil$/u", $symb) == 1) {
      //fwrite(STDERR, "checkArgsIF---"); //DIAG
      //fwrite(STDERR, var_dump($this->args)); //DIAG
      //fwrite(STDERR, var_dump($this->types)); //DIAG
      return true;
    }

    return self::check_var($symb);
  }

  /*******************************************************************************************
   * Helper for function check_val - checks variable.
   * Returns true if values match types or value of incorrect operand.
   ******************************************************************************************/
  private function check_var($var) {
    if(preg_match("/^(GF|TF|LF)@([[:alpha:]]|[_\-$&%*])(?:[[:alnum:]]|[_\-$&%*])*$/u", $var) == 0) {
      return $var;
    }
    return true;
  }

  /*******************************************************************************************
   * Helper for function check_val - checks label.
   * Returns true if values match types or value of incorrect operand.
   ******************************************************************************************/
  private function check_label($label) {
    if(preg_match("/^([[:alpha:]]|[_\-$&%*])(?:[[:alnum:]]|[_\-$&%*])*$/u", $label) == 0) {
      return $label;
    }
    return true;
  }

  /*******************************************************************************************
   * Helper for function check_val - checks data type name.
   * Returns true if values match types or value of incorrect operand.
   ******************************************************************************************/
  private function check_type($type) {
    if($type == "string" || $type == "int" || $type == "bool" || $type == "nil") {
      return true;
    }
    return $type;
  }
}

/*******************************************************************************************
 * XML OUTPUT
 * Handles creation of XML output.
 ******************************************************************************************/
class xml_out {
  private $buffer;

  /*****************************************************************************************
   * Creates an instance of XML buffer that is used by other XML instructions
   ****************************************************************************************/
  public function __construct() {
    $this->buffer = xmlwriter_open_memory();
  }

  /*****************************************************************************************
   * Function sets initial settings for the XML file
   ****************************************************************************************/
  public function init() {
    // Set indentation
    xmlwriter_set_indent($this->buffer, 1);
    $res = xmlwriter_set_indent_string($this->buffer, "  ");
    // Create XML header
    xmlwriter_start_document($this->buffer, '1.0', 'UTF-8');
  }

  /*****************************************************************************************
   * Creates a program element in XML buffer
   ****************************************************************************************/
  public function start_program() {
    // BEGIN Program
    xmlwriter_start_element($this->buffer, 'program');
    xmlwriter_start_attribute($this->buffer, 'language');
    xmlwriter_text($this->buffer, 'IPPcode19');
    xmlwriter_end_attribute($this->buffer);
  }

  /*****************************************************************************************
   * Creates a new instruction element in buffer. Argument $instruction_num contains
   * order of the instruction (can be obtained as a key from linked list of instr.)
   * and $instruction should contain an instance of instruction class.
   ****************************************************************************************/
  public function new_instruction($instruction_num, $instruction) {
    xmlwriter_start_element($this->buffer, 'instruction');     // BEGIN ELEM Instruction

    xmlwriter_start_attribute($this->buffer, 'order');           // BEGIN ATTR Order
    xmlwriter_text($this->buffer, $instruction_num);
    xmlwriter_end_attribute($this->buffer);                      // END ATTR Order

    xmlwriter_start_attribute($this->buffer, 'opcode');          // BEGIN ATTR Opcode
    xmlwriter_text($this->buffer, strtoupper($instruction->get_opcode()));
    xmlwriter_end_attribute($this->buffer);                      // END ATTR Opcode

    switch(get_class($instruction)) {
      case "instruction_3_op":
        $op_count = 3;
        break;
      case "instruction_2_op":
        $op_count = 2;
        break;
      case "instruction_1_op":
        $op_count = 1;
        break;
      case "instruction_0_op":
        $op_count = 0;
        break;
    }

    $ops = $instruction->get_ops();
    $types = $instruction->get_types();

    for($i = 1; $i <= $op_count; $i++) {
      xmlwriter_start_element($this->buffer, "arg$i");                // BEGIN ELEM Arg
      xmlwriter_start_attribute($this->buffer, 'type');                 // BEGIN ATTR Type

      xmlwriter_text($this->buffer, $types[$i-1]);
      xmlwriter_end_attribute($this->buffer);                           // END ATTR Type
      xmlwriter_text($this->buffer, $ops[$i-1]);
      xmlwriter_end_element($this->buffer);                           // END ELEM Arg
    }

    xmlwriter_end_element($this->buffer);                           // END ELEM Instruction
  }

  /*****************************************************************************************
   * Function closes program element in XML buffer.
   ****************************************************************************************/
  public function end_program() {
    xmlwriter_end_element($this->buffer); // END ELEM Program
    xmlwriter_end_document($this->buffer);
  }


  /*****************************************************************************************
   * Function prints XML from buffer to standard output.
   ****************************************************************************************/
  public function write() {
    // Flush buffer and write XML to stdout
    echo xmlwriter_output_memory ($this->buffer);
  }
}

/*******************************************************************************************
 * STATISTICS
 * This class stores statistics for STATP extension and provides functions to write them
 * to a file and modifying them.
 ******************************************************************************************/
class stats {
  private $code = 0;         // Total lines of code
  private $comments = 0;     // Total comment lines
  private $labels = 0;       // Number of labels
  private $jumps = 0;        // Number of all jumps

  /*****************************************************************************************
   * Function creates (or overwrites) a file at path specified in arguments
   * Parameter args should contain associative array returned by getopt
   ****************************************************************************************/
  public function write_file($args) {
    if(!isset($args['stats'])) {
      return;
    }
    $myfile = fopen($args['stats'], "w") or exit(12);
    // Go over argument list and write statistics in that order
    foreach ($args as $key => $value) {
      switch($key) {
        case "loc":
          fwrite($myfile, "$this->code\n");
          break;
        case "comments":
          fwrite($myfile, "$this->comments\n");
          break;
        case "labels":
          fwrite($myfile, "$this->labels\n");
          break;
        case "jumps":
          fwrite($myfile, "$this->jumps\n");
          break;
        default:
          // DO NOTHING - other options
          break;
      }
    }

    // Save file to disk
    fclose($myfile);
  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   * Called when lines are cleaned
   ****************************************************************************************/
  public function add_comment() {
    $this->comments++;
  }

  /*****************************************************************************************
   * Function increments number of lines with code in current file
   * Call from xml writer
   ****************************************************************************************/
  public function add_code()  {
    $this->code++;
  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   * Call from xml writer
   ****************************************************************************************/
  public function add_jump() {
    $this->jumps++;
  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   * Call from xml writer
   ****************************************************************************************/
  public function add_label() {
    $this->labels++;
  }
}

// Function reads arguments from command line and checks that valid options were given.
// When invalid options are given, script ends with an appropriate error code
function check_args() {
  $short_args  = "h";
  $long_args  = array("help", "stats:", "loc", "comments", "labels", "jumps");

  $args = getopt($short_args, $long_args);

  if($args === false) {
    // Failure while reading arguments (undefinded options included)
    exit(10);
  }

  // Writing help
  if(((isset($args['h'])) xor (isset($args['help']))) && (count($args) == 1)) {
    // Help argument without any value and accompanying arguments
    help();
    exit(0);
  }
  else {
    if((isset($args['h']) || isset($args['help'])) && count($args) > 1) {
      exit(10);
    }
  }

  // Invalid argument options
  // Stats is not set, but some of the other options are set
  if(!isset($args['stats']) && (isset($args['loc']) || isset($args['comments']) ||
      isset($args['labels']) || isset($args['jumps']))) {
    // Arguments "loc" or "comments" on input and "stats" is missing or no file path was given
    fwrite(STDERR, "File path for statistics is undefined or option \"--stats\" is missing entirely. Use \"-h\" or \"--help\" for more info.\n");
    exit(10);
  }
  // Stats is set, but some of the other options are not set
  if(isset($args['stats']) && !(isset($args['comments']) || isset($args['loc']) ||
    isset($args['labels']) || isset($args['jumps']))) {
    fwrite(STDERR, "No statistic set for option \"--stats\". Use \"-h\" or \"--help\" for more info.\n");
    exit(10);
  }

  return $args;
}

// Function prints help on standard output
function help() {
  echo "IPP Project 1 - parse.php v3 help\n\n";
  echo "This script takes input in IPPcode19 language and turns it into " .
  "(hopefully) equivalent XML representation. Extension STATP is implemented too. " .
  "\n\n";
  echo "COMPATIBILITY:\nThis script was intended to run on PHP 7.3.\n\n";
  echo "USAGE:\nphp parse.php [ OPTIONS ] < input.src\n";
  echo "Script expects input on the standard command line input.\n\n";
  echo "OPTIONS:\n";
  echo "--stats=filename  This parameter enables statistics. Statistics will be " .
  "printed after the script finishes into the specified file (must be used with " .
  "one or more of: --loc, --comments, --labels, --jumps)\n";
  echo "--loc             This outputs number of lines with code into the statistic " .
  "(can't be used w/o --stats)\n";
  echo "--comments        Prints number of comments into the statistic (can't " .
  "be used w/o --stats)\n";
  echo "--jumps           Prints number of jump instructions into the statistic " .
  "(can't be used w/o --stats)\n";
  echo "--labels          Prints number of defined labels into the statistic " .
  "(can't be used w/o --stats)\n";

}
?>
