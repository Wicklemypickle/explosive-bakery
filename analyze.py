import sys
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import csv
import os
import json

##############
## Script analyzes thrust signal
##############
## requires matplotlib, numpy, scipy to be installed


###################################################################
#                       CONFIG
###################################################################

SG_WINDOW_SIZE =    51
SG_ORDER =          5
SHOW_PLOT =         True

###################################################################
#                       FUNCTIONS
###################################################################

def json_sort(opts):
    from collections import OrderedDict as OD
    skeys = ['date', 'serial_port', 'baud_rate', 'rocket_length', 'rocket_diameter',
             'rocket_material', 'rocket_fuel_mass', 'rocket_mass', 'fuel_type',
             'nozzle_used', 'left_endpoint', 'right_endpoint', 'filename',
             'comments', 'data']
    return OD(sorted(opts.iteritems(), key=lambda x: skeys.index(x[0])))

def onclick(event):
    if not event.dblclick:
        return

    global ix, iy
    ix, iy = event.xdata, event.ydata
    # print 'x = %d, y = %d'%(ix, iy)

    global coords
    coords.append((ix, iy))
    if len(coords) == 1:
        print 'Double click on right endpoint'
    if len(coords) == 2:
        fig.canvas.mpl_disconnect(cid)
        plt.close()

    return coords

def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    """Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    from math import factorial

    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')

def integrate(x, y, yshift):
    if len(x) != len(y):
        print 'x length: %s' % len(x)
        print 'y length: %s' % len(y)
        raise Exception('cannot integrate x and y of different length')

    area = 0.0
    for i in range(len(x))[0:-2]:
        x1 = x[i]
        x2 = x[i+1]
        y1 = y[i]
        y2 = y[i+1]
        dx = x2 - x1
        area += dx * ((y1 + y2) / 2.0)

    return area + ((x[-1] - x[0]) * yshift)

###################################################################
#                       HERE'S THE SCRIPT
###################################################################

if len(sys.argv) < 2:
    print 'Must run with format:'
    print 'python analyze.py <file-name.json>'
    sys.exit(0)

file_name = os.path.abspath(sys.argv[1])
print file_name
trial = os.path.basename(os.path.split(file_name)[0])
if not os.path.exists(file_name):
    print 'File not found.'
    sys.exit(0)

# read in all the data
f = open(file_name)
opts = json.load(f)
if 'left_endpoint' not in opts and 'right_endpoint' not in opts:
    fig = plt.figure()
    ax = fig.add_subplot(111)
    coords = []
    ax.plot(opts['data']['ms'], opts['data']['thrusts'], label='Thrust timeseries')
    plt.legend()
    print 'Double click on left coordinate'
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    left = coords[0][0]
    right = coords[1][0]
    if left > right:
        print 'Warning: left endpoint greater than right endpoint...'
        print 'Dataset will be empty.'

    opts['left_endpoint'] = left
    opts['right_endpoint'] = right
    f.close()
    json.dump(json_sort(opts), open(file_name, 'w'), indent=2)

# convert to numpy array
raw_time = opts['data']['ms']
raw_thrust = opts['data']['thrusts']
thrust_times = []
thrust_vals = []
for i in range(len(raw_time)):
    time = raw_time[i]
    if time > opts['left_endpoint'] and time < opts['right_endpoint']:
        thrust_times.append(raw_time[i])
        thrust_vals.append(raw_thrust[i])


thrust_times = np.array(thrust_times)
thrust_vals = np.array(thrust_vals)

num_data_points = len(thrust_times)
if not num_data_points:
    print 'No data points'
    sys.exit(0)
else:
    smooth_thrust = savitzky_golay(thrust_vals, SG_WINDOW_SIZE, SG_ORDER)
    print len(smooth_thrust)

try:
    impulse = integrate(thrust_times,
                        smooth_thrust,
                        yshift=-1.0 * (min(smooth_thrust)))
except Exception:
    impulse = integrate(thrust_times,
                        thrust_vals,
                        yshift=-1.0 * (min(thrust_vals)))

print 'NUMBER OF DATA POINTS:\t%s' % (num_data_points)
print 'MEASUREMENT FREQUENCY:\t%s hz' % (num_data_points/(float(thrust_times[-1]) - float(thrust_times[0])))
print 'AVERAGE THRUST:\t\t%s g' % np.mean(thrust_vals)
print 'MASS BURNED:\t\t%s g' % abs(thrust_vals[-1] - thrust_vals[0])
print 'IMPULSE:\t\t%s g*s' % impulse

ax = plt.axes()
ax.plot(thrust_times, thrust_vals, color=(1,0,0,0.2), label='Original signal')
ax.plot(thrust_times, smooth_thrust, color=(.4, 0.2, 1,1), label='Smoothed signal')
plt.legend()
plt.xlabel('Time (s)')
plt.ylabel('Thrust (g)')
plt.title('Thrust for trial "%s"' % trial)
plt.savefig('%s/thrust-timeseries.png' % os.path.split(file_name)[0])


plt.show()

