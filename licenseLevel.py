#!/bin/python
"""Collect and print current Abaqus license usage information

Usage:
    abaqus python licenseLevel.py

Carl Osterwisch, May 2024
"""

from __future__ import print_function

# Customize following line for the trigrams desired in report
report = ('QAX', 'QXT', 'SRU', 'SUN')

def dslsstat():
    "Collect current license usage data using dslsstat"
    import re
    import subprocess
    from subprocess import Popen, PIPE
    import sys
    cmd = 'abaqus licensing dslsstat -usage'
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if sys.version_info.major >= 3:
        stdout_data, stderr_data = proc.communicate(timeout=60)
    else:
        # timeout unsupported in Abaqus < 2024
        stdout_data, stderr_data = proc.communicate()

    summary = {'error': stderr_data.decode()}
    if proc.returncode:
        summary['error'] += stdout_data.decode()
    beyondHeader = False
    feature = None
    for line in stdout_data.decode().split('\n'):
        if not beyondHeader:
            if line.startswith('Licenses:'):
                beyondHeader = True
        elif line.startswith('+'):
            if 'Feature' in line:
                # collect column headings
                headings = [column.strip().lower() for column in line[1:].split('|')]
        elif line.startswith('|'):
            # collect feature status
            columns = [column.strip() for column in line[1:].split('|')]
            row = {heading: value for heading, value in zip(headings, columns)}
            feature = summary.setdefault(row['feature'], {})
            row['number'] = int(row['number']) + feature.get('number', 0) # cumulative
            row['inuse'] = int(row['inuse']) + feature.get('inuse', 0) # cumulative
            feature.update(row)
        elif feature and 'using' in line:
            # collect detailed usage data from lines following feature
            usage = feature.setdefault('usage', [])
            usage.append(re.sub('\(.+, ', '', line.strip()))
    return summary

def printSummary():
    "Print license status to stdout"
    summary = dslsstat()
    if 'error' in summary:
        print(summary['error'])
    for trigram in report:
        feature = summary.get(trigram)
        if feature is None:
            continue
        print(trigram, feature['inuse'], 'in use of', feature['number'])
        for line in feature.get('usage', []):
            print('\t' + line)

if __name__ == '__main__':
    printSummary()
