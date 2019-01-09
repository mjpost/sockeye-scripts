#!/usr/bin/perl

use utf8;
use strict;

# Force UTF8 on all streams
binmode STDIN, ":encoding(UTF-8)";
binmode STDOUT, ":encoding(UTF-8)";

while ($_ = <>) {
  chomp;
  s/(\p{Han})/ \1 /g; 
  s/ +/ /g; 
  s/^ //; 
  s/ $//;
  print "$_\n";
}
