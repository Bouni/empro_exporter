import logging
import signal
import struct
import uuid
from time import sleep

import click
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from prometheus_client import Gauge, Info, start_http_server
from registers import registers
from slugify import Slugify

logger = logging.getLogger(__name__)


class EMproModbusExporter:
    def __init__(self, host):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        self.slugify = None
        self.stop = False
        self.host = host
        self.client = None
        self.metrics = {}
        self.init_prometheus()
        self.run()

    def init_prometheus(self):
        self.slugify = Slugify(to_lower=True)
        self.slugify.separator = "_"
        self.slugify.pretranslate = {"+": "plus", "-": "minus"}
        for n, r in enumerate(registers):
            s = self.slugify(f"empro_{r['short_name']}")
            registers[n]["slug"] = s
            if s in self.metrics:
                print(s, r)
            if r["datatype"] in [
                "uint8",
                "uint16",
                "sint16",
                "uint32",
                "sint32",
                "fl32",
            ]:
                self.metrics[s] = Gauge(s, r["description"], ["unit", "register"])
            else:
                self.metrics[s] = Info(s, r["description"], ["register"])

    def run(self):
        self.client = ModbusTcpClient(self.host)
        while not self.stop:
            for register in registers:
                self.read_register(register)
            sleep(1)

    def _decode_result(self, register, r):
        _register = r["register"]
        datatype = r["datatype"]
        count = r["count"]
        slug = r["slug"]
        unit = r["unit"]
        name = r["short_name"]
        if datatype == "bool":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = bool(result.decode_8bit_uint())
            self.metrics[slug].labels(register=_register).info({"name": name, "value": str(v)})
        elif datatype == "uint8":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_8bit_uint()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "uint16":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_16bit_uint()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "sint16":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_16bit_int()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "uint32":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_32bit_uint()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "sint32":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_32bit_int()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "fl32":
            result = BinaryPayloadDecoder.fromRegisters(
                register.registers, Endian.Big, Endian.Little
            )
            v = result.decode_32bit_float()
            self.metrics[slug].labels(unit=unit, register=_register).set(v)
        elif datatype == "ascii":
            result = BinaryPayloadDecoder.fromRegisters(
                [
                    struct.unpack("<H", struct.pack(">H", r))[0]
                    for r in register.registers
                ]
            )
            v = result.decode_string(count).decode("UTF-8")
            self.metrics[slug].labels(register=_register).info({"name": name, "value": str(v)})
        elif datatype == "uint8[]":
            logger.info("Skip unit8[], not implemented")
        elif datatype == "bitmask":
            logger.info("Skip bitmask, not implemented")

    def read_register(self, register):
        try:
            if register["rw"] == "w":
                logger.info(f"Skip write-only register {register['register']}")
                return
            result = self.client.read_holding_registers(
                register["register"], register["count"]
            )
            self._decode_result(result, register)
        except Exception as e:
            logger.error("Error %s reading register %s" % e, register)

    def exit(self, signum, frame):
        self.stop = True


@click.command()
@click.argument("host", required=True)
@click.option("-m", "--metrics_port", default=9052)
def main(host, metrics_port):
    start_http_server(metrics_port)
    EMproModbusExporter(host)


if __name__ == "__main__":
    main()
