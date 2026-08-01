import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseStamped
from visualization_msgs.msg import Marker, MarkerArray
from nav_msgs.msg import Path
import numpy as np
import re
import serial


class UWBTrilaterationNode(Node):
    def __init__(self):
        super().__init__('uwb_trilateration_node')

        # --- publishers ---
        self.publisher_ = self.create_publisher(Point, 'uwb_pose', 10)
        self.anchor_marker_pub = self.create_publisher(MarkerArray, 'anchor_markers', 10)
        self.tag_marker_pub = self.create_publisher(Marker, 'tag_marker', 10)
        self.lines_pub = self.create_publisher(Marker, 'tag_to_anchor_lines', 10)
        self.path_pub = self.create_publisher(Path, 'tag_path', 10)

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

        # trail: keep last N tag poses
        self.path_msg = Path()
        self.path_msg.header.frame_id = "world"
        self.max_path_length = 300

        # anchors are static -> publish once, not on the timer
        self.publish_anchor_markers()

        self.timer = self.create_timer(0.001, self.read_and_process)

    def publish_anchor_markers(self):
        marker_array = MarkerArray()

        for idx, (x, y) in enumerate(self.anchors):
            sphere = Marker()
            sphere.header.frame_id = "world"
            sphere.header.stamp = self.get_clock().now().to_msg()
            sphere.ns = "anchors"
            sphere.id = idx
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x = x / 100.0
            sphere.pose.position.y = y / 100.0
            sphere.pose.position.z = 0.0
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = sphere.scale.y = sphere.scale.z = 0.15
            sphere.color.r, sphere.color.g, sphere.color.b, sphere.color.a = 1.0, 0.0, 0.0, 1.0
            marker_array.markers.append(sphere)

        line = Marker()
        line.header.frame_id = "world"
        line.header.stamp = self.get_clock().now().to_msg()
        line.ns = "anchor_outline"
        line.id = 100
        line.type = Marker.LINE_STRIP
        line.action = Marker.ADD
        line.scale.x = 0.02
        line.color.r, line.color.g, line.color.b, line.color.a = 0.0, 1.0, 0.0, 1.0

        for (x, y) in list(self.anchors) + [self.anchors[0]]:
            p = Point()
            p.x, p.y, p.z = x / 100.0, y / 100.0, 0.0
            line.points.append(p)

        marker_array.markers.append(line)
        self.anchor_marker_pub.publish(marker_array)

    def publish_tag_visuals(self, tag_x, tag_y):
        tag_marker = Marker()
        tag_marker.header.frame_id = "world"
        tag_marker.header.stamp = self.get_clock().now().to_msg()
        tag_marker.ns = "tag"
        tag_marker.id = 0
        tag_marker.type = Marker.SPHERE
        tag_marker.action = Marker.ADD
        tag_marker.pose.position.x = tag_x
        tag_marker.pose.position.y = tag_y
        tag_marker.pose.position.z = 0.0
        tag_marker.pose.orientation.w = 1.0
        tag_marker.scale.x = tag_marker.scale.y = tag_marker.scale.z = 0.15
        tag_marker.color.r, tag_marker.color.g, tag_marker.color.b, tag_marker.color.a = 0.0, 0.0, 1.0, 1.0
        self.tag_marker_pub.publish(tag_marker)

        lines_to_anchors = Marker()
        lines_to_anchors.header.frame_id = "world"
        lines_to_anchors.header.stamp = self.get_clock().now().to_msg()
        lines_to_anchors.ns = "tag_to_anchor_lines"
        lines_to_anchors.id = 200
        lines_to_anchors.type = Marker.LINE_LIST
        lines_to_anchors.action = Marker.ADD
        lines_to_anchors.scale.x = 0.01
        lines_to_anchors.color.r, lines_to_anchors.color.g, lines_to_anchors.color.b, lines_to_anchors.color.a = 1.0, 1.0, 0.0, 0.6

        for (ax, ay) in self.anchors:
            lines_to_anchors.points.append(Point(x=tag_x, y=tag_y, z=0.0))
            lines_to_anchors.points.append(Point(x=ax / 100.0, y=ay / 100.0, z=0.0))

        self.lines_pub.publish(lines_to_anchors)

        pose = PoseStamped()
        pose.header.frame_id = "world"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = tag_x
        pose.pose.position.y = tag_y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0

        self.path_msg.poses.append(pose)
        if len(self.path_msg.poses) > self.max_path_length:
            self.path_msg.poses.pop(0)
        self.path_msg.header.stamp = self.get_clock().now().to_msg()
        self.path_pub.publish(self.path_msg)

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

                    tag_x = float(solution[0]) / 100.0
                    tag_y = float(solution[1]) / 100.0

                    msg = Point()
                    msg.x, msg.y, msg.z = tag_x, tag_y, 0.0
                    self.publisher_.publish(msg)
                    self.get_logger().info(
                        f"POSITION ({valid_count}/4) -> X: {solution[0]:.2f}cm Y: {solution[1]:.2f}cm"
                    )

                    self.publish_tag_visuals(tag_x, tag_y)
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