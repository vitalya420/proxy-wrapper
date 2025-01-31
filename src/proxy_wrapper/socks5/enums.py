from enum import Enum


class SocksVersion(int, Enum):
    SOCKS5 = 0x05


class Method(int, Enum):
    NO_AUTHENTICATION_REQUIRED = 0x00
    GSSAPI = 0x01
    USERNAME_PASSWORD = 0x02
    NO_ACCEPTABLE_METHODS = 0xFF


class Command(int, Enum):
    CONNECT = 0x01
    BIND = 0x02
    UDP_ASSOCIATE = 0x03


class ATYP(int, Enum):
    IPV4 = 0x01
    DOMAIN_NAME = 0x03
    IPV6 = 0x04


class ReplyStatus(int, Enum):
    SUCCESS = 0x00
    GENERAL_FAILURE = 0x01
    CONNECTION_NOT_ALLOWED = 0x02
    NETWORK_UNREACHABLE = 0x03
    HOST_UNREACHABLE = 0x04
    CONNECTION_REFUSED = 0x05
    TTL_EXPIRED = 0x06
    COMMAND_NOT_SUPPORTED = 0x07
    ADDRESS_TYPE_NOT_SUPPORTED = 0x08
