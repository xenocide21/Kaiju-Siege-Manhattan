#!/usr/bin/env python3
"""Run harness with symbolic names: '@frame' in script -> address of _frame."""
import sys, re, subprocess, os
here = os.path.dirname(os.path.abspath(__file__))
sym = {}
for line in open(os.path.join(here, '../src/kaiju.sym')):
    p = line.split()
    if len(p) >= 3 and p[2].startswith('_'):
        sym[p[2][1:]] = p[1]
script = sys.stdin.read()
script = re.sub(r'@(\w+)', lambda m: sym[m.group(1)], script)
open('/tmp/script.txt', 'w').write(script)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '../shots')
subprocess.run([os.path.join(here, os.environ.get('HARNESS','harness')), os.path.join(here, '../src/kaiju.pce'), '/tmp/script.txt', out])
