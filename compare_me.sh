#!/usr/bin/env bash
python calculate.py > me.txt
python calculateAverage.py > them.txt

git diff --no-index --word-diff me.txt them.txt
