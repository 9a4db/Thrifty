#!/usr/bin/env python

"""
Search for carrier and perform frequency shift if found.
"""

import numpy as np
from collections import deque
import carrier_sync_results
import block_reader
import argparse
import sys
import itertools
# import pyfftw

import matplotlib.pyplot as plt # tmp

def dirichlet_kernel(k, settings):
    """Calculate dirichlet weights.
    
    From: https://en.wikipedia.org/wiki/Discrete_Fourier_transform:
    DFT of a rect function is a sinc-like function (Dirichlet kernel)
    """
    N, W = settings.data_len, settings.code_len
    k = np.array(k, dtype=np.float64)
    f = lambda k: np.sin(np.pi*W*k/N)/W/np.sin(np.pi*k/N)
    # f = lambda k: np.sin(np.pi*W*k/N)/W/(np.pi*k/N) # sinc
    return np.piecewise(k, [k == 0, k != 0], [lambda x: 1, f])


def find_peak(fft, settings):
    """Return index of peak within window [min_idx,max_idx)."""
    normalise = len(fft) / settings.sample_rate
    min_idx = int(settings.carrier_freq_min * normalise)
    max_idx = int(settings.carrier_freq_max * normalise)

    if min_idx > max_idx:
        min_idx, max_idx = max_idx, min_idx

    if min_idx == max_idx:
        return min_idx

    if min_idx < 0 and max_idx >= 0:
        m1 = np.argmax(fft[min_idx:]) + min_idx
        m2 = np.argmax(fft[:max_idx + 1])
        return m1 if fft[m1] > fft[m2] else m2
    else:
        return np.argmax(fft[min_idx:max_idx + 1]) + min_idx


def freq_shift(fft, peak):
    shifted_fft = np.roll(fft, -peak)
    return shifted_fft


def carrier_syncer(settings):
    means = deque([], settings.carrier_noise_window_size)
    # ba = pyfftw.empty_aligned(settings.data_len, dtype='complex64')

    n = settings.carrier_peak_average
    rel = np.arange(-n, n + 1)
    weights = dirichlet_kernel(rel, settings)

    # @profile
    def carrier_sync(b):
        r = carrier_sync_results.CarrierSyncResults()
        # ba[:] = b
        # r.fft = pyfftw.interfaces.numpy_fft.fft(ba)
        r.fft = np.fft.fft(b)
        fft_mag = np.abs(r.fft)
    
        means.append(np.mean(fft_mag))
        r.noise = np.mean(means)
    
        t = settings.carrier_threshold
        tc, tn, ts = t['constant'], t['snr'], t['stddev']
        stddev = np.std(fft_mag) if ts else 0
        r.threshold = tc + tn * r.noise + ts * stddev
    
        r.peak = find_peak(fft_mag, settings)
    
        # Calculate weighted average of peak
        r.peak_avg_energy = np.sum(fft_mag[r.peak + rel]) / np.sum(weights)

        if r.peak_avg_energy > r.threshold:
            r.detected = True
            r.shifted_fft = freq_shift(r.fft, r.peak)
            assert(np.abs(r.shifted_fft[0]) >= np.abs(r.fft[r.peak]))
    
        return r

    return carrier_sync


if __name__ == '__main__':
    import settings

    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('input', type=argparse.FileType('rb'),
                        default='-',
                        help='input data (\'-\' streams from stdin)')
    parser.add_argument('-p', dest='plot', action='store_true',
                        default=False,
                        help='plot results')
    parser.add_argument('-a', dest='all', action='store_true',
                        default=False,
                        help='output summary for detections and non-detections')
    parser.add_argument('-s', dest='sample_rate', type=float,
                        default=settings.sample_rate,
                        help='overwrite sample rate')
    parser.add_argument('-c', dest='chip_rate', type=float,
                        default=settings.chip_rate,
                        help='overwrite chip rate')
    parser.add_argument('--carrier_freq_min', dest='carrier_freq_min',
                        type=float, default=settings.carrier_freq_min,
                        help='overwrite minimum carrier frequency')
    parser.add_argument('--carrier_freq_max', dest='carrier_freq_max',
                        type=float, default=settings.carrier_freq_max,
                        help='overwrite maximum carrier frequency')
    parser.add_argument('-o', '--output', dest='output',
                        type=argparse.FileType('w'), default=None,
                        help='output serialized block on detection')

    args = parser.parse_args()
    settings.sample_rate = args.sample_rate
    settings.chip_rate = args.chip_rate
    settings.carrier_freq_min = args.carrier_freq_min
    settings.carrier_freq_max = args.carrier_freq_max
    # overwrite freq_min, max, threshold

    blocks = block_reader.data_reader(args.input, settings)
    syncer = carrier_syncer(settings)

    for i, b in enumerate(blocks):
        r = syncer(b)
        r.idx = i
        if not r.detected and not args.all:
            continue
        if args.plot:
            r.plot(settings)
            plt.show()

        sys.stderr.write(r.summary(settings) + '\n')

        if args.output != None:
            s = block_reader.serialize_block(b)
            print >>args.output, i, s

