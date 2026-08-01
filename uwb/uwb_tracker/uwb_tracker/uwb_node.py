import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
import numpy as np
import re
import serial


class UWBTrilaterationNode(Node):
    def __init__(self):
        super().__init__('uwb_trilateration_node')
        self.publisher_ = self.create_publisher(Point, 'uwb_pose', 10)

        # --- HARDWARE CONFIGURATION ---
        self.SERIAL_PORT = "/dev/ttyACM0"
        self.BAUD_RATE = 115200
        try:
            self.ser = serial.Serial(self.SERIAL_PORT, self.BAUD_RATE, timeout=1)
            self.ser.flush()
            self.get_logger().info(f"Connected to Serial Port: {self.SERIAL_PORT}")
        except Exception as e:
            self.get_logger().error(f"Could not open port {self.SERIAL_PORT}: {e}")
            raise

        self.anchors = np.array([
            [0.0, 0.0], [200.0, 0.0], [0.0, 200.0], [200.0, 200.0],
        ])
        self.num_anchors = len(self.anchors)
        self.mac_to_index = {"0x0001": 0, "0x0002": 1, "0x0003": 2, "0x0004": 3}
        self.anchor_health = {mac: False for mac in self.mac_to_index}
        self.distance_buffers = {mac: [] for mac in self.mac_to_index}
        self.current_distances = [None, None, None, None]
        self.reading_count = 0

        self.anchor_sq = self.anchors[:, 0] ** 2 + self.anchors[:, 1] ** 2
        A_list, self.pair_indices = [], []
        for i in range(self.num_anchors):
            for j in range(i + 1, self.num_anchors):
                A_list.append([2 * (self.anchors[i, 0] - self.anchors[j, 0]),
                                2 * (self.anchors[i, 1] - self.anchors[j, 1])])
                self.pair_indices.append((i, j))
        self.A = np.array(A_list)
        self.b = np.zeros(6)

        # fires as fast as possible — same effect as your original `while True`
        self.timer = self.create_timer(0.001, self.read_and_process)

    def read_and_process(self):
        raw_line = self.ser.readline()
        if not raw_line:
            return
        try:
            line = raw_line.decode("utf-8").strip()
            if not line:
                return

            if "RX_TIMEOUT" in line:
                m = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                if m and m.group(1) in self.mac_to_index:
                    mac = m.group(1)
                    if self.anchor_health[mac]:
                        self.get_logger().warn(f"OFFLINE: {mac} (RX_TIMEOUT)")
                    self.anchor_health[mac] = False
                    self.distance_buffers[mac].clear()
                return

            if "SUCCESS" in line and "distance[cm]=" in line:
                mac_m = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                dist_m = re.search(r"distance\[cm\]=([0-9.]+)", line)
                if mac_m and dist_m and mac_m.group(1) in self.mac_to_index:
                    mac = mac_m.group(1)
                    self.distance_buffers[mac].append(float(dist_m.group(1)))
                    self.reading_count += 1
                    self.anchor_health[mac] = True

            if self.reading_count >= 10:
                for mac, idx in self.mac_to_index.items():
                    buf = self.distance_buffers[mac]
                    self.current_distances[idx] = np.mean(buf) if buf else None

                valid_count = sum(d is not None for d in self.current_distances)

                if valid_count >= 3:
                    r_safe = [d if d is not None else 0.0 for d in self.current_distances]
                    r_sq = np.array(r_safe) ** 2
                    for row, (i, j) in enumerate(self.pair_indices):
                        self.b[row] = (r_sq[j] - r_sq[i]) - self.anchor_sq[j] + self.anchor_sq[i]
                    solution, *_ = np.linalg.lstsq(self.A, self.b, rcond=None)

                    msg = Point()
                    msg.x = float(solution[0]) / 100.0   # cm -> m, ROS convention
                    msg.y = float(solution[1]) / 100.0
                    msg.z = 0.0
                    self.publisher_.publish(msg)
                    self.get_logger().info(
                        f"POSITION ({valid_count}/4) -> X: {solution[0]:.2f}cm Y: {solution[1]:.2f}cm"
                    )
                else:
                    self.get_logger().warn(f"BATCH FAILED: only {valid_count} anchors active")

                for mac in self.mac_to_index:
                    self.distance_buffers[mac].clear()
                self.current_distances = [None, None, None, None]
                self.reading_count = 0

        except (ValueError, UnicodeDecodeError, IndexError):
            return


def main(args=None):
    rclpy.init(args=args)
    node = UWBTrilaterationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down tracker safely.")
    finally:
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
