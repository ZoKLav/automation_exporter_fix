"""Experimental intrinsic-opacity preference patch for one exact Automation DLL.

Usage: python patch_plugin.py ORIGINAL.dll OUTPUT.dll
Creates an unsigned DLL; refuses other builds and existing output paths.
"""
import hashlib
from pathlib import Path
import struct
import sys

ORIGINAL_SHA256 = '5f52eb582110ab68db835783cabac30cd0728c5b561bbc3beb2dcafbcbe38721'
PATCHES = (
    # If an intrinsic opacity texture exists, select it instead of the stamp.
    (0x52C6E, bytes.fromhex('0f 84 37 06 00 00'), bytes.fromhex('90 e9 37 06 00 00')),
    # Load the intrinsic opacity texture even when a valid stamp exists.
    (0x559A8, bytes.fromhex('75 32'), bytes.fromhex('90 90')),
)

def checksum(data, checksum_offset):
    total = 0
    for i in range(0, len(data), 2):
        word = 0 if checksum_offset <= i < checksum_offset + 4 else int.from_bytes(data[i:i+2], 'little')
        total += word
        total = (total & 0xffff) + (total >> 16)
    total = (total & 0xffff) + (total >> 16)
    return total + len(data)

def patch(data):
    if hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Unsupported DLL. This patch requires the exact supplied x64 build.')
    b = bytearray(data)
    for offset, before, after in PATCHES:
        if b[offset:offset+len(before)] != before:
            raise ValueError('Instruction bytes do not match.')
        b[offset:offset+len(before)] = after
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    if struct.unpack_from('<H', b, pe+4)[0] != 0x8664:
        raise ValueError('Expected AMD64 image.')
    certificate_directory = pe+24+112+4*8
    cert_offset, cert_size = struct.unpack_from('<II', b, certificate_directory)
    if cert_offset + cert_size != len(b):
        raise ValueError('Unexpected certificate placement.')
    # A modified binary cannot retain its publisher signature. Remove the
    # trailing certificate and directory instead of presenting an invalid signature.
    del b[cert_offset:]
    struct.pack_into('<II', b, certificate_directory, 0, 0)
    checksum_offset = pe+24+64
    struct.pack_into('<I', b, checksum_offset, 0)
    struct.pack_into('<I', b, checksum_offset, checksum(b, checksum_offset))
    return bytes(b)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    result = patch(Path(sys.argv[1]).read_bytes())
    with Path(sys.argv[2]).open('xb') as f:
        f.write(result)
    print('Created experimental unsigned DLL:', sys.argv[2])
    print('SHA256:', hashlib.sha256(result).hexdigest())
