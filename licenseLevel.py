#!/bin/python
"""Collect and print current Abaqus license usage information

Usage:

    abaqus python licenseLevel.py [--all] [trigram...]

Carl Osterwisch, May 2024
https://github.com/costerwi/plugin-licenseLevel
"""

from __future__ import print_function, with_statement
from io import StringIO
import itertools
import re
import sys

class UsageLine(object):
    "Convenience class for working with license usage strings"

    sequence_iter = itertools.count() # running total of class instances

    def __init__(self, line):
        self.line = str(line).strip()
        self.sequence = next(self.sequence_iter) # used to preserve order

    @property
    def jobId(self):
        "Extract unique job Id from raw usage line"
        m = re.match('.+ using', self.line)
        if m:
            return m.group(0)
        return ''

    @property
    def licenses(self):
        "Return int number of licenses"
        m = re.search('(\d+) licenses', self.line)
        if m:
            return int(m.group(1))
        return 0

    @licenses.setter
    def licenses(self, n):
        "Set number of licenses"
        self.line = re.sub('\d+ license', '{} license'.format(n), self.line)

    def __lt__(self, other):
        return self.sequence < other.sequence

    def __str__(self):
        "Return abreviated string with jobId removed"
        return re.sub('\(.+, ', '', self.line)


def dslsstat():
    "Collect current license usage data using dslsstat"
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
    stderr = stderr_data.decode()
    if proc.returncode:
        stderr += stdout_data.decode()
    return summarize(StringIO(stdout_data.decode()), StringIO(stderr))


def summarize(stdout, stderr=None):
    "Parse streams of dslsstat data and return summary dict"
    summary = {}
    if stderr:
        summary['error'] = '\n'.join(stderr.readlines())
    beyondHeader = False
    feature = None
    for line in stdout:
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
            usage = feature.setdefault('usage', {}) # jobId: UsageLine
            usageLine = UsageLine(line)
            previousUsage = usage.get(usageLine.jobId)
            if previousUsage is None:
                usage[usageLine.jobId] = usageLine
            else:
                # Accumulate license usage for the same jobId
                previousUsage.licenses += usageLine.licenses
    for trigram, data in summary.items():
        # Convert usage dict to ordered list of strings
        if not 'usage' in data:
            continue
        usage = data.get('usage')
        data['usage'] = [str(usageLine) for usageLine in sorted(usage.values())]
    return summary


def printSummary(trigrams=[]):
    "Print license status to stdout"
    if sys.stdin.isatty():
        licenseFeatures = dslsstat()
    else:
        # read from pipe
        licenseFeatures = summarize(sys.stdin)
    error = licenseFeatures.get('error')
    if error:
        print(error)
    if not trigrams:
        # use default Abaqus list
        trigrams = 'QAT', 'QPT', 'QXT', 'SRU', 'SUN', 'QAX', 'QSI', 'QPA'
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
