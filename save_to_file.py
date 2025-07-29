import asyncio
import json

from concurrent.futures import ThreadPoolExecutor

import aiofiles as aiofiles
from easysnmp import EasySNMPTimeoutError, Session

IP_ADDRESS = (
    'x.x.x.x'
)


class MySnmp:

    def __init__(self, ip):
        self.response_model = None
        self.__session = Session(hostname=str(ip), community='cisco123', version=2, timeout=2, retries=1)

    def get_name(self):
        try:
            response_name = self.__session.get('.1.3.6.1.2.1.1.5.0').value
            if "EPON" in response_name or "GPON" in response_name:
                self.response_model = response_name
                return response_name
        except EasySNMPTimeoutError:
            pass

    def get_ports(self):

        self.count = 0
        self.response_model = self.__session.get('.1.3.6.1.2.1.1.1.0').value
        if 'BDCOM(tm) P3310C' in self.response_model or 'BDCOM(tm) P3310D' in self.response_model or 'ELTEX LTP-4X-rev.C' in self.response_model:
            self.count = 4
            return self.count
        else:
            self.count = 8
            return self.count

    def get_onu_quantity(self):
        data = {}
        self.__session.use_numeric = True
        if 'BDCOM' in self.response_model:
            self.__session.timeout = 1
            result_epon = self.__session.walk('1.3.6.1.4.1.3320.101.11.4.1.5')
            for epon in result_epon:
                if self.count == 4:
                    epon_port = int(epon.oid.split('.')[-1]) - 14
                    # print(epon_port)
                    data[epon_port] = data.setdefault(epon_port, 0) + 1
                else:
                    if 'P3608B' in self.response_model:
                        epon_port = int(epon.oid.split('.')[-1]) - 75
                    else:
                        epon_port = int(epon.oid.split('.')[-1]) - 46
                    data[epon_port] = data.setdefault(epon_port, 0) + 1

        else:
            result_gpon = self.__session.walk(".1.3.6.1.4.1.35265.1.22.3.80.1.4.1")
            for gpon in result_gpon:
                gpon_port = int(gpon.oid.split('.')[-1])
                if data.get(gpon_port) is None:
                    data[gpon_port] = 1
                else:
                    data[gpon_port] += 1
        return data, sum(data.values())


def get_info(ip):
    snmp = MySnmp(ip)
    if snmp.get_name() is not None:
        try:
            name = snmp.get_name()
            ports = snmp.get_ports()
            onu_quantity, sum_onu = snmp.get_onu_quantity()
        except Exception as e:
            pass
            # print(f'Error occurred on {ip}: {e}')
        else:
            # print('; '.join(list(map(lambda x: ' --> '.join([str(y) for y in x]), onu_quantity.items()))))
            return {
                'name': name,
                'ip': ip,
                'ports': ports,
                'onu_quantity': '; '.join(list(map(lambda x: ' — '.join([str(y) for y in x]), onu_quantity.items()))),
                'sum_onu': sum_onu
            }


async def write_to_file():
    async with aiofiles.open('result.json', mode='w') as f:
        result = list()
        for ip in IP_ADDRESS:
            data = get_info(ip)
            print(data)
            if data is not None:
                result.append(data)
        await f.write(json.dumps(result, indent=4, ensure_ascii=False))


asyncio.run(write_to_file())
