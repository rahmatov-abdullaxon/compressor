def encode(value):
    if value < 0: raise ValueError("Only unsigned integers are supported")
    buffer = bytearray()
    remaining = value
    while True:
        byte = remaining & 0x7F
        remaining >>= 7
        if remaining: buffer.append(byte | 0x80)
        else: buffer.append(byte); return bytes(buffer)

def decode(data, offset=0):
    shift = 0
    value = 0
    position = offset
    while position < len(data):
        byte = data[position]
        position = position + 1
        value = value | ((byte & 0x7F) << shift)
        if byte & 0x80 == 0: return value, position
        shift = shift + 7
        if shift > 64: raise ValueError("Integer is too large.")
    raise ValueError("Unexpected end of data while decoding integer.")
