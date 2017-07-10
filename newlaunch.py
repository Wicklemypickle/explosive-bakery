##############
## Script listens to serial port and writes contents into a file.
##############
## requires pySerial to be installed 

import serial
import sys
import datetime
import set_options
import json
import os
import csv

test = False

def json_sort(opts):
    from collections import OrderedDict as OD
    skeys = ['date', 'serial_port', 'baud_rate', 'rocket_length',
             'rocket_diameter', 'rocket_material', 'rocket_fuel_mass', 'rocket_mass',
             'fuel_type', 'nozzle_used', 'left_endpoint', 'right_endpoint',
             'comments', 'data']
    return OD(sorted(opts.iteritems(), key=lambda x: skeys.index(x[0])))

options = set_options.get_opt_dict()
date = datetime.datetime.now()
date_folder = date.strftime('%y-%m-%d')
os.mkdir(date_folder) if not os.path.exists(date_folder) else None

while True:
    trial_folder = raw_input('Input trial name: ')
    path = '%s/%s' % (date_folder, trial_folder)
    if not os.path.exists(path):
        # os.mkdir(path)
        break
    else:
        print 'Trial already exists.'

fname = trial_folder + '-data.json'
file_path = '%s/%s' % (path, fname)
try:
    raw_input('\nPress enter to begin logging, or <ctrl-c> to exit.\n')
    os.mkdir(path)
except KeyboardInterrupt:
    sys.exit(0)

if test:
    times = []
    thrusts = []
    file_name = raw_input('TEST MODE ENABLED. Enter a filename for the CSV: ')
    try:
        input_file = open(file_name, "r")
        for line in csv.reader(input_file):
            times.append(float(line[0])/1000.0)
            thrusts.append(float(line[1]))
    except IOError as e: 
        print e
        sys.exit(1)
else:
    ser = serial.Serial(options['serial_port'], options['baud_rate'])
    print ser.readline().strip()
    times = []
    thrusts = []
    while True:
        try:
            line = ser.readline();
            line = line.decode('utf-8') #ser.readline returns a binary, convert to string
            sys.stdout.write('\r' + line.strip() + '\t\t\t\t')
            sys.stdout.flush()
            pretty_line = line.split(',\t')
            times.append(float(pretty_line[0]) / 1000.0)
            thrusts.append(float(pretty_line[1].strip()))
        except KeyboardInterrupt:
            break

options['filename'] = fname
options['date'] = date.strftime('%y-%m-%d-%H-%M-%S')
options['data']['ms'] = times
options['data']['thrusts'] = thrusts

json.dump(json_sort(options), open(file_path, 'w'), indent=2)

print '\nLogging complete.'
print 'Analyze now? [y/n]'
if raw_input('> ') == 'y':
    os.system('python %s/analyze.py "%s"' % (os.path.abspath(os.curdir), file_path))

