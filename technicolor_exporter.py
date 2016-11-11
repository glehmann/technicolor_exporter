#!/usr/bin/env python

import re
import telnetlib
import time

from prometheus_client import start_http_server, Metric, REGISTRY


host = '192.168.1.254'
user = 'Administrator'
password = ''


class TechnicolorConnection(object):
    def __init__(self):
        self.connect()

    def read_until_prompt(self):
        prompt = '{Administrator}=>'.encode('ascii')
        return self.tn.read_until(prompt)[:-len(prompt)].decode('ascii')

    def run(self, command):
        command += '\r\n'
        self.tn.write(command.encode('ascii'))
        return self.read_until_prompt()[len(command):]

    def connect(self):
        self.tn = telnetlib.Telnet(host)
        self.tn.read_until('Username : '.encode('ascii'))
        self.tn.write((user + '\r\n').encode('ascii'))
        self.tn.read_until('Password : '.encode('ascii'))
        self.tn.write((password + '\r\n').encode('ascii'))
        self.read_until_prompt()

    def internet_stats(self):
        ref = r'''Interface                            Group  MTU   RX         TX         Admin  Oper.+
\d+   Internet. . . . . . . . . . . .  (?P<group>\S+) +(?P<mtu>\d+) +(?P<rx>\d+) (?P<rx_unit>\S+) +(?P<tx>\d+)+ (?P<tx_unit>\S+) +(?P<admin>\S+) +(?P<oper>\S+).+
    Lower-Intf    : .+
    Encapsoverhead: (?P<encapsoverhead>\d+).+
    Flags         : (?P<flags>[A-Z0-9 ]*).+
    IPv4.+
       Flags         : (?P<ipv4_flags>[A-Z0-9 ]*).+
       RX unicastpkts: (?P<ipv4_rx_unicastpkts>\d+) +brcastpkts : (?P<ipv4_rx_brcastpkts>\d+) +mcastpkts : (?P<ipv4_rx_mcastpkts>\d+).+
       TX unicastpkts: (?P<ipv4_tx_unicastpkts>\d+) +brcastpkts : (?P<ipv4_tx_brcastpkts>\d+) +mcastpkts : (?P<ipv4_tx_mcastpkts>\d+) +droppkts: (?P<ipv4_tx_droppkts>\d+).+
       TX singlepkts: (?P<ipv4_tx_singlepkts>\d+) +multiplepkts: (?P<ipv4_tx_multiplepkts>\d+).+
    IPv6.+
       Flags         : (?P<ipv6_flags>[A-Z0-9 ]*).+
       curhoplimit : (?P<ipv6_curhoplimit>\d+) +dadtransmits : (?P<ipv6_dadtransmits>\d+) +retranstimer : (?P<ipv6_retranstimer>\d+) (?P<ipv6_retranstimer_unit>\S+).+
       RX unicastpkts: (?P<ipv6_rx_unicastpkts>\d+) +brcastpkts : (?P<ipv6_rx_brcastpkts>\d+) +mcastpkts : (?P<ipv6_rx_mcastpkts>\d+) +droppkts: (?P<ipv6_rx_droppkts>\d+).+
       TX unicastpkts: (?P<ipv6_tx_unicastpkts>\d+) +brcastpkts : (?P<ipv6_tx_brcastpkts>\d+) +mcastpkts : (?P<ipv6_tx_mcastpkts>\d+) +droppkts: (?P<ipv6_tx_droppkts>\d+).+
       TX singlepkts: (?P<ipv6_tx_singlepkts>\d+) +multiplepkts: (?P<ipv6_tx_multiplepkts>\d+).+
'''
        res = self.run(':ip iflist intf=Internet')
        rres = re.search(ref, res)
        return rres.groupdict()

    # print(run(tn, ':xdsl info'))

    def exit(self):
        self.run('exit')


class TechnicolorCollector(object):
    def collect(self):
        conn = TechnicolorConnection()
        internet_metrics = conn.internet_stats()
        conn.exit()
        print(internet_metrics)
        metric = Metric('technicolor_internet', 'Internet metrics', 'gauge')
        for k in sorted(internet_metrics.keys()):
            v = internet_metrics[k]
            if v.isdigit():
                metric.add_sample('technicolor_internet_' + k, value=float(v), labels={})
        metric.add_sample('technicolor_internet_admin', value=1 if internet_metrics['admin'] == 'UP' else 0, labels={})
        metric.add_sample('technicolor_internet_oper', value=1 if internet_metrics['oper'] == 'UP' else 0, labels={})

        yield metric


if __name__ == '__main__':
    start_http_server(54324)
    REGISTRY.register(TechnicolorCollector())

    while True:
        time.sleep(1)
