#!/usr/bin/env python

"""
Perform code detection on data captured with rtl_sdr.

Examples:
  To capture:
      rtl_sdr -f 435e6 -s 2.1e6 -g 10 dump.bin

  To process the data:
      detector.py -s 2.1e6 dump.bin

  To stream:
      rtl_sdr -f 435e6 -s 2.1e6 -g 10 - | detector.py -s 2.1e6 -
"""

# profiling: kernprof -l -v detector.py dump24.bin

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

code = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0])

def raw_chunk_reader(stream, chunk_size):
    while True:
        buf = stream.read(chunk_size)
        if len(buf) == 0:
            break
        yield buf


def data_block_reader(stream, block_size):
    """Read and convert fixed-sized blocks of samples."""
    chunk_size = block_size * 2 # I and Q
    chunk = ""
    for raw in raw_chunk_reader(stream, chunk_size - len(chunk)):
        if len(raw) == 0:
            chunk = raw
        else:
            chunk += raw

        if len(chunk) < chunk_size:
            continue

        data = np.frombuffer(chunk, dtype=np.uint8)

        iq = np.empty(len(data)//2, 'complex')
        iq.real, iq.imag = data[::2], data[1::2]
        iq /= (255/2)
        iq -= (1 + 1j)

        assert(len(iq) == block_size)
        yield iq
        chunk = ""


#@profile
def crunch(stream, sample_rate, chip_rate, plot=False):
    def plot_signal(s, t0=0, imag=False, title="", **kwargs):
        t = t0 + np.arange(len(s)) / sample_rate
        plt.plot(t, s.real, t, s.imag, **kwargs)
        plt.grid()
        if title:
            plt.title(title)

    plot2 = False

    sps = sample_rate / chip_rate
    N_code = int(sps * len(code))
    # block_size = N_code # TODO: this should be a power of two / block_size = N
    block_size = 1<<(int(np.ceil(np.log2(N_code))))
    N = block_size
    N2 = 2 * N # = len(D)

    dt = N / sample_rate
    print "Blocks: size=%d; dt=%.2f ms" % (block_size, dt*1000)

    # # Graphing

    # Prepare code: resample, get FFT
    # TODO: anti-aliasing filter
    code_indices = np.arange(N_code) * len(code) / N_code
    c = code[code_indices]
    c = np.concatenate([c*2-1, np.zeros(N2 - N_code)])
    C = np.fft.fft(c)

    # plot_signal(c)
    print "Code: {} symbols @ {:.6f} MHz = {:.3f} ms ; {} samples @ {:.6f} Msps".format(
            len(code), chip_rate/1e6, len(code)/chip_rate*1e3, N_code, sample_rate/1e6)

    prev_means = deque([10], 10)
    prev_dc_bias = deque([5], 10)
    prev_m_avg = deque([10], 10)
    prev_corr_t = 0

    freq_shift = np.exp(-2j * np.pi * np.arange(N) * np.fft.fftfreq(N))

    A = np.zeros(N)
    a = np.zeros(N)
    bi = 0
    corr_dt = 0

    for bi, b in enumerate(data_block_reader(stream, N)):
        B = np.fft.fft(b)

        # TODO: shift in freq domain
        d = np.concatenate([a, b])
        D = np.fft.fft(d)
        D_mag = np.abs(D)

        # w = window for carrier detection
        w_hz = 20e3
        w_n = int(w_hz / sample_rate * N2)
        W_mag = np.concatenate([D_mag[1:w_n], D_mag[-w_n:]])

        W_peak_idx = np.argmax(W_mag)
        W_peak = W_mag[W_peak_idx]

        D_avg = np.average(D_mag) 

        noise = np.mean(prev_means)
        dc_bias = np.mean(prev_dc_bias)
        threshold = dc_bias + 2 * noise

        if W_peak > threshold:
            peak_idx = W_peak_idx + 1 if W_peak_idx < w_n else len(W_mag) - W_peak_idx
            W_peak_f = sample_rate / N2 * peak_idx
            SNR = 20 * np.log10(W_peak / noise)
            print "Carrier in block #%d (%.3f s) at %.2f kHz (%d) -- energy=%.2f (thres: %.0f, avg: %.0f, S/N: %.2f dB)" % (bi, bi*dt, W_peak_f/1000.0, W_peak_idx, W_peak, threshold, D_avg, SNR)
            sys.stdout.flush()

            f = np.fft.fftfreq(N2, 1.0/sample_rate)

            if plot:
                # plt.figure()
                # plt.subplot(2,2,1)
                # plot_signal(d, title="d")
                plt.subplot(2,2,2)
                plt.plot(np.fft.fftshift(f), np.fft.fftshift(D_mag))

            # freq offset correction in freq domain
            E = np.roll(D, peak_idx)

            if plot:
                plt.subplot(2,2,3)
                plt.plot(np.fft.fftshift(f), np.fft.fftshift(np.abs(E)))

                e = np.fft.ifft(E)
                plt.subplot(2,2,1)
                # plot_signal(np.abs(e), alpha=0.5)
                plot_signal(e)

            if plot2:
                plt.figure()
                e = np.fft.ifft(E)
                plot_signal(-np.abs(e))

            # E = np.fft.fft(e) # test

            M = E * C.conjugate()
            m_full = np.fft.ifft(M)
            m = m_full[:N]
            m_mag = np.abs(m)

            m_std = np.std(m_mag)
            m_avg = np.mean(m_mag)
            prev_m_avg.append(m_avg)
            mean = np.mean(prev_m_avg)
            threshold = 10 + 4 * mean + 1 * m_std
            # print "Corr peak", m_std, m_avg, mean, threshold

            corr_max = np.max(m_mag)
            if corr_max > threshold:
                rel_idx = np.argmax(m_mag)
                abs_idx = N * bi + rel_idx
                t = abs_idx / sample_rate
                corr_dt = t - prev_corr_t
                
                SNR = 20 * np.log10(corr_max / mean)
                print "Corr peak @ {:.6f} s ({}:{}={}) dt={:.6f} thresh={:.0f} corr_max={:.0f} SNR={:.2f}".format(
                        t, bi, rel_idx, abs_idx, corr_dt, threshold, corr_max, SNR)

                if plot:
                    plt.subplot(2,2,1)
                    plot_signal(c * np.max(np.abs(e)), t0=(rel_idx)/sample_rate, alpha=0.5)

                if plot2:
                    plot_signal(c, t0=(rel_idx)/sample_rate, alpha=0.5)

                prev_corr_t = t

            if plot:
                plt.subplot(2,2,4)
                plt.plot(m_mag)
                plt.plot([0, len(m_mag) - 1], [threshold, threshold])
                # TODO: plot detection vertical line at detection peak

                if plot == True:
                    plt.show()
                else:
                    plt.savefig(plot, dpi=150)

                # plt.close()

            if plot2:
                plt.show()


        prev_means.append(D_avg)
        prev_dc_bias.append(D_mag[0])
        a = b
        A = B

        # Kontrolleer met time-domain korrelasie

    # step output / graphs

    print bi * N / sample_rate


if __name__ == "__main__":
    # Parse command-line parameters
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('filename', type=argparse.FileType('rb'), help='input data (a \'-\') streams from stdin')
    parser.add_argument('-s', dest='sample_rate', type=float, default=2.1e6, help='(default: 2.1e6)')
    parser.add_argument('-c', dest='chip_rate', type=float, default=1e6, help='(default: 1e6)')
    parser.add_argument('-p', dest='plot', action='store_true', default=False, help='plot when detected')

    args = parser.parse_args()

    crunch(args.filename, args.sample_rate, args.chip_rate, args.plot)

