import logging
from homekit.model.services.service_types import ServicesTypes
from homekit.model.characteristics.characteristic_types import CharacteristicsTypes
import gatt.gatt

# the uuid of the ble descriptors that hold the characteristic instance id as value (see page 128)
CharacteristicInstanceID = 'dc46f0fe-81d2-4616-b5d9-6abdd796939a'


def setup_logging(level):
    """
    Set up the logging to use a decent format and the log level given as parameter.
    :param level: the log level used for the root logger
    """
    logging.basicConfig(format='%(asctime)s %(filename)s:%(lineno)04d %(levelname)s %(message)s')
    if level:
        getattr(logging, level.upper())
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % level)
        logging.getLogger().setLevel(numeric_level)


def find_characteristic(device, service_uuid, char_uuid):
    """

    :param device:
    :param service_uuid:
    :param char_uuid:
    :return:
    """
    service_found = None
    logging.debug('services: %s', device.services)
    for possible_service in device.services:
        if ServicesTypes.get_short(service_uuid.upper()) == ServicesTypes.get_short(possible_service.uuid.upper()):
            service_found = possible_service
            break
    logging.debug('searched service: %s', service_found)

    if not service_found:
        logging.error('searched service not found.')
        return None, None

    result_char = None
    result_char_id = None
    for characteristic in service_found.characteristics:
        logging.debug('char: %s %s', characteristic.uuid, CharacteristicsTypes.get_short(characteristic.uuid.upper()))
        if CharacteristicsTypes.get_short(char_uuid.upper()) == CharacteristicsTypes.get_short(
                characteristic.uuid.upper()):
            result_char = characteristic
            for descriptor in characteristic.descriptors:
                value = descriptor.read_value()
                if descriptor.uuid == CharacteristicInstanceID:
                    cid = int.from_bytes(value, byteorder='little')
                    result_char_id = cid

    if not result_char:
        logging.error('searched char not found.')
        return None, None

    logging.debug('searched char: %s %s', result_char, result_char_id)
    return result_char, result_char_id


class ResolvingManager(gatt.gatt.DeviceManager):
    """
    DeviceManager implementation that stops running after a given device was discovered.
    """
    def __init__(self, adapter_name, mac):
        self.mac = mac
        gatt.gatt.DeviceManager.__init__(self, adapter_name=adapter_name)

    def device_discovered(self, device):
        logging.debug('discovered %s', device.mac_address.upper())
        if device.mac_address.upper() == self.mac.upper():
            self.stop()


class LoggingDevice(gatt.gatt.Device):
    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logging.debug('device disconnected')
