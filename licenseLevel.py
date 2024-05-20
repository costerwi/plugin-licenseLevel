#!/bin/python
"""Collect and print current Abaqus license usage information

Usage:

    abaqus python licenseLevel.py [--all] [trigram...]

Carl Osterwisch, May 2024
https://github.com/costerwi/plugin-licenseLevel
"""

from __future__ import print_function
import sys

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

def printSummary(trigrams=[]):
    "Print license status to stdout"
    licenseFeatures = dslsstat()
    error = licenseFeatures.get('error')
    if error:
        print(error)
    if not trigrams:
        # use default Abaqus list
        trigrams = 'QAT', 'QPT', 'QXT', 'SRU', 'SUN', 'QAX'
    elif '--all' in trigrams:
        # report all available features
        trigrams = sorted(licenseFeatures.keys())
    for trigram in trigrams:
        featureData = licenseFeatures.get(trigram.upper())
        if featureData is None:
            continue
        print(trigram,
            featureData['number'] - featureData['inuse'],
            'available of',
            featureData['number'],
            featureData['model'].lower() + 's')
        for line in featureData.get('usage', []):
            print('\t' + line)

if __name__ == '__main__':
    if '--help' in sys.argv:
        sys.exit(__doc__)
    # use trigrams specified on command line, if any
    printSummary(sys.argv[1:])
