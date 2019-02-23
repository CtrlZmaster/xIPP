<?php
/*
 * Project: IFJ Project 1 - IFJ17 compiler
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
$shortArgs  = "h::";
$longArgs  = array("help::", "stats::", "loc::", "comments::");

$cliArgs = getopt($shortArgs, $longArgs);

if($cliArgs === false) {
  // Failure while reading arguments
  exit(10);
}

// Writing help
if(((isset($cliArgs['h']) && $cliArgs['h'] === false) xor (isset($cliArgs['help']) && $cliArgs['help'] == false)) && (count($cliArgs) == 1)) {
  // Help argument without any value and accompanying arguments
  echo "This will turn into help eventually.\n";
  exit(0);
}
else {
    // No parameters
    //fwrite(STDERR, "Invalid arguments.\n");
    //exit(10);
}

// Invalid argument options
if((isset($cliArgs['loc']) || isset($cliArgs['comments'])) && (!isset($cliArgs['stats']) || (isset($cliArgs['stats']) && $cliArgs[stats] === false))) {
  // Arguments "loc" or "comments" on input and "stats" is missing or no file path was given
  fwrite(STDERR, "File path for statistics is undefined or argument \"--stats\" is missing entirely. Use \"-h\" or \"--help\" for more info.\n");
  exit(10);
}

// FILE PATH FOR STATISTICS (string) is in $cliArgs['stats']

if($header = fgets(STDIN)) {
  if(preg_match("/^(\s)*\.IPPcode18(\s)*$/ui", $header) === 0) {
    $line = __LINE__ + 1;
    fwrite(STDERR,"Line 1: Header is not \".IPPcode18\". Thrown at parse.php:$line.\n");
    return(21);
  }
}
// Create new object for stats
$stats = new stats();

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

// Reading from stdin
$line = new codeLine();
for($i = 2, $instNum = 0; ($line->text = fgets(STDIN)) !== false; $i++) {
  $line->number = $i;

  //Detecting empty lines and skipping them
  if(substr($line->text, 0, 1) == "\n") {
    continue;
  }
  // Stripping new line characters returned by fgets
  if(substr($line->text, -1) == "\n") {
    rtrim($line->text, "\n");
  }

  $line->deleteComment();
  if($line->text == "") {
    $stats->addComment();
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
    xmlwriter_start_element($xmlTemp, "arg$j");           // BEGIN ELEM Arg
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
// Successful termination
exit(0);
//END OF MAIN BODY




/*******************************************************************************************
 * TOKENS
 * This class implements the token and its functions.
 ******************************************************************************************/
class token {
  public $instWord; // ORDER 0
  public $args = array();
  public $types = array("none", "none", "none");
  public $lineNum;  // ORDER 4

  public function fillVal($order, $content) {
    switch($order) {
      case 0:
        $this->instWord = $content;
        break;
      case 1:
        $this->args[0] = $content;
        echo "token $this->instWord fillVal (1a)\narg 0 =>";
        var_dump($this->args[0]);
        echo "type 0 =>";
        var_dump($this->types[0]);
        echo"\n";
        break;
      case 2:
        $this->args[1] = $content;
        echo "token $this->instWord fillVal (1b)\narg 1 =>";
        var_dump($this->args[0]);
        echo "type 1 =>";
        var_dump($this->types[0]);
        echo"\n";
        break;
      case 3:
        $this->args[2] = $content;
        echo "token $this->instWord fillVal (1c)\narg 2 =>";
        var_dump($this->args[0]);
        echo "type 2 =>";
        var_dump($this->types[0]);
        echo"\n";
        break;
      case 4:
        $this->lineNum = $content;
        break;
      default:
        fwrite(STDERR,"Invalid call of fillVal - something tried to fill non-existent value in token.\n");
    }
  }

  // Checks syntax of an argument. Parameter index accetss index to argument array and content is a value
  // that should be checked. Argument array contains names of data types for comparison.
  public function checkArgs() {
    for($i = 0; $i < 3; $i++) {
      $imm = false; // Immediate value definition not yet matched, true when matched
      //fwrite(STDERR, "  opcode = $this->instWord, ArgOrder = $i, ArgVal = $this->args[$i]\n"); //DIAG
      switch($this->types[$i]) {
        case "symb":
          // Variable or immediate value - no break - NOT calling exit in this case
          // String, int, bool
          if(
             preg_match("/^string@(?:[^\s\\#@]|(\\[0-9]{3}))*$/u", $this->args[$i]) == 1 ||
             preg_match("/^int@(([+-][0-9]+)|([0-9]*))?$/u", $this->args[$i]) == 1 ||
             preg_match("/^bool@(true|false)?$/u", $this->args[$i]) == 1
            ) {
            $imm = true;
            $clean = preg_split("/@/u", $this->args[$i]);
            $this->args[$i] = $clean[1]; // Part after @
            $this->types[$i] = $clean[0]; // Part before @
          }
        case "var":
          if(preg_match("/^(GF|TF|LF)@(?:[[:alnum:]]|[_\-$&%*])+$/u", $this->args[$i]) == 0) {
            $line = __LINE__ + 1;
            echo "token $this->instWord checkArgs (2)\nargs $i => ";
            var_dump($this->args[$i]);
            echo "type $i =>";
            var_dump($this->types[$i]);
            fwrite(STDERR,"Line $this->lineNum: $this->args[$i] is not a valid variable. Thrown at parse.php:$line.\n");
            exit(21);
          }
          else {
            break;
          }

          if($imm == false) {
            $line = __LINE__ + 1;
            fwrite(STDERR,"Line $this->lineNum: This is not a valid immediate value. Thrown at parse.php:$line.\n");
            exit(21);
          }
          break;
        case "label":
          if(preg_match("/^(?:[[:alnum:]]|[_\-$&%*])+$/u", $this->args[$i]) == 0) {
            $line = __LINE__ + 1;
            fwrite(STDERR,"Line $this->lineNum: This is not a valid label. Thrown at parse.php:$line.\n");
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
   * This function takes a line of code and explodes it into lexemes. It also checks that
   * there are no ivalid characters on the line.
   ****************************************************************************************/
  public function toToken() {
    $lexemes = preg_split("/\s+/u", $this->text);
    $token = new token();

    // preg_split returns empty string on zeroth index when white spaces are
    // in front of the string - $offset solves that by ignoring empty string there is one
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
        $line = __LINE__ + 1;
        fwrite(STDERR,"Line $this->number: Unrecognized instruction. Thrown at parse.php:$line.\n");
        break;
    }
    $this->fillToken($token, $lexemes);
    return $token;
  }

  // This function helps to find empty string generated by preg_split when white spaces
  // are in front of an instruction
  private function firstLexemeIndex($lexemes) {
    if(isset($lexemes[0]) && $lexemes[0] = "" ) {
      return 1;
    }
    else {
      return 0;
    }
  }

  // This method fills the token with arguments from a code line. It also checks argument types
  // and their count.
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
        $line = __LINE__ + 1;
        fwrite(STDERR,"Line $this->number: Too many arguments. Thrown at parse.php:$line.\n");
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
  }

  public function deleteComment() {
    $exploded = preg_split("/(\s)*#/u", $this->text);
    $this->text = $exploded[0];
  }
}

class stats {
  private $code;
  private $comments;

  public function write() {
    echo "STATS";
  }

  public function addComment() {
    $this->comments++;
  }

  public function addCodeLine()  {
    $this->comments++;
  }
}
?>
