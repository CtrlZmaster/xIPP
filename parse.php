<?php
/*
 * Project: IPP Project 1
 * File: parse.php
 * Title: Lexical and syntax analyser of IPPcode19
 * Description: This script performs lexical and syntax analysis of IPPcode19 language.
 * Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
 */

/*******************************************************************************************
* MAIN BODY
* Program starts here.
******************************************************************************************/
// Arguments handling
// This script accepts only --help parameter
check_args(getopt($shortArgs, $longArgs));

// Creates an object for statistics
$stats = new stats();

// Pass statistics to source_code class and begin processing the code
$source = new source_code($stats);



// Create new object for stats
$stats = new stats();
if(isset($cliArgs['stats'])) {
  $stats->changePath($cliArgs['stats']);
}



// Iterate through lines, delete comments, if non-empty line is found, compares it to the header
for($i = 1; $line->text = fgets(STDIN); $i++) {
//fwrite(STDERR, "Iteration $i, line: $line->text\n"); //DIAG
  $line->number = $i;

  //Detecting empty lines and skipping them (empty line == only '\n' character)
  if(substr($line->text, 0, 1) == "\n") {
    //fwrite(STDERR, "Skipped line $i\n"); //DIAG
    continue;
  }
  // Stripping new line characters returned by fgets
  $line->stripNewLine();
  $line->deleteComment($stats);
  // If the line is not empty, check for header
  if($line->text != "") {
    if(preg_match("/(\s)*\.IPPcode18(\s)*/iu", $line->text) === 0) {
      // Header not found
      $phpLine = __LINE__ + 1;
      fwrite(STDERR,"Line $line->number: Header doesn't contain \".IPPcode18\". Thrown at parse.php:$phpLine.\n");
      exit(21);
    }
    else {
      // Header was found, move on to syntax checking
      break;
    }
  }
}
// If there was no header and it's end of file
if(feof(STDIN)) {
  $phpLine = __LINE__ + 1;
  fwrite(STDERR,"Line $line->number: Header doesn't contain \".IPPcode18\". Thrown at parse.php:$phpLine.\n");
  exit(21);
}

// Create resource for XML and set indentation
$xmlTemp = xmlwriter_open_memory();
xmlwriter_set_indent($xmlTemp, 1);
$res = xmlwriter_set_indent_string($xmlTemp, "  ");
// Create XML header
xmlwriter_start_document($xmlTemp, '1.0', 'UTF-8');

// BEGIN Program
xmlwriter_start_element($xmlTemp, 'program');
xmlwriter_start_attribute($xmlTemp, 'language');
xmlwriter_text($xmlTemp, 'IPPcode18');
xmlwriter_end_attribute($xmlTemp);


// Write $stats
if(isset($cliArgs['stats'])) {
  $stats->writeFile($firstStat);
}

// Successful termination
exit(0);
//END OF MAIN BODY













































/*******************************************************************************************
 * 2019 IMPLEMENTATION
 * New classes only.
 ******************************************************************************************/
class source_code {
  private $stats;
  private $cur_line;
  private $code_line;
  private $cur_line_num;

  public function __construct($stats) {
    $this->stats = $stats;
  }

