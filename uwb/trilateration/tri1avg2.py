"""
UWB Multilateration Tracker — Full All-Pairs Least Squares + Per-Anchor Block Averaging
------------------------------------------------------------------------------------------
Reads live ranging data from up to 4 UWB anchors over serial and computes the
tag's 2D position (x, y) in centimeters.

Approach:
  - No sub-grouping and no single reference anchor: every pair of currently
    ONLINE anchors is subtracted against every other online anchor
    (all-pairs linearization), forming one combined overdetermined system.
  - The equation system (A, b) is rebuilt DYNAMICALLY each block from only
    the anchors that actually have a valid reading — an anchor that is
    offline or hasn't completed its block average is fully excluded from
    every pair, rather than being zero-substituted. This fixes the
    zero-range corruption bug present in the earlier full-4-anchor scripts.
  - Solved via least squares (np.linalg.lstsq) once at least 3 anchors are
    online (minimum needed for a 2D solve with redundancy).

Temporal smoothing:
  - Each anchor accumulates its OWN raw readings independently. Once a
    given anchor collects BLOCK_SIZE (10) raw readings, they're averaged
    into a single distance value and that anchor's buffer is cleared to
    start collecting its next block. This is per-anchor block averaging
    (not a global/shared counter), so every anchor is smoothed over
    exactly its own 10 samples regardless of how fast/slow it reports —
    fixes the uneven-sampling bug from the global-counter version.
  - A position is computed any time all online anchors' distance slots are
    populated (>=3 of them) and their most-recent block averages haven't
    yet been consumed. After a position is printed, the consumed anchors'
    distance slots are cleared so the next position requires fresh block
    averages from those anchors.

Robustness:
  - Tracks per-anchor online/offline status via RX_TIMEOUT messages;
    offline anchors have their buffer and stored distance cleared and are
    excluded from the equation system until they come back online.
"""

import numpy as np
import re
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0"  # Verified by ls /dev/ttyACM* on Linux, or Device Manager on Windows
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(" Running Full All-Pairs Multilateration with Per-Anchor Block Averaging (10 readings)...")
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}.")
    print(f"Details: {e}")
    exit()

# Define your 4 Anchors in Centimeters (200cm square layout).
# Anchor order here must match the MAC-to-index mapping below.
anchors = np.array(
    [
        [0.0, 0.0],     # Anchor 0 (MAC: 0x0001) -0
        [200.0, 0.0],   # Anchor 1 (MAC: 0x0002) -2
        [0.0, 200.0],   # Anchor 2 (MAC: 0x0003) -4
        [200.0, 200.0], # Anchor 3 (MAC: 0x0004) -10
    ]
)
num_anchors = len(anchors)

mac_to_index = {"0x0001": 0, "0x0002": 1, "0x0003": 2, "0x0004": 3}

# Live health tracker (True = Online, False = Offline)
anchor_health = {mac: False for mac in mac_to_index.keys()}

# Pre-calculate anchor squared terms up front (used in every equation)
anchor_sq = anchors[:, 0] ** 2 + anchors[:, 1] ** 2

# --- PER-ANCHOR BLOCK AVERAGING STATE ---
BLOCK_SIZE = 10
distance_buffers = [[] for _ in range(num_anchors)]   # raw readings currently being collected, per anchor
current_distances = [None, None, None, None]           # most recent completed block average, per anchor

print("-" * 80)


def solve_multilateration(valid_indices, distances):
    """
    Builds and solves the all-pairs linearized system using ONLY the anchors
    listed in valid_indices (dynamic — excludes offline/not-yet-averaged
    anchors entirely rather than substituting a fake zero distance).
    """
    A_rows = []
    b_rows = []

    for a in range(len(valid_indices)):
        for c in range(a + 1, len(valid_indices)):
            i = valid_indices[a]
            j = valid_indices[c]

            ri = distances[i]
            rj = distances[j]

            A_rows.append(
                [
                    2 * (anchors[i, 0] - anchors[j, 0]),
                    2 * (anchors[i, 1] - anchors[j, 1]),
                ]
            )
            b_rows.append((rj**2 - ri**2) - anchor_sq[j] + anchor_sq[i])

    A = np.array(A_rows)
    b = np.array(b_rows)

    solution, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return solution


# --- 2. MAIN PARSING LOOP ---
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
                        idx = mac_to_index[mac]
                        if anchor_health[mac] is True:
                            print(f" OFFLINE ALERT: UWB Anchor {mac} went down! (RX_TIMEOUT)")
                        anchor_health[mac] = False
                        current_distances[idx] = None
                        distance_buffers[idx].clear()
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

                        if anchor_health[target_mac] is False:
                            print(f" ONLINE NOTICE: UWB Anchor {target_mac} is up and running!")
                        anchor_health[target_mac] = True

                        # Accumulate this anchor's OWN raw readings
                        distance_buffers[idx].append(target_dist)

                        # This anchor's block is complete -> average it and reset its buffer
                        if len(distance_buffers[idx]) >= BLOCK_SIZE:
                            current_distances[idx] = sum(distance_buffers[idx]) / BLOCK_SIZE
                            distance_buffers[idx].clear()

            # --- STEP C: COMPUTE POSITION ONCE ENOUGH ANCHORS HAVE A FRESH BLOCK AVERAGE ---
            valid_indices = [i for i in range(num_anchors) if current_distances[i] is not None]

            if len(valid_indices) >= 3:
                tag_x, tag_y = solve_multilateration(valid_indices, current_distances)

                print(
                    f" POSITION ({len(valid_indices)}/4 Anchors) -> X: {tag_x:7.2f} cm | Y: {tag_y:7.2f} cm"
                )

                # Consume the block averages that were just used -> forces fresh
                # 10-reading blocks from these anchors before the next position.
                for idx in valid_indices:
                    current_distances[idx] = None

        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Closing serial stream and shutting down tracker safely.")
    ser.close()