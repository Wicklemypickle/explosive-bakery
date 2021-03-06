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
import numpy as np

TEST_MODE = True
IMPORT_CSV = True

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--cli", action='store_true', default=False,
    help='Use command line interface')
ap.add_argument("-n", "--name", 
    help='The name by which to save this test')
ap.add_argument("--nozzle", action='store_true', default=True)
ap.add_argument("--no-nozzle", action='store_false', dest='nozzle')
ap.add_argument("-l", "--length", type=float,
    help='rocket length')
ap.add_argument("-d", "--diameter", type=float,
    help='rocket diameter')
ap.add_argument('--date', help='The date on which the test occured. YY-MM-DD.')
args = vars(ap.parse_args())

# populate the test options JSON with cl args
options = set_options.get_defaults()
if args['nozzle'] is not None: options['nozzle_used'] = args['nozzle']
if args['diameter'] is not None: options['rocket_diameter'] = args['diameter']
if args['length'] is not None: options['rocket_length'] = args['length']

# allow the use of the CLI if requested
if args['cli']: options = set_options.get_opt_dict(options=options)

# make a folder for today
date = datetime.datetime.now()
date_folder = date.strftime('%y-%m-%d') if args['date'] is None else args['date']
new_date_folder_created = os.mkdir(date_folder) if not os.path.exists(date_folder) else False

# ensure we have a valid subfolder name in which to store the test
trial_folder = args['name']
while True:
    if trial_folder is None: trial_folder = raw_input('Input trial name: ')
    path = '%s/%s' % (date_folder, trial_folder)
    if not os.path.exists(path):
        try:
            os.mkdir(path)
            break
        except:
            print 'Failed to create {}'.format(trial_name)
            trial_folder = None
    else:
        print 'Trial {} already exists.'.format(trial_folder)
        trial_folder = None
fname = trial_folder + '-data.json'
file_path = '%s/%s' % (path, fname)

try: raw_input('\nPress enter to begin logging, or <ctrl-c> to exit.\n')
except KeyboardInterrupt:
    os.rmdir(path) # if the user cancels the test, remove the test folder
    sys.exit(0)


# collect data from the serial port
if not TEST_MODE:
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
elif IMPORT_CSV:
    times = []
    thrusts = []
    file_name = raw_input('CSV CONVERT ENABLED. Enter a filename for the CSV: ')
    try:
        input_file = open(file_name.strip(), "r")
        for line in csv.reader(input_file):
            times.append(float(line[0])/1000.0)
            thrusts.append(float(line[1]))
    except IOError as e: 
        print e
        sys.exit(1)
else:
    print 'Spoofing some test data for ya! ;)'
    times = np.array(range(1,100)) * 11.0
    thrusts = np.random.random(100) * 100.0

# add the test results to the JSON
options['filename'] = fname
options['date'] = date.strftime('%y-%m-%d-%H-%M-%S')
options['data']['ms'] = times
options['data']['thrusts'] = thrusts
# and organize the JSON
json.dump(set_options.json_sort(options), open(file_path, 'w'), indent=2)

# perform analysis if requested
print '\nLogging complete.'
print 'Analyze now? [y/n]'
if raw_input('> ') == 'y':
    os.system('python %s/analyze.py "%s"' % (os.path.abspath(os.curdir), file_path))