  // Function processes the source code from stdin
  public function process() {
    $header_found = false;
    // Reading from stdin
    for($i = 1; ($this->cur_line = fgets(STDIN)) !== false; $i++) {
      //fwrite(STDERR, "Iteration $i, line: $line->text\n"); //DIAG
      $this->cur_line_num = $i;

      // Clean the line and update in class
      $this->code_line = clean_line($this->cur_line);

      if($this->code_line === false) {
        // No instruction found on this line, skip it
        continue;
      }

      // If header wasn't found yet and current line contains ".IPPcode19", header
      // is marked as found, the script is terminated otherwise
      if(!$header_found) {
        if(check_header()) {
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

      $instructions = new SplDoublyLinkedList;
      $this->divide($instructions);
      // ---------------------------------------REVISED UNTIL HERE
      xmlwriter_start_element($xmlTemp, 'instruction');     // BEGIN ELEM Instruction

      xmlwriter_start_attribute($xmlTemp, 'order');         // BEGIN ATTR Order
      xmlwriter_text($xmlTemp, $instNum);
      xmlwriter_end_attribute($xmlTemp);                    // END ATTR Order

      xmlwriter_start_attribute($xmlTemp, 'opcode');         // BEGIN ATTR Opcode
      xmlwriter_text($xmlTemp, strtoupper($token->instWord));
      xmlwriter_end_attribute($xmlTemp);                    // END ATTR Opcode

      for($j = 0; $j < 3; $j++) {
        if(($type = $token->types[$j]) == "none") {
          // Break if argument doesn't exist
          break;
        }
        $argNum = $j + 1;
        xmlwriter_start_element($xmlTemp, "arg$argNum");           // BEGIN ELEM Arg
        xmlwriter_start_attribute($xmlTemp, 'type');          // BEGIN ATTR Type

        xmlwriter_text($xmlTemp, $type);
        xmlwriter_end_attribute($xmlTemp);                    // END ATTR Type
        xmlwriter_text($xmlTemp, $token->args[$j]);
        xmlwriter_end_element($xmlTemp);                      // END ELEM Arg
      }

      xmlwriter_end_element($xmlTemp);                      // END ELEM Instruction
    }

    xmlwriter_end_element($xmlTemp); // END ELEM Program
    xmlwriter_end_document($xmlTemp);
    // Flush and write XML to stdout
    echo xmlwriter_output_memory ($xmlTemp);

  }

  // Returns a line cleaned from comments and newline character,
  // false when the line contained only comment or whitespace chars
  private function clean_line() {
    // Find comments first
    preg_split("/#/u", $this->line, $exploded);

    if(count($exploded) == 1) {
      // No '#' sign was present
      if($exploded[0] == "") {
        // Empty line
        return false;
      }
      else {
        // This might be an instruction
        $this->stats->add_code();
        // Trimming the new line character
        $trimmed = preg_replace ('/(\n)|(\r\n)$/', "", $exploded[0]);
        return $trimmed;
      }
    }

    if(preg_match('/(\s)*$/', $exploded[0]) === 1) {
      // First string matched for white spaces, next string is located after '#',
      // so it can be safely discarded as a comment
      $this->stats->add_comment();
      return false;
    }
    else {
      // First string might contain an istruction, next are comments
      $this->stats->add_comment();
      $this->stats->add_code();
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

  private function divide($instruction_list) {
    $lexemes = preg_split("/(\s)+/u", $this->code_line);
    $lexeme_count = count($lexemes);
    switch(strtolower($lexemes[0])) {
      // Instructions without 0 operands
      case "createframe":
      case "pushframe":
      case "popframe":
      case "return":
      case "break":
        $instruction = new instruction_0_op($this);
        if($lexeme_count != 1) {
          //TODO: Throw error
          exit(23);
        }
        break;

      // Instructions with 1 operand
      case "defvar":
      case "pops":
        $instruction = new instruction_1_op($this);
        $instruction->fill_types("var");
        if($lexeme_count != 2) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1]);
        break;
      case "call":
      case "label":
      case "jump":
        $instruction = new instruction_1_op($this);
        $instruction->fill_types("label");
        if($lexeme_count != 2) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1]);
        break;
      case "pushs":
      case "write":
      case "dprint":
        $instruction = new instruction_1_op($this);
        $instruction->fill_types("symb");
        if($lexeme_count != 2) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1]);
        break;

