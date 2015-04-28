#!/bin/bash
code-sniffer --config code-plagiarism.conf
sh summary.sh
sh accused.sh
