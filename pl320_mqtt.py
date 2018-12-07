#! /usr/bin/python3

import os
import sys
import time
import serial
import paho.mqtt.client as paho

_debug = False


class prologix_t(object):
    def __init__(self, com_port, addr):
        self._dev = serial.Serial(com_port, baudrate=9600, timeout=1)
        self._eol = "\n"
        self._addr = addr

        self._raw_write("++mode 1")
        self._raw_write("++ifc")
        self._raw_write("++read_tmo_ms 200")
        self._raw_write("++ver")
        lines = self._raw_read()
        assert len(lines) > 1
        assert lines[0] == b"Prologix GPIB-USB Controller version 6.107"

    def _raw_write(self, cmd):
        self._dev.write(cmd.encode() + self._eol.encode())

    def _raw_read(self):
        self._raw_write("++read")
        raw_lines = self._dev.readlines()
        return [line.rstrip() for line in raw_lines]

    def send(self, cmd):
        self._raw_write('++addr %u' % self._addr)
        self._raw_write(cmd)

    def sendrcv(self, cmd):
        self.send(cmd)
        return self._raw_read()



class pl320_t(object):
    def __init__(self, com_port, addr):
        self._dev = prologix_t(com_port, addr)
        self._mV = 0
        self._mA = 0
        self._mA_used = 0
        self.milli_voltage = 0
        self.milli_amps = 0

    @property
    def milli_voltage(self):
        return self._mV

    @milli_voltage.setter
    def milli_voltage(self, mV):
        self._dev.send("X%umV" % mV)
        self._mV = mV

    @property
    def milli_amps(self):
        return self._mA

    @milli_amps.setter
    def milli_amps(self, mA):
        self._dev.send("X%umA" % mA)
        self._mA = mA

    @property
    def used_milli_amps(self):
        lines = self._dev.sendrcv("XI?")
        if len(lines) == 1:
            line = lines[0]
            assert line.endswith(b"mA")
            self._mA_used = int(line[0:-2])
        else:
            print("lines", lines)
        return self._mA_used

pl320_mV = "kit/pl320/mV"
pl320_mA = "kit/pl320/mA"

pl320_set_mV = "kit/pl320/set_mV"
pl320_set_mA = "kit/pl320/set_mA"

pl320_read_used = "kit/pl320/read_used"
pl320_set_read_used = "kit/pl320/set_read_used"
pl320_used_mA = "kit/pl320/used_mA"


class power_supply_t(object):
    def __init__(self, broker, port, username, password, com_port, addr):
        self._dev = pl320_t(com_port, addr)
        self.client = paho.Client("PL320")
        self.client.tls_set()
        self.client.username_pw_set(username, password)
        self.client.connect(broker, port)
        self.client.on_message = lambda c, u, m : self._on_message(u, m)

        self.client.subscribe(pl320_set_mV)
        self.client.subscribe(pl320_set_mA)
        self.client.subscribe(pl320_set_read_used)
        self._read_used = False
        self._update_others()


    def _output(self, topic, value):
        self.client.publish(topic, value)
        if _debug:
            print(topic, value)

    def _update_others(self):
        self._output(pl320_used_mA,
            self._dev.used_milli_amps if self._read_used else 0)
        self._output(pl320_mV, self._dev.milli_voltage)
        self._output(pl320_mA, self._dev.milli_amps)
        self._output(pl320_read_used, self._read_used)

    def _on_message(self, userdata, message):

        if _debug:
            print(message.topic, "=", message.payload)

        if message.topic == pl320_set_mV:
            self._dev.milli_voltage = int(message.payload)

        if message.topic == pl320_set_mA:
            self._dev.milli_amps = int(message.payload)

        if message.topic == pl320_set_read_used:
            self._read_used = message.payload == b"True"

        self._update_others()

    def loop(self):
        self.client.loop()
        self._update_others()

    def finish(self):
        self.client.disconnect()

    def is_running(self):
        return True


def main():

    if len(sys.argv) < 7:
        print("<ssl host> <port> <username> <password> <tty> <GPID addr>")
        sys.exit(-1)

    if os.getenv("DEBUG"):
        global _debug
        _debug = True

    hostname   = sys.argv[1]
    port       = int(sys.argv[2])
    username   = sys.argv[3]
    password   = sys.argv[4]
    tty_device = sys.argv[5]
    gpid_addr  = int(sys.argv[6])

    power_supply = power_supply_t(hostname,
                                  port,
                                  username,
                                  password,
                                  tty_device,
                                  gpid_addr)
    print("Running")

    while power_supply.is_running():
        power_supply.loop()
        time.sleep(0.5)

    power_supply.finish()


if __name__ == "__main__":
    main()



