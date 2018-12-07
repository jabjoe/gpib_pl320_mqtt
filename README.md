Introduction
------------

This is a quick test of using MQTT to control an old Thurlby PL320 power supply over Prologix's USB GPIB.


MQTT messages
-------------

kit/pl320/mV             # The millivolts the power supply is set to.

kit/pl320/mA             # The milliamps the power supply current limit is set to.

kit/pl320/set_mV         # Change the millivolts the power supply is set to.

kit/pl320/set_mA         # Change the milliamps the power supply current limit is set to.


kit/pl320/read_used      # If the controller is set to read the used current.

kit/pl320/set_read_used  # Change if the controller is set to read the used current.

kit/pl320/used_mA        # The used current, or zero if not set to be read.



Running Test
------------

It is called with the arguments:

    <ssl host> <port> <username> <password> <tty> <GPIB addr>

The SSL host with the broker, which obviously must be SSL.

The port will normally 8883 as it's a SSL broker.

The username and password explain themselves.

The tty is the serial port the GPIB is under.

The GPIB address is the address set on the back of the Thurlby PL320 power supply.
