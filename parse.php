<?php
/*
 * Project: IPP Project 1
 * File: parse.php
 * Title: Lexical and syntax analyser of IPPcode18
 * Description: This script performs lexical and syntax analysis of IPPcode18 language.
 * Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
 */

/*******************************************************************************************
* MAIN BODY
* Program starts here.
******************************************************************************************/
// Arguments handling
// This script accepts only --help parameter
$shortArgs  = "h";
$longArgs  = array("help", "stats:", "loc", "comments");
$allArgs = array("h", "help", "stats", "loc", "comments");

$cliArgs = getopt($shortArgs, $longArgs);

if($cliArgs === false) {
  // Failure while reading arguments
  exit(10);
}

// Writing help
if(((isset($cliArgs['h'])) xor (isset($cliArgs['help']))) && (count($cliArgs) == 1)) {
  // Help argument without any value and accompanying arguments
  echo "IPP Project 1 - parse.php v2 help\n\nThis script takes input in IPPcode18 language and turns it into (hopefully) equivalent XML representation. Extension STATP is implemented too.\nFull assignment here: https://wis.fit.vutbr.cz/FIT/st/course-files-st.php?file=%2Fcourse%2FIPP-IT%2Fprojects%2F2017-2018%2FZadani%2Fipp18spec.pdf&cid=12180\n\nCOMPATIBILITY:\nThis script was intended to run on PHP 5.6.3.\n\nUSAGE:\nphp parse.php [ OPTIONS ] < input.src\nScript expects input on the standard command line input.\n\nOPTIONS:\n--stats=filename  This parameter enables statistics. Statistics will be printed after the script finishes into the specified file (must be used with --loc, --comments or both)\n--loc             This outputs number of lines with code into the statistic (can't be used w/o --stats)\n--comments        Prints number of comments into the statistic (can't be used w/o --stats)\n";
  exit(0);
}
else {
  if((isset($cliArgs['h']) || isset($cliArgs['help'])) && count($cliArgs) > 1) {
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

// Create new object for stats
$stats = new stats();
if(isset($cliArgs['stats'])) {
  $stats->changePath($cliArgs['stats']);
}

// Checking IPP header
$line = new codeLine();

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

// Reading from stdin - increment i, when the header was found, first for loop ended with break, thus not incrementing i
for($i = $i+1, $instNum = 0; ($line->text = fgets(STDIN)) !== false; $i++) {
  //fwrite(STDERR, "Iteration $i, line: $line->text\n"); //DIAG
  $line->number = $i;

  //Detecting empty lines and skipping them (empty line == only '\n' character)
  if(substr($line->text, 0, 1) == "\n") {
    //fwrite(STDERR, "Skipped empty line nr.$i\n"); //DIAG
    continue;
  }
  // Stripping new line characters returned by fgets
  $line->stripNewLine();

  $line->deleteComment($stats); // Deletes comments and counts code and comment lines
  if($line->text == "") {
    // If the line contained only a comment, it's empty now
    //fwrite(STDERR, "Skipped line $i\n"); //DIAG
    continue;
  }
  $token = $line->toToken();
  $token->checkArgs();

  // Increase instruction number - syntax is checked
  $instNum++;

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

// Write $stats
if(isset($cliArgs['stats'])) {
  $stats->writeFile($firstStat);
}

// Successful termination
exit(0);
//END OF MAIN BODY




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
    // NOTE: Empty lines are not passed here
    $exploded = preg_split("/(\s)*#/u", $this->text, 2);
    $this->text = $exploded[0];
    if($this->text == "") {
      // Line contains only a comment - call empty string detection after this
      // to catch newly empty lines
      $stats->addComment();
      return;
    }
    if(isset($exploded[0]) && !isset($exploded[1])) {
      // No '#' sign has to be present, so nothing is set in second match
      $stats->addCodeLine();
    }
    else {
      if(isset($exploded[0]) && isset($exploded[1])) {
        // Now it can be comment+code or comment only
        if($exploded[0] == "") {
          // Comment only lines don't get any match in first string
          $stats->addComment();
        }
        else {
          // Code+comment lines can't have empty first match
          $stats->addComment();
          $stats->addCodeLine();
        }
      }
    }
  }

  public function stripNewLine() {
    if(substr($this->text, -1) == "\n") {
      rtrim($this->text, "\n");
    }
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
  private $filePath; // Path to a file where stats should be printed

  /*****************************************************************************************
   * Function creates (or overwrites) a file at path specified in Arguments
   * Parameter firstStat determines which statistic should be written on a first line
   * of generated file
   ****************************************************************************************/
  public function writeFile($firstStat) {
    $this->code--; // Header was counted in
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
  public function addComment() {
    $this->comments++;
  }

  /*****************************************************************************************
   * Function increments number of lines with code in current file
   ****************************************************************************************/
  public function addCodeLine()  {
    $this->code++;
  }

  /*****************************************************************************************
   * This function sets a path to the file forom arguments in this object
   ****************************************************************************************/
  public function changePath($path) {
    $this->filePath = $path;
  }
}
?>
