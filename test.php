<?php
/*
 * Project: IPP Project 1
 * File: test.php
 * Title: Lexical and syntax analyser of IPPcode18
 * Description: This script performs testing of parse.php and interpret.py
 * Author: Michal Pospíšil (xpospi95@stud.fit.vutbr.cz)
 */

 // Arguments handling
 // This script accepts only --help parameter
 $shortArgs  = "h";
 $longArgs  = array("help", "directory::", "recursive", "parse-script::", "int-script::");

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
 if(isset($cliArgs[directory]) && isset($cliArgs[directory])) {
   // Arguments "loc" or "comments" on input and "stats" is missing or no file path was given
   fwrite(STDERR, "File path for statistics is undefined or argument \"--stats\" is missing entirely. Use \"-h\" or \"--help\" for more info.\n");
   exit(10);
 }
 ?>
