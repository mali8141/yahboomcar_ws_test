import rclpy
from rclpy.node import Node
import queue
import threading
import datetime
import sounddevice as sd
import soundfile as sf


class Uma16RecorderNode(Node):
    def __init__(self):
        super().__init__('uma16_recorder')
        
        # 1. Declare ROS 2 Parameters (replaces argparse)
        self.declare_parameter('device', '')
        self.declare_parameter('samplerate', 48000)
        self.declare_parameter('channels', 16)
        self.declare_parameter('filename', '')

        # Fetch parameter values
        device_param = self.get_parameter('device').value
        self.device = int(device_param) if device_param.isdigit() else (device_param if device_param else None)
        self.samplerate = self.get_parameter('samplerate').value
        self.channels = self.get_parameter('channels').value
        self.filename = self.get_parameter('filename').value

        # Generate default filename if none provided
        if not self.filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"uma16_recording_{timestamp}.wav"

        # 2. Setup Queue and State
        self.q = queue.Queue()
        self.is_recording = True

        try:
            # 3. Open SoundFile and InputStream
            self.file = sf.SoundFile(self.filename, mode='w', samplerate=self.samplerate,
                                     channels=self.channels, subtype='PCM_16')
            
            self.stream = sd.InputStream(samplerate=self.samplerate, device=self.device,
                                         channels=self.channels, callback=self.audio_callback)
            self.stream.start()
            
            self.get_logger().info(f"Recording to {self.filename}...")
            self.get_logger().info(f"Channels: {self.channels} | Sample Rate: {self.samplerate} Hz")

            # 4. Start a background thread for writing to disk (prevents blocking rclpy.spin)
            self.writer_thread = threading.Thread(target=self.file_writer)
            self.writer_thread.start()

        except Exception as e:
            self.get_logger().error(f"Failed to initialize audio: {e}")
            raise

    def audio_callback(self, indata, frames, time, status):
        """Called for each audio block by sounddevice."""
        if status:
            self.get_logger().warning(f"Audio stream status: {status}")
        self.q.put(indata.copy())

    def file_writer(self):
        """Pulls from the queue and writes to disk in a separate thread."""
        # Keep writing as long as we are recording OR the queue still has data
        while self.is_recording or not self.q.empty():
            try:
                # Use a timeout so the thread can periodically check `self.is_recording`
                data = self.q.get(timeout=0.1)
                self.file.write(data)
            except queue.Empty:
                pass

    def destroy_node(self):
        """Clean up resources when the node shuts down."""
        self.get_logger().info("Stopping recording and cleaning up...")
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if hasattr(self, 'writer_thread'):
            self.writer_thread.join()
            
        if hasattr(self, 'file'):
            self.file.close()
            
        self.get_logger().info(f"Recording safely saved to: {self.filename}")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = Uma16RecorderNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass # Handle Ctrl+C gracefully
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
