# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import sys
import time
import pika

import Adafruit_MPR121.MPR121 as MPR121

print('Iceberg Facet Sensor')

cap = MPR121.MPR121()

if not len(sys.argv) > 1:
    print('Iceberg id must be specified!')
    sys.exit(1)

currentTimeMillis = lambda: int(round(time.time() * 1000))

icebergId = sys.argv[1];
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='events', type='topic')

# Initialize communication with MPR121 using default I2C bus of device, and
# default I2C address (0x5A).  On BeagleBone Black will default to I2C bus 0.
if not cap.begin():
    print('Error initializing MPR121.  Check your wiring!')
    sys.exit(1)

# Alternatively, specify a custom I2C address such as 0x5B (ADDR tied to 3.3V),
# 0x5C (ADDR tied to SDA), or 0x5D (ADDR tied to SCL).
# cap.begin(address=0x5B)

# Also you can specify an optional I2C bus with the bus keyword parameter.
# cap.begin(busnum=1)

# Main loop to print a message every time a pin is touched.
print('Press Ctrl-C to quit.')
last_touched = cap.touched()

while True:

    current_touched = cap.touched()

    # Check each pin's last and current state to see if it was pressed or released.
    for i in range(12):

        # Each pin is represented by a bit in the touched value.  A value of 1
        # means the pin is being touched, and 0 means it is not being touched.
        pin_bit = 1 << i

        # First check if transitioned from not touched to touched.
        if current_touched & pin_bit and not last_touched & pin_bit:
            print('{0} touched!'.format(i))
            channel.basic_publish(exchange='events', routing_key=('{}.{}.touch.event'.format(icebergId, i)),
                                  body='{{"type":"TOUCH","sensorNumber":{},"icebergId":"{}","touched":true,"time":{}}}'.
                                  format(i, icebergId, currentTimeMillis()))

        # Next check if transitioned from touched to not touched.
        if not current_touched & pin_bit and last_touched & pin_bit:
            print('{0} released!'.format(i))
            channel.basic_publish(exchange='events',
                                  routing_key=('{}.{}.touch.event'.format(icebergId, i)),
                                  body=
                                  '{{"type":"TOUCH","sensorNumber":{},"icebergId":"{}","touched":false,"time":{}}}'.
                                  format(i, icebergId, currentTimeMillis()))

    # Update last state and wait a short period before repeating.
    last_touched = current_touched
    time.sleep(0.1)
