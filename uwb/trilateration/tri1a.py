import numpy as np
import re
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0"  # Verified by your debug.py
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(" Listening for live UWB data stream...")
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}.")
    print(f"Details: {e}")
    exit()

# Define your 4 Anchors in Centimeters (30x30 meters = 3000x3000 cm)
anchors = np.array(
    [
        [0.0, 0.0],  # Anchor 0 (MAC: 0x0001)
        [200.0, 0.0],  # Anchor 1 (MAC: 0x0002)
        [0.0, 200.0],  # Anchor 2 (MAC: 0x0003)
        [200.0, 200.0],  # Anchor 3 (MAC: 0x0004)
    ]
)
num_anchors = len(anchors)

# Map MAC address strings to internal indexes
mac_to_index = {"0x0001": 0, "0x0002": 1, "0x0003": 2, "0x0004": 3}

# Live health tracker (True = Online, False = Offline)
anchor_health = {mac: False for mac in mac_to_index.keys()}

# Memory buffer: Stores the last known valid distance for each anchor
current_distances = [None, None, None, None]

# --- 2. OPTIMIZATION: PRE-CALCULATE STATIC PROPERTIES ---
anchor_sq = anchors[:, 0] ** 2 + anchors[:, 1] ** 2

A_list = []
pair_indices = []
for i in range(num_anchors):
    for j in range(i + 1, num_anchors):
        A_list.append(
            [
                2 * (anchors[i, 0] - anchors[j, 0]),
                2 * (anchors[i, 1] - anchors[j, 1]),
            ]
        )
        pair_indices.append((i, j))

A = np.array(A_list)
b = np.zeros(6)

print("-" * 80)

# --- 3. MAIN PARSING LOOP ---
try:
    while True:
        # Read exactly like your working debug.py script
        raw_line = ser.readline()
        if not raw_line:
            continue

        try:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue

            # --- CONDITION A: OFFLINE ALERTS (RX_TIMEOUT) ---
            if "RX_TIMEOUT" in line:
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                if mac_match:
                    mac = mac_match.group(1)
                    if mac in mac_to_index:
                        if anchor_health[mac] is True:
                            print(
                                f"OFFLINE ALERT: UWB Anchor {mac} went down! (RX_TIMEOUT)"
                            )
                        anchor_health[mac] = False
                        current_distances[mac_to_index[mac]] = None
                continue

            # --- CONDITION B: SUCCESSFUL READINGS ---
            # Handles double quotes around "SUCCESS" safely
            if "SUCCESS" in line and "distance[cm]=" in line:
                # Use robust regex pattern searching to extract the tags cleanly
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                dist_match = re.search(r"distance\[cm\]=([0-9.]+)", line)

                if mac_match and dist_match:
                    target_mac = mac_match.group(1)
                    target_dist = float(dist_match.group(1))

                    if target_mac in mac_to_index:
                        idx = mac_to_index[target_mac]
                        current_distances[idx] = target_dist

                        # Print status notice when a chip transitions online
                        if anchor_health[target_mac] is False:
                            print(
                                f"ONLINE NOTICE: UWB Anchor {target_mac} is up and running!"
                            )
                        anchor_health[target_mac] = True

            # --- STEP C: DYNAMIC POSITION COMPUTATION ---
            valid_count = sum(1 for d in current_distances if d is not None)

            # Compute positions if 3 or 4 anchors are fully operational
            if valid_count >= 3:
                r_safe = [
                    d if d is not None else 0.0 for d in current_distances
                ]
                r_sq = np.array(r_safe) ** 2

                for row_idx, (i, j) in enumerate(pair_indices):
                    b[row_idx] = (
                        (r_sq[j] - r_sq[i]) - anchor_sq[j] + anchor_sq[i]
                    )

                solution, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

                # Print the true scaled coordinates
                print(f"POSITION ({valid_count}/4 Anchors Active)-> X: {(solution[0]):.2f} cm | Y: {(solution[1]):.2f} cm\n")

        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Shutting down tracker safely.")
    ser.close()
