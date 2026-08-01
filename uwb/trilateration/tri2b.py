"""
UWB Trilateration Tracker — Logic 2: Hybrid Sub-Group Least Squares (All-Pairs)
--------------------------------------------------------------------------------
Reads live ranging data from 4 UWB anchors over serial and computes the
tag's 2D position (x, y) in centimeters.

Approach:
  - Splits the 4 anchors into 3 overlapping triads (Groups 123, 234, 134).
  - For each triad, forms ALL 3 pairwise-subtracted range equations
    (A-B, A-C, B-C) rather than picking a single reference anchor —
    this makes each triad's local system overdetermined (3 equations,
    2 unknowns).
  - Solves each triad's overdetermined system via least squares
    (np.linalg.lstsq), letting the redundant equation help average out
    noise within the group itself.
  - Averages the (x, y) results from however many of the 3 groups solved
    successfully (anchors online) to produce the final position estimate.

Robustness:
  - Tracks per-anchor online/offline status via RX_TIMEOUT messages.
  - Holds last-known distance per anchor so a group can still solve even
    if a DIFFERENT anchor (outside that group) is temporarily offline.
  - No temporal smoothing filter — each serial update produces an
    immediate, independent position estimate.

Note: unlike an exact 2-equation solve, the extra pairwise equation per
group provides local (spatial) noise averaging before the cross-group
average is taken — generally more robust to a single noisy anchor than
a purely exact reference-anchor solve, at a small extra compute cost.
"""

import numpy as np
import re
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0" # Verified by ls /dev/ttyACM* command on Linux or check Device Manager on Windows
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(
        " Running Hybrid Logic: All-Pairs Least Squares inside 3 Sub-Groups..."
    )
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}. Close Minicom!")
    print(f"Details: {e}")
    exit()

# Define your 4 Anchors in Centimeters i.e. place them on vertices of a square arrangement of side 200cm here. The order of anchors is important and must match the MAC address mapping below.
anchors = np.array(
    [
        [0.0, 0.0],  # Anchor index 0 (MAC: 0x0001) -  0
        [0.0, 200.0],  # Anchor index 1 (MAC: 0x0002) -  2
        [200.0, 0.0],  # Anchor index 2 (MAC: 0x0003) -  4
        [200.0, 200.0],  # Anchor index 3 (MAC: 0x0004) -  10
    ]
)
num_anchors = len(anchors)

# Map MAC address strings to internal indexes (Axes Fixed Alignment)
mac_to_index = {"0x0001": 0, "0x0003": 1, "0x0002": 2, "0x0004": 3}

# Live health tracker and State memory buffer
anchor_health = {mac: False for mac in mac_to_index.keys()}
current_distances = [None, None, None, None]

# Pre-calculate anchor squared terms up front (Optimization)
anchor_sq = anchors[:, 0] ** 2 + anchors[:, 1] ** 2

# --- HYBRID SUB-GROUP DEFINITIONS ---
# Each group now defines its 3 unique internal anchor index pairs.
# With 3 anchors, there are exactly 3 pairs: (A,B), (A,C), (B,C)
groups_config = [
    {
        "name": "Group 123",
        "indices": [0, 1, 2],
        "pairs": [(0, 1), (0, 2), (1, 2)],
    },  # Anchors 1, 3, 2
    {
        "name": "Group 234",
        "indices": [1, 2, 3],
        "pairs": [(1, 2), (1, 3), (2, 3)],
    },  # Anchors 3, 2, 4
    {
        "name": "Group 134",
        "indices": [0, 1, 3],
        "pairs": [(0, 1), (0, 3), (1, 3)],
    },  # Anchors 1, 3, 4
]

print("-" * 80)

# --- 2. MAIN STATE-TRACKING LOOP ---
try:
    while True:
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
                                f" OFFLINE ALERT: UWB Anchor {mac} went down! (RX_TIMEOUT)"
                            )
                        anchor_health[mac] = False
                        current_distances[mac_to_index[mac]] = None
                continue

            # --- CONDITION B: SUCCESSFUL READINGS ---
            if "SUCCESS" in line and "distance[cm]=" in line:
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                dist_match = re.search(r"distance\[cm\]=([0-9.]+)", line)

                if mac_match and dist_match:
                    target_mac = mac_match.group(1)
                    target_dist = float(dist_match.group(1))

                    if target_mac in mac_to_index:
                        idx = mac_to_index[target_mac]
                        current_distances[idx] = target_dist

                        if anchor_health[target_mac] is False:
                            print(
                                f" ONLINE NOTICE: UWB Anchor {target_mac} is up and running!"
                            )
                        anchor_health[target_mac] = True

            # --- STEP C: PROCESS HYBRID SUB-GROUP LEAST SQUARES ---
            valid_coordinates = []

            for g in groups_config:
                # Check if all 3 anchors for this subgroup are online
                if all(current_distances[idx] is not None for idx in g["indices"]):

                    # Pre-allocate a 3x2 Matrix A and a 3-element Vector b for this group
                    sub_A = np.zeros((3, 2))
                    sub_b = np.zeros(3)

                    # Build the 3 equations by subtracting each anchor from each other
                    for row_idx, (i, j) in enumerate(g["pairs"]):
                        ri = current_distances[i]
                        rj = current_distances[j]

                        # Fill row of sub_A
                        sub_A[row_idx, 0] = 2 * (anchors[i, 0] - anchors[j, 0])
                        sub_A[row_idx, 1] = 2 * (anchors[i, 1] - anchors[j, 1])

                        # Fill row of sub_b
                        sub_b[row_idx] = (
                            (rj**2 - ri**2) - anchor_sq[j] + anchor_sq[i]
                        )

                    # Solve this group's 3-equation system using Least Squares
                    solution, _, _, _ = np.linalg.lstsq(
                        sub_A, sub_b, rcond=None
                    )
                    valid_coordinates.append(solution)

            # --- STEP D: GLOBAL AVERAGE REPORTING ---
            if len(valid_coordinates) > 0:
                # Average the coordinates from all active solved subgroups
                avg_coords = np.mean(valid_coordinates, axis=0)

                tag_x = avg_coords[0]
                tag_y = avg_coords[1]

                print(
                    f" HYBRID POSITION ({len(valid_coordinates)}/3 Groups) -> X: {tag_x:7.2f} cm | Y: {tag_y:7.2f} cm"
                )

        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Closing serial stream and shutting down tracker safely.")
    ser.close()
