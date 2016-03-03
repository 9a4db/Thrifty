#!/usr/bin/env python

import numpy as np
import base64

def raw_chunk_reader(stream, chunk_size):
    while True:
        buf = stream.read(chunk_size)
        if len(buf) == 0:
            break
        yield buf


def raw_block_reader(stream, block_size):
    """Read fixed-sized blocks of samples."""
    chunk = ""
    for raw in raw_chunk_reader(stream, block_size - len(chunk)):
        if len(raw) == 0:
            chunk = raw
        else:
            chunk += raw

        if len(chunk) < block_size:
            continue

        data = np.frombuffer(chunk, dtype=np.uint8)

        yield data
        chunk = ""


def raw_to_complex(data):
    """Convert from raw samples to complex array."""
    iq = data.astype(np.float32).view(np.complex64)
    iq -= 127.4 + 127.4j
    iq /= 128
    return iq


def complex_to_raw(iq):
    """Convert from complex array back to raw samples"""
    scaled = iq.astype(np.complex64).view(np.float32) * 128 + 127.4
    return scaled.astype(np.uint8)
    # TOOD: d = complex_to_raw(c); assert(np.all([b, d]))


def data_reader(stream, settings):
    block_len, history_len = settings.block_len, settings.history_len
    assert(settings.data_len == block_len + history_len)

    data = np.zeros(settings.data_len)
    for b in raw_block_reader(stream, block_len * 2):
        c = raw_to_complex(b)
        assert(len(c) == block_len)
        data = np.concatenate([data[-history_len:], c])
        assert(len(data) == settings.data_len)
        yield data


def full_data_reader(stream, settings):
    """Read full blocks with history already included."""
    for b in raw_block_reader(stream, settings.data_len * 2):
        c = raw_to_complex(b)
        yield c


def serialize_block(block):
    return base64.b64encode(complex_to_raw(block))


def serialized_block_reader(stream, settings):
    while True:
        line = stream.readline()
        if line == '':
            break
        idx, s = line.rstrip('\n').split(' ')
        raw = np.fromstring(base64.b64decode(s), dtype='uint8')
        d = raw_to_complex(raw)
        assert(len(d) == settings.data_len)
        yield int(idx), d

