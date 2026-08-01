import re
import numpy as np
import serial

# --- 1. HARDWARE CONFIGURATION ---
SERIAL_PORT = "/dev/ttyACM0"   # Your verified serial port
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    ser.flush()  
    print(f" Connected to Serial Port: {SERIAL_PORT}")
    print(" Sub-Groups Averaging (3 Equations, 3 Groups)...")
except Exception as e:
    print(f" ERROR: Could not open port {SERIAL_PORT}. Close Minicom!")
    print(f"Details: {e}")
    exit()

# Define your 4 Anchors in Centimeters 
anchors = np.array([
    [0.0, 0.0],       # Anchor 0 (MAC: 0x0001) - Index 0
    [200.0, 0.0],      # Anchor 1 (MAC: 0x0002) - Index 1
    [0.0, 200.0],      # Anchor 2 (MAC: 0x0003) - Index 2
    [200.0, 200.0]      # Anchor 3 (MAC: 0x0004) - Index 3
])
num_anchors = len(anchors)

# Map MAC address strings to internal indexes
mac_to_index = {
    "0x0001": 0,
    "0x0002": 1,
    "0x0003": 2,
    "0x0004": 3
}

# Live health tracker (True = Online, False = Offline)
anchor_health = {mac: False for mac in mac_to_index.keys()}

# Persistent Memory Buffer: Stores the last known valid distance for each anchor slot
current_distances = [None, None, None, None]

# Pre-calculate anchor squared terms up front (Optimization)
anchor_sq = anchors[:, 0]**2 + anchors[:, 1]**2

# --- LOGIC DEFINITIONS: THE 3 GROUPS ---
# Group 1: Anchors [0, 1, 2] (Ref: 0) -> Equations relative to 0: (0,1) and (0,2)
# Group 2: Anchors [1, 2, 3] (Ref: 1) -> Equations relative to 1: (1,2) and (1,3)
# Group 3: Anchors [0, 2, 3] (Ref: 2) -> Equations relative to 2: (2,0) and (2,3)
groups_config = [
    {"name": "Group 123", "indices": [0, 1, 2], "ref": 0, "others": [1, 2]},
    {"name": "Group 234", "indices": [1, 2, 3], "ref": 1, "others": [2, 3]},
    {"name": "Group 134", "indices": [0, 2, 3], "ref": 2, "others": [0, 3]}
]

print("-" * 80)

# --- 2. FAST DETERMINANT SOLVER FOR A 2x2 SYSTEM ---
def solve_2x2_determinant(M11, M12, M21, M22, R1, R2):
    """Solves a 2x2 system of equations using Cramer's Determinant Rule."""
    D = (M11 * M22) - (M12 * M21)
    if abs(D) < 1e-5:
        return None  # Parallel lines, can't divide by zero
    
    Dx = (R1 * M22) - (M12 * R2)
    Dy = (M11 * R2) - (R1 * M21)
    
    x = Dx / D
    y = Dy / D
    return x, y

# --- 3. MAIN STATE-TRACKING LOOP ---
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
                        if anchor_health[mac] is True:
                            print(f" OFFLINE ALERT: UWB Anchor {mac} went down! (RX_TIMEOUT)")
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
                            print(f" ONLINE NOTICE: UWB Anchor {target_mac} is up and running!")
                        anchor_health[target_mac] = True

            # --- STEP C: LOGIC 2 SEPARATE GROUP EVALUATIONS ---
            valid_coordinates = []
            
            # Walk through each of our 3 configurations
            for g in groups_config:
                ref_idx = g["ref"]
                other1, other2 = g["others"]
                
                # Check if all 3 anchors needed for THIS specific group are currently online
                if (current_distances[ref_idx] is not None and 
                    current_distances[other1] is not None and 
                    current_distances[other2] is not None):
                    
                    # Extract coordinates and radii values for the math
                    x_ref, y_ref = anchors[ref_idx]
                    x1, y1 = anchors[other1]
                    x2, y2 = anchors[other2]
                    
                    r_ref = current_distances[ref_idx]
                    r1 = current_distances[other1]
                    r2 = current_distances[other2]
                    
                    # Linearize Equation 1: (Ref subtracted from other1)
                    M11 = 2 * (x_ref - x1)
                    M12 = 2 * (y_ref - y1)
                    R1 = (r1**2 - r_ref**2) - (x1**2 + y1**2) + anchor_sq[ref_idx]
                    
                    # Linearize Equation 2: (Ref subtracted from other2)
                    M21 = 2 * (x_ref - x2)
                    M22 = 2 * (y_ref - y2)
                    R2 = (r2**2 - r_ref**2) - (x2**2 + y2**2) + anchor_sq[ref_idx]
                    
                    # Solve the 2x2 system using Cramer's Determinant Rule
                    coord_result = solve_2x2_determinant(M11, M12, M21, M22, R1, R2)
                    
                    if coord_result is not None:
                        valid_coordinates.append(coord_result)

            # --- STEP D: FINAL GLOBAL COORDINATE AVERAGING ---
            # We calculate the final coordinate average if at least one subgroup has a valid answer
            if len(valid_coordinates) > 0:
                x_sum = sum(coord[0] for coord in valid_coordinates)
                y_sum = sum(coord[1] for coord in valid_coordinates)
                
                final_x = x_sum / len(valid_coordinates)
                final_y = y_sum / len(valid_coordinates)
                
                print(f"POSITION UPDATE (Logic 2: {len(valid_coordinates)}/3 Groups Solved) -> X: {final_x:7.2f} cm | Y: {final_y:7.2f} cm")

        except (ValueError, UnicodeDecodeError, IndexError):
            continue

except KeyboardInterrupt:
    print("\n Closing serial stream and shutting down tracker safely.")
    ser.close()
