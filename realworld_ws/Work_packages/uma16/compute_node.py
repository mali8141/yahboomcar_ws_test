#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

import os
import sounddevice as sd
import h5py
import numpy as np
import acoular as ac
import warnings
import uuid

os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
warnings.filterwarnings("ignore")


class BeamformingCompute:
    """Core compute implementation extracted from the ROS wrapper.

    This module is intended to contain the processing logic (recording,
    beamforming, map generation) so ROS nodes remain thin wrappers.
    """

    def __init__(self, mic_geom_file='uma16_geom.xml', fs=48000, channels=16, duration=0.5, freq_band=8000):
        self.FS = fs
        self.CHANNELS = channels
        self.DURATION = duration
        self.MIC_GEOM_FILE = mic_geom_file
        self.FREQ_BAND = freq_band

        self.mg = ac.MicGeom(file=self.MIC_GEOM_FILE)
        self.rg = ac.RectGrid(x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=-0.3, increment=0.01)
        self.st = ac.SteeringVector(grid=self.rg, mics=self.mg)

    def record_and_process(self, device=None):
        current_temp = f'live_temp_{uuid.uuid4().hex}.h5'
        try:
            sd.default.device = device
            recording = sd.rec(int(self.DURATION * self.FS), samplerate=self.FS, channels=self.CHANNELS, dtype='float32')
            sd.wait()
            with h5py.File(current_temp, 'w') as f:
                dset = f.create_dataset('time_data', data=recording)
                dset.attrs['sample_freq'] = float(self.FS)

            ts = ac.TimeSamples(file=current_temp)
            ps = ac.PowerSpectra(source=ts, block_size=128, window='Hanning', cached=False)
            bb = ac.BeamformerBase(freq_data=ps, steer=self.st, cached=False)
            pm = bb.synthetic(self.FREQ_BAND, 3)
            Lm = ac.L_p(pm)
            return Lm.T.flatten().tolist()
        finally:
            if os.path.exists(current_temp):
                try:
                    os.remove(current_temp)
                except OSError:
                    pass
