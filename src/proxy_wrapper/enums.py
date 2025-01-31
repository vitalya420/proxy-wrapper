from enum import Enum


class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxySocketState(str, Enum):
    INITIALIZED = "initialized"
    IN_COMMAND_MODE = "in_command_mode"
    CONNECTING_TO_PROXY = 'connecting_to_proxy'
