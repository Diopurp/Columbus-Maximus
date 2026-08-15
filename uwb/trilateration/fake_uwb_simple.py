import pty
import os
import random
import time
import math

master_fd, slave_fd = pty.openpty()
slave_name = os.ttyname(slave_fd)

print("="*50)
print(f"Point your node's SERIAL_PORT at: {slave_name}")
print("ctrl+C to stop")
print("="*50)

anchors = {
    "0x0001" : (0.0, 0.0),
    "0x0002" : (0.0, 500.0),
    "0x0003" : (500.0, 500.0),
    "0x0004" : (500.0, 500.0)
}
t = 0.0

try:
    while True:
        # Simulate a tag moving in a small circle in the middle of the square
        fake_x = 250.0 + 80.0 * math.cos(t)
        fake_y = 250.0 + 80.0 * math.sin(t)

        for mac, (ax, ay) in anchors.items():
            true_dist = math.sqrt((fake_x - ax) ** 2 + (fake_y - ay) ** 2)

            # Occasionally simulate a dropped anchor, to test that code path too
            if random.random() < 0.03:
                line = f"RX_TIMEOUT mac_address={mac}\r\n"
            else:
                noisy_dist = true_dist + random.uniform(-2.0, 2.0)  # +/- 2cm noise
                line = f"SUCCESS mac_address={mac} distance[cm]={noisy_dist:.2f}\r\n"

            os.write(master_fd, line.encode())
            print("sent:", line.strip())
            time.sleep(0.02)

        t += 0.05
except KeyboardInterrupt:
    print("\nStopped.")

finally:
    os.close(master_fd)
    os.close(slave_fd)    