      // Instructions with 2 operands
      case "move":
      case "int2char":
      case "strlen":
      case "type":
        $instruction = new instruction_2_op($this);
        $instruction->fill_types("var", "symb");
        if($lexeme_count != 3) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1], $lexemes[2]);
        break;
      case "read":
        $instruction = new instruction_2_op($this);
        $instruction->fill_types("var", "type");
        if($lexeme_count != 3) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1], $lexemes[2]);
        break;

      // Instructions with 3 arguments
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
        $instruction = new instruction_3_op($this);
        $instruction->fill_types("var", "symb", "symb");
        if($lexeme_count != 4) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1], $lexemes[2], $lexemes[3]);
        break;
      case "jumpifeq":
      case "jumpifneq":
        $instruction = new instruction_3_op($this);
        $instruction->fill_types("label", "symb", "symb");
        if($lexeme_count != 4) {
          //TODO: Throw error
          exit(23);
        }
        $instruction->fill_vals($lexemes[1], $lexemes[2], $lexemes[3]);
        break;
      default:
        $phpLine = __LINE__ + 1;
        fwrite(STDERR,"Line $this->cur_line_num: Unrecognized instruction. Thrown at parse.php:$phpLine.\n");
        exit(22);
    }
    if(check_vals($instruction) === true) {
      //TODO: Throw error - wrong operand type
      exit(22);
    }
    $instruction_list->push();
  }


}

class instruction_0_op {
  protected $line_num;       // Line number in original file
  protected $opcode_char_num;       // Char number in original file
  protected $opcode;

  public function __construct($source_code) {

  }
}

class instruction_1_op extends instruction_0_op {
  protected $arg1_val;
  protected $arg1_type;
  protected $arg1_char_num;

  public function fill_types($type1) {
    $this->arg1_type = $type1;
  }

  public function fill_vals($val1) {
    $this->arg1_val = $val1;
  }
}

class instruction_2_op extends instruction_1_op {
  protected $arg2_val;
  protected $arg2_type;
  protected $arg2_char_num;

  public function fill_types($type1, $type2) {
    instruction_1_op::fill_types($type1);
    $this->arg2_type = $type2;
  }

  public function fill_vals($val1, $val2) {
    instruction_1_op::fill_vals($val1);
    $this->arg2_val = $val2;
  }
}

class instruction_3_op extends instruction_2_op {
  protected $arg3_val;
  protected $arg3_type;
  protected $arg3_char_num;

  public function fill_types($type1, $type2, $type3) {
    instruction_2_op::fill_types($type1, $type2);
    $this->arg3_type = $type3;
  }

  public function fill_vals($val1, $val2, $val3) {
    instruction_2_op::fill_vals($val1, $val2);
    $this->arg3_val = $val3;
  }
}

class op_rules {
  // Returns true if values match types or offending value
  public function check_vals($instruction) {
    switch(getClass($instruction)) {
      case "instruction_3_op":
        if(check_val($this->arg3_val, $this->arg3_type) !== true) {
          return $this->arg3_val;
        }
      case "instruction_2_op":
        if(check_val($this->arg2_val, $this->arg2_type) !== true) {
          return $this->arg2_val;
        }
      case "instruction_1_op":
        if(check_val($this->arg2_val, $this->arg2_type) !== true) {
          return $this->arg1_val;
        }
    }
    return true;
  }

  private function check_val($value, $type) {
    switch($type) {
      case "label":
        break;
      case "var":
        break;
      case "symb":
        break;
      case "type":
        break;
    }
  }

  private function check_str($str) {

  }

  private function check_int($int) {

  }

  private function check_bool($bool) {

  }

  private function check_var($var) {

  }

  private function check_label($label) {

  }

  private function check_type($type) {

  }
}

/*******************************************************************************************
 * STATISTICS
 * This class stores statistics for STATP extension and provides functions to write them
 * to a file and changing them.
 ******************************************************************************************/
class stats {
  private $code = 0;     // Total lines of code
  private $comments = 0; // Total comment lines
  private $labels = 0;
  private $jumps = 0;
  private $filePath = false; // Path to a file where stats should be printed

  /*****************************************************************************************
   * Function creates (or overwrites) a file at path specified in Arguments
   * Parameter firstStat determines which statistic should be written on a first line
   * of generated file
   ****************************************************************************************/
  public function write_file($firstStat) {
    //$this->code--; // Header was counted in
    $myfile = fopen($this->filePath, "w") or exit(12);
    if($firstStat == "loc") {
      fwrite($myfile, "$this->code\n");
      fwrite($myfile, "$this->comments\n");
    }
    else {
      fwrite($myfile, "$this->comments\n");
      fwrite($myfile, "$this->code\n");
    }
    fclose($myfile);

  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   ****************************************************************************************/
  public function add_comment() {
    $this->comments++;
  }

  /*****************************************************************************************
   * Function increments number of lines with code in current file
   ****************************************************************************************/
  public function add_code()  {
    $this->code++;
  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   ****************************************************************************************/
  public function add_jump() {
    $this->jumps++;
  }

  /*****************************************************************************************
   * Function increments number of comments in current file
   ****************************************************************************************/
  public function add_label() {
    $this->labels++;
  }

  /*****************************************************************************************
   * This function sets a path to the file from arguments in this object
   ****************************************************************************************/
  public function set_file_path($path) {
    $this->filePath = $path;
  }
}

function check_args($args) {
  $shortArgs  = array("h");
  $longArgs  = array("help", "stats:", "loc", "comments");
  $allArgs = array("h", "help", "stats", "loc", "comments");

  if($args === false) {
    // Failure while reading arguments
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
  // LINE 1: stats is not set, but loc and comments is set
  // LINE 2: stats is set, but comments or loc is not set
  if(((isset($cliArgs['loc']) || isset($cliArgs['comments'])) && (!isset($cliArgs['stats']))) ||
       (isset($cliArgs['stats']) && (!isset($cliArgs['comments']) || !isset($cliArgs['loc'])))) {
    // Arguments "loc" or "comments" on input and "stats" is missing or no file path was given
    fwrite(STDERR, "File path for statistics is undefined or argument \"--stats\" is missing entirely. Use \"-h\" or \"--help\" for more info.\n");
    exit(10);
  }

  // Throw error on unknown options
  /*foreach ($cliArgs as $key => $value) {
    $argFound = 0;
    for($i = 0; $i < count($allArgs); $i++) {
      if($key == $allArgs[$i]) {
        $argFound++;
      }
      if($argFound == 0) {
        fwrite(STDERR,"Unknown argument(s).\n");
        exit(10);
      }
    }
  }*/

  // Find which stat is first in argument list
  foreach ($cliArgs as $key => $value) {
    if($key == "loc" || $key == "comments") {
      $firstStat = $key;
      break;
    }
  }
}

function help() {
  echo "IPP Project 1 - parse.php v2 help\n\nThis script takes input in
  IPPcode18 language and turns it into (hopefully) equivalent XML representation.
  Extension STATP is implemented too.\n\nCOMPATIBILITY:\nThis script was
  intended to run on PHP 7.3.\n\nUSAGE:\nphp parse.php [ OPTIONS ] < input.src\n
  Script expects input on the standard command line input.\n\nOPTIONS:
  \n--stats=filename  This parameter enables statistics. Statistics will be
  printed after the script finishes into the specified file (must be used with
  --loc, --comments or both)\n--loc             This outputs number of lines
  with code into the statistic (can't be used w/o --stats)\n--comments
  Prints number of comments into the statistic (can't be used w/o --stats)\n";
}

/******************************************************************************************/










































/*******************************************************************************************
 * TOKENS
 * This class implements the token and its functions.
 ******************************************************************************************/
class token {
  public $instWord; // ORDER 0 - contains operation code
  public $args = array(); // Array of argument values
  public $types = array("none", "none", "none"); // Array of argument types (var, symb, label) and later (bool, string, int)
  public $lineNum;  // ORDER 4 - line number in original file

  /*****************************************************************************************
   * Function fills token with argument values, opcode and original line number from input
   * depending on number specified in parameter "order".
   ****************************************************************************************/
  public function fillVal($order, $content) {
    switch($order) {
      case 0:
        $this->instWord = $content;
        break;
      case 1:
        $this->args[0] = $content;
        break;
      case 2:
        $this->args[1] = $content;
        break;
      case 3:
        $this->args[2] = $content;
        break;
      case 4:
        $this->lineNum = $content;
        break;
      default:
        fwrite(STDERR,"Invalid call of fillVal - something tried to fill non-existent value in token.\n");
    }
  }

  /*****************************************************************************************
   * Checks syntax of all arguments by scanning token properties "types" and "args" where types contain allowed argument types
   * and args contain values read from input.
   ****************************************************************************************/
  public function checkArgs() {
    //fwrite(STDERR, "checkArgs-----"); //DIAG
    //fwrite(STDERR, var_dump($this->args)); //DIAG
    //fwrite(STDERR, var_dump($this->types)); //DIAG
    for($i = 0; $i < 3; $i++) {
      switch($this->types[$i]) {
        case "symb":
          // Variable or immediate value - no break - NOT calling exit in this case
          // Checking format of an immediate value - string, int, bool
          //fwrite(STDERR, $this->args[$i]); //DIAG
          if( preg_match("/^string@(?:[^\s\\#]|(\\[0-9]{3}))*$/u", $this->args[$i], $matched) == 1 ||
              preg_match("/^int@[+-]?[0-9]+$/u", $this->args[$i]) == 1 ||
              preg_match("/^bool@(true|false)$/u", $this->args[$i]) == 1) {
            // Number two limits outputted strings to two, in front and behind the '@'
            $clean = preg_split("/@/u", $this->args[$i], 2);
            $this->args[$i] = $clean[1]; // Part after @
            $this->types[$i] = $clean[0]; // Part before @
            //fwrite(STDERR, "checkArgsIF---"); //DIAG
            //fwrite(STDERR, var_dump($this->args)); //DIAG
            //fwrite(STDERR, var_dump($this->types)); //DIAG
            break;
          }
        case "var":
          if(preg_match("/^(GF|TF|LF)@([[:alpha:]]|[_\-$&%*])(?:[[:alnum:]]|[_\-$&%*])*$/u", $this->args[$i], $matched) == 0 ||
             $this->args[$i] != $matched[0]) {
            //fwrite(STDERR, $this->args[$i]); //DIAG
            //fwrite(STDERR, var_dump($matched)); //DIAG
            if($this->types[$i] == "var") {
              // Came from var - incorrect syntax
              $phpLine = __LINE__ + 1;
              fwrite(STDERR,"Line $this->lineNum: This is not a valid variable. Thrown at parse.php:$phpLine.\n");
              exit(21);
            }
            else {
              // Came from immediate value checking (if in "symb" case evaluated as false)
              $phpLine = __LINE__ + 1;
              fwrite(STDERR,"Line $this->lineNum: This is not a valid immediate value. Thrown at parse.php:$phpLine.\n");
              exit(21);
            }
          }
          else {
            // Variable has correct syntax, breaking before the error for incorrect symbols.
            if($this->types[$i] == "symb") {
              // If it was first examined as a symbol, type has to change to var for XML output
              $this->types[$i] = "var";
            }
            break;
          }

        case "label":
          if(preg_match("/^([[:alpha:]]|[_\-$&%*])(?:[[:alnum:]]|[_\-$&%*])*$/u", $this->args[$i]) == 0) {
            $phpLine = __LINE__ + 1;
            fwrite(STDERR,"Line $this->lineNum: This is not a valid label. Thrown at parse.php:$phpLine.\n");
            exit(21);
          }
          break;

        case "none":
          break 2;
        default:
          fwrite(STDERR,"Invalid call of checkArgs - something tried to check an unknown data type.\n");
          break;
      }
    }
  }
}

/*******************************************************************************************
 * CODE LINES
 * Functions in this class check syntax and turn lines into tokens if possible.
 ******************************************************************************************/
class codeLine {
  public $text;
  public $number;

  /*****************************************************************************************
   * This function converts code lines to tokens. Upon token creation, it fills Instruction'
   * argument types into the token object for type compatibility checking.
   ****************************************************************************************/
  public function toToken() {
    $lexemes = preg_split("/(\s)+/u", $this->text);
    $token = new token();

    // preg_split returns empty string on zeroth index when white spaces are
    // in front of the string - $offset solves that by ignoring empty string if there is one
    $offset = $this->firstLexemeIndex($lexemes);
    // Checking number of arguments
    switch(strtolower($lexemes[$offset])) {
      // Instructions without an argument
      case "createframe":
      case "pushframe":
      case "popframe":
      case "return":
      case "break":
        break;

      // Instructions with 1 argument
      case "defvar":
      case "pops":
        $token->types[0] = "var";
        break;
      case "call":
      case "label":
      case "jump":
        $token->types[0] = "label";
        break;
      case "pushs":
      case "write":
      case "dprint":
        $token->types[0] = "symb";
        break;

      // Instructions with 2 arguments
      case "move":
      case "int2char":
      case "strlen":
      case "type":
        $token->types[0] = "var";
        $token->types[1] = "symb";
        break;
      case "read":
        $token->types[0] = "var";
        $token->types[1] = "type";
        break;

      // Instructions with 3 arguments
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
        $token->types[0] = "var";
        $token->types[1] = "symb";
        $token->types[2] = "symb";
        break;
      case "jumpifeq":
      case "jumpifneq":
        $token->types[0] = "label";
        $token->types[1] = "symb";
        $token->types[2] = "symb";
        break;
      default:
        $phpLine = __LINE__ + 1;
        fwrite(STDERR,"Line $this->number: Unrecognized instruction. Thrown at parse.php:$phpLine.\n");
        exit(21);
        break;
    }
    $this->fillToken($token, $lexemes);
    return $token;
  }

  /*****************************************************************************************
   * This function helps to find empty string generated by preg_split when white spaces
   * are in front of an instruction
   ****************************************************************************************/
  private function firstLexemeIndex($lexemes) {
    if($lexemes[0] == "" ) {
      // Instruction is in first index
      return 1;
    }
    else {
      //Instruction is in zeroth index
      return 0;
    }
  }

  /*****************************************************************************************
   * This method fills the token with arguments from a code line. It also checks
   * argument types generated by toToken() and their count.
   ****************************************************************************************/
  private function fillToken(&$token, $lexemes) {
    // Maximal number of arguments determined by changing default value of a given
    // argument's type. Iterates through arguments, if they're changed to indicate
    // that the instruction supports them, $maxArgs gets incremented.
    for($i = 0, $maxArgs = 0; $i < 3; $i++) {
      if($token->types[$i] != "none") {
        $maxArgs++;
      }
    }
    // Checking number of arguments - if there is more, filling token fails
    for($i = 0, $j = 0; $i < count($lexemes); $i++, $j++) {
      // More arguments than allowed
      //fwrite(STDERR, "j=$j, i=$i, maxargs='$maxArgs'\n"); //DIAG
      if($j > $maxArgs + 1) { // + 1 to accomodate instruction
        $phpLine = __LINE__ + 1;
        fwrite(STDERR,"Line $this->number: Too many arguments. Thrown at parse.php:$phpLine.\n");
        exit(21);
      }

      // Skip empty strings - created when white spaces are encountered at the end or
      // beginning of a line
      //fwrite(STDERR, "j=$j, i=$i, lexemes[$i]='$lexemes[$i]'\n"); //DIAG
      if($lexemes[$i] == "") {
        $j--;
        continue;
      }
      // Copy instruction and arguments into token
      $token->fillVal($j, $lexemes[$i]);
    }
    // Copies original line number into the token
    $token->fillVal(4,$this->number);
    //$token->checkArgs();
  }

  /*****************************************************************************************
   * This method takes a line of code and removes everything after the first hash sign.
   * It also calls methods from stats class to count lines with code or comments.
   ****************************************************************************************/
  public function deleteComment($stats) {

  }

  public function stripNewLine() {
    if(substr($this->text, -1) == "\n") {
      rtrim($this->text, "\n");
    }
  }
}


?>
