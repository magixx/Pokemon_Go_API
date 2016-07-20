import struct


class ConverterUtil(object):
    """
    Utility to help with conversions
    """

    @staticmethod
    def i2f(int_n):
        """Integer to Float"""
        return struct.unpack('<Q', struct.pack('<d', int_n))[0]

    @staticmethod
    def f2h(float_n):
        """Float to Hex"""
        return hex(struct.unpack('<Q', struct.pack('<d', float_n))[0])

    @staticmethod
    def f2i(float_n):
        """Float to Integer"""
        return struct.unpack('<Q', struct.pack('<d', float_n))[0]

    @staticmethod
    def l2f(float_n):
        """Long to float"""
        return struct.unpack('d', struct.pack('Q', int(bin(float_n), 0)))[0]

    @staticmethod
    def h2f(hex):
        """Hex to Float"""
        return struct.unpack('<d', struct.pack('<Q', int(hex, 16)))[0]