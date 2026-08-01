import collections
import re
import numpy as np
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0"   # Verify from your terminal with 'ls /dev/tty*' command
BAUD_RATE = 115200  # Check what parameter you want to set for the baud rate while calibrating the UWB module.

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()  
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(" Listening with 5-Step Moving Average Smoothing...")
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}. Close Minicom!")
    print(f"Details: {e}")
    exit()

# Anchors defined strictly in Centimeters 
anchors = np.array([
    [0.0, 0.0],       # Anchor 0 (MAC: 0x0001) - Bottom Left
    [60.0, 0.0],      # Anchor 1 (MAC: 0x0002) - Bottom Right
    [0.0, 60.0],      # Anchor 2 (MAC: 0x0003) - Top Left
    [60.0, 60.0]      # Anchor 3 (MAC: 0x0004) - Top Right
])
num_anchors = len(anchors)

# Map MAC address strings to internal indexes
mac_to_index = {  #this dictionary allows us to quickly convert a MAC address string into an index for our anchors list
    "0x0001": 0,
    "0x0002": 1,
    "0x0003": 2,
    "0x0004": 3
}

# Live health tracker
anchor_health = {mac: False for mac in mac_to_index.keys()}

# --- MOVING AVERAGE CONFIGURATION ---
WINDOW_SIZE = 5
# Create a sliding history memory list for each of the 4 anchors.
# 'maxlen=5' means when item #6 arrives, item #1 is pushed out automatically.
history = [collections.deque(maxlen=WINDOW_SIZE) for _ in range(num_anchors)]

# --- 2. OPTIMIZATION: PRE-CALCULATE STATIC PROPERTIES ---
anchor_sq = anchors[:, 0]**2 + anchors[:, 1]**2

A_list = []
pair_indices = []
for i in range(num_anchors):
    for j in range(i + 1, num_anchors):
        A_list.append([2 * (anchors[i, 0] - anchors[j, 0]), 2 * (anchors[i, 1] - anchors[j, 1])])
        pair_indices.append((i, j))

A = np.array(A_list)  
b = np.zeros(6)       

print("-" * 80)

# --- 3. MAIN LOOP ---
try:
    while True:
        raw_line = ser.readline()
        if not raw_line:
            continue
            
        try:
            line = raw_line.decode('utf-8').strip()
            if not line:
                continue
            
            # --- CONDITION A: OFFLINE ALERTS ---
            if "RX_TIMEOUT" in line:
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                if mac_match:
                    mac = mac_match.group(1)
                    if mac in mac_to_index:
                        if anchor_health[mac] is True:
                            print(f"OFFLINE: Anchor {mac} went down!")
                        anchor_health[mac] = False
                        history[mac_to_index[mac]].clear()  # Clear history for this dead anchor
                continue
            
            # --- CONDITION B: SUCCESSFUL READINGS ---
            if "SUCCESS" in line:
                mac_match = re.search(r"mac_address=(0x[0-9a-fA-F]+)", line)
                dist_match = re.search(r"distance\[cm\]=([0-9.]+)", line)
                
                if mac_match and dist_match:
                    target_mac = mac_match.group(1)
                    target_dist = float(dist_match.group(1))
                    
                    if target_mac in mac_to_index:
                        idx = mac_to_index[target_mac]
                        
                        # Add the fresh reading to this anchor's moving history list
                        history[idx].append(target_dist)
                        
                        if anchor_health[target_mac] is False:
                            print(f"ONLINE: Anchor {target_mac} is active!")
                        anchor_health[target_mac] = True

            # --- STEP C: CALCULATE SMOOTHED COORDINATES ---
            # Check how many anchors have collected a baseline profile of at least 3 historical readings
            valid_anchors = [idx for idx in range(num_anchors) if len(history[idx]) >= 3]
            valid_count = len(valid_anchors)
            
            # Run calculations if 3 or 4 anchors have history lines ready
            if valid_count >= 3:
                
                # Dynamic Averaging: Calculate the mean of the sliding window for each active anchor
                # 1. Pre-allocate as a NumPy array
                smoothed_distances = np.zeros(num_anchors)

                for idx in range(num_anchors):
                    if len(history[idx]) > 0:
                        smoothed_distances[idx] = sum(history[idx]) / len(history[idx])
                    else:
                        smoothed_distances[idx] = 0.0


                r_sq = smoothed_distances**2 

                for row_idx, (i, j) in enumerate(pair_indices):
                    b[row_idx] = (r_sq[j] - r_sq[i]) - anchor_sq[j] + anchor_sq[i]
                
                solution, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
                
                # Print output
                print(f" POSITION ({valid_count}/4 Anchors Active) -> X: {solution[0]:.2f} cm | Y: {solution[1]:.2f} cm")

            
        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Shutting down tracker safely.")
    ser.close()
