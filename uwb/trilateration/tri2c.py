"""
UWB Trilateration Tracker — Logic 2 + Block Downsampling (10-Packet Averaging)
--------------------------------------------------------------------------------
Reads live ranging data from 4 UWB anchors over serial by averaging 
10 readings of individual anchors and computes thetag's 2D position 
(x, y) in centimeters.

Approach:
  - Same trilateration core as the base Hybrid Logic 2: splits the 4
    anchors into 3 overlapping triads (Groups 123, 234, 134), forms all
    3 pairwise-subtracted range equations per triad, solves each via
    least squares (np.linalg.lstsq), then averages results across the
    triads that have valid data.
  - Adds a pre-filtering stage: each anchor's raw distance readings are
    accumulated into a per-anchor buffer. Once 10 raw readings arrive,
    they're averaged into a single value, pushed into the working
    distance array, and the buffer is cleared (tumbling/block average,
    NOT a sliding moving average).
  - Position is computed only once at least 3 of 4 anchors have a fresh
    10-reading block average ready. After each position output, all
    anchor distance slots are reset to None, forcing every subsequent
    position to wait for entirely new blocks of 10 readings per anchor.

Robustness:
  - Tracks per-anchor online/offline status via RX_TIMEOUT messages;
    clears that anchor's in-progress accumulator block if it drops.

Tradeoff: substantially reduces per-packet ranging noise (via the
10-sample block average) at the cost of a much lower position update
rate compared to the unfiltered variants — good for a stationary or
slow-moving tag, less suited to fast motion tracking.
"""
import numpy as np
import re
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0"  # Verified by ls /dev/ttyACM* command on Linux or check Device Manager on Windows
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(" Running Hybrid Logic with Block Downsampling (10-Packet Averaging)...")
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}. Close Minicom!")
    print(f"Details: {e}")
    exit()

# Define your 4 Anchors in Centimeters 
anchors = np.array([
    [0.0, 0.0],       # Anchor index 0 (MAC: 0x0001) - 0
    [0.0, 60.0],      # Anchor index 1 (MAC: 0x0003) - 2
    [60.0, 0.0],      # Anchor index 2 (MAC: 0x0002) - 4
    [60.0, 60.0]      # Anchor index 3 (MAC: 0x0004) - 10
])
num_anchors = len(anchors)

# Map MAC address strings to internal indexes
mac_to_index = {"0x0001": 0, "0x0003": 1, "0x0002": 2, "0x0004": 3}

# Live health tracker
anchor_health = {mac: False for mac in mac_to_index.keys()}

# --- BLOCK DOWNSAMPLING ACCUMULATORS ---
BLOCK_SIZE = 10
# Lists of lists to hold the raw values for the current block
distance_accumulator = [[] for _ in range(num_anchors)]

# Persistent Memory Buffer: It holds the final averaged block distance for the math
current_distances = [None, None, None, None]

# Pre-calculate anchor squared terms up front (Optimization)
anchor_sq = anchors[:, 0]**2 + anchors[:, 1]**2

# Hybrid Sub-Group Configurations
groups_config = [
    {"name": "Group 123", "indices": [0, 1, 2], "pairs": [(0, 1), (0, 2), (1, 2)]},
    {"name": "Group 234", "indices": [1, 2, 3], "pairs": [(1, 2), (1, 3), (2, 3)]},
    {"name": "Group 134", "indices": [0, 1, 3], "pairs": [(0, 1), (0, 3), (1, 3)]}
]

print("-" * 80)

# --- 2. MAIN STATE-TRACKING LOOP ---
try:
    while True:
        raw_line = ser.readline()
        if not raw_line:
            continue
            
        try:
            line = raw_line.decode('utf-8').strip()
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
                        distance_accumulator[idx].clear() # Reset this accumulator block
                continue
            
            # --- CONDITION B: PROCESS SUCCESSFUL READINGS ---
            if "SUCCESS" in line and "distance[cm]=" in line:
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                dist_match = re.search(r"distance\[cm\]=([0-9.]+)", line)
                
                if mac_match and dist_match:
                    target_mac = mac_match.group(1)
                    target_dist = float(dist_match.group(1))
                    
                    if target_mac in mac_to_index:
                        idx = mac_to_index[target_mac]
                        
                        # Step B1: Accumulate raw readings for this anchor block
                        distance_accumulator[idx].append(target_dist)
                        
                        if anchor_health[target_mac] is False:
                            print(f" ONLINE NOTICE: UWB Anchor {target_mac} is up and running!")
                        anchor_health[target_mac] = True
                        
                        # Step B2: Check if this anchor has filled its block of 10 readings
                        if len(distance_accumulator[idx]) >= BLOCK_SIZE:
                            # Calculate the clean mean of this block and save it to memory
                            current_distances[idx] = sum(distance_accumulator[idx]) / BLOCK_SIZE
                            # WIPE the accumulator array clean to start gathering the NEXT 10 readings
                            distance_accumulator[idx].clear()

            # --- STEP C: EXECUTE LEAST SQUARES ONLY IF ALL ACCUMULATORS HAVE CALCULATED A BLOCK ---
            # Gatekeeper: We only calculate positions when the system memory holds non-None block averages
            valid_count = sum(1 for d in current_distances if d is not None)
            
            # Run matrix math when 3 or 4 anchors have a freshly averaged block ready
            if valid_count >= 3:
                valid_coordinates = []
                
                for g in groups_config:
                    if all(current_distances[idx] is not None for idx in g["indices"]):
                        sub_A = np.zeros((3, 2))
                        sub_b = np.zeros(3)
                        
                        for row_idx, (i, j) in enumerate(g["pairs"]):
                            ri = current_distances[i]
                            rj = current_distances[j]
                            
                            sub_A[row_idx, 0] = 2 * (anchors[i, 0] - anchors[j, 0])
                            sub_A[row_idx, 1] = 2 * (anchors[i, 1] - anchors[j, 1])
                            sub_b[row_idx] = (rj**2 - ri**2) - anchor_sq[j] + anchor_sq[i]
                        
                        solution, _, _, _ = np.linalg.lstsq(sub_A, sub_b, rcond=None)
                        valid_coordinates.append(solution)
                
                # --- STEP D: CALCULATE AND DISPLAY COMPROMISE POINT ---
                if len(valid_coordinates) > 0:
                    avg_coords = np.mean(valid_coordinates, axis=0)
                    
                    tag_x = avg_coords[0]
                    tag_y = avg_coords[1]
                    
                    print(f" BLOCK POSITION ({valid_count}/4 Blocks Averaged) -> X: {tag_x:7.2f} cm | Y: {tag_y:7.2f} cm")
                    
                    # RESET the memory buffer slots to None. This FORCES the loop to wait 
                    # until the next independent blocks of 10 readings are fully gathered.
                    current_distances = [None, None, None, None]
                    
        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Closing serial stream and shutting down tracker safely.")
    ser.close()
