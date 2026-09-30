#!/usr/bin/env python3
"""Live matplotlib viewer for the /beamforming_heatmap topic published by
uma16_acoustic_overlay (see ../docs/acoustic_overlay.md).

uma16_acoustic_overlay has no GUI of its own -- it only publishes flattened
Float32MultiArray heatmap data. This script reshapes that data back into a
2D grid and displays it live.

--grid-x/--grid-y must match the acoustic overlay node's grid parameters:
    grid_x = (grid_x_max - grid_x_min) / grid_increment + 1
    grid_y = (grid_y_max - grid_y_min) / grid_increment + 1
The overlay node logs its computed "Grid shape: (...)" on startup -- use
that value here if you changed any grid_* parameter away from the defaults.
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class HeatmapViewer(Node):
    def __init__(self, topic: str, shape: tuple[int, int]):
        super().__init__('heatmap_viewer')
        self.shape = shape
        self.create_subscription(Float32MultiArray, topic, self._on_heatmap, 10)

        self.fig, self.ax = plt.subplots()
        self.ax.set_title(f'/{topic.lstrip("/")}')
        cmap = plt.get_cmap('jet').copy()
        cmap.set_bad(color='0.85')  # cells below threshold (NaN) render as neutral gray
        self.im = self.ax.imshow(np.zeros(shape), cmap=cmap, origin='lower')
        self.fig.colorbar(self.im, label='Level (dB)')
        plt.ion()
        plt.show()

    def _on_heatmap(self, msg: Float32MultiArray):
        data = np.array(msg.data, dtype=np.float32)
        expected = self.shape[0] * self.shape[1]
        if data.size != expected:
            self.get_logger().warning(
                f'Got {data.size} values but expected {expected} for shape {self.shape}; '
                'pass --grid-x/--grid-y matching the acoustic overlay node\'s grid parameters.'
            )
            return
        grid = data.reshape(self.shape)
        masked = np.ma.masked_invalid(grid)
        self.im.set_data(masked)
        if masked.count() > 0:
            self.im.set_clim(masked.min(), masked.max())
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', default='/beamforming_heatmap')
    parser.add_argument('--grid-x', type=int, default=41,
                         help='Grid width; must match uma16_acoustic_overlay (default 41 for its default grid_* params)')
    parser.add_argument('--grid-y', type=int, default=41,
                         help='Grid height; must match uma16_acoustic_overlay (default 41 for its default grid_* params)')
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = HeatmapViewer(args.topic, (args.grid_y, args.grid_x))
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            plt.pause(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
