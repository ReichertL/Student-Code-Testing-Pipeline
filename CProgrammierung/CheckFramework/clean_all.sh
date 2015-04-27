#!/bin/bash
find . -type f -name '*.app' -delete
find . -type f -name '*.allocated' -delete
find . -type f -name '*.valgrind' -delete
find . -type f -name '*.result' -delete
find . -type f -name '*.analysis' -delete

rm sniffer.sqli*
rm *.csv
rm *.ps