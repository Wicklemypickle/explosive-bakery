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
import argparse

test = False

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cli", action='store_true', default=False,
    help='Use command line interface')
ap.add_argument("-n", "--name", 
    help='The name by which to save this test')
args = vars(ap.parse_args())


if args['cli']: options = set_options.get_opt_dict()
else: options = set_options.get_defaults()

# make a folder for today
date = datetime.datetime.now()
date_folder = date.strftime('%y-%m-%d')
os.mkdir(date_folder) if not os.path.exists(date_folder) else None


trial_folder = args['name']
while True:
    if trial_folder is None: trial_folder = raw_input('Input trial name: ')
    path = '%s/%s' % (date_folder, trial_folder)
    if not os.path.exists(path):
        break
    else:
        print 'Trial {} already exists.'.format(trial_folder)
        trial_folder = None

fname = trial_folder + '-data.json'
file_path = '%s/%s' % (path, fname)
try:
    raw_input('\nPress enter to begin logging, or <ctrl-c> to exit.\n')
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
    print '############         {}          ############'.format(trial_folder)
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
            ser.close()
            break

os.mkdir(path)

options['filename'] = fname
options['date'] = date.strftime('%y-%m-%d-%H-%M-%S')
options['data']['ms'] = times
options['data']['thrusts'] = thrusts

json.dump(set_options.json_sort(options), open(file_path, 'w'), indent=2)

print '\nLogging complete.'
print 'Analyze now? [y/n]'
if raw_input('> ') == 'y':
    os.system('python %s/analyze.py "%s"' % (os.path.abspath(os.curdir), file_path))

