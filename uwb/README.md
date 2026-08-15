# UWB Tracker — Columbus Maximus

A ROS2 package for UWB (Ultra-Wideband) trilateration — reads distance readings from 4 fixed anchors over serial, computes a moving tag's (x, y) position, and optionally visualizes everything live in RViz.

---

## Repository structure

```
uwb/
├── uwb_tracker/                  # The actual ROS2 package — clone this into your ros2_ws/src
│   ├── uwb_tracker/              # Python package containing the node code
│   │   ├── __init__.py           # Marks this folder as a Python package (leave empty)
│   │   ├── uwb_node.py           # Basic node — computes & publishes tag coordinates only
│   │   └── uwb_node_rviz.py      # Full node — coordinates + complete RViz visualization
│   ├── setup.py                  # Package build config, entry points (which commands run which file)
│   ├── setup.cfg
│   └── package.xml               # Package metadata + dependencies
│
├── datasheets/
│   └── *.pdf                     # Reference datasheets for the UWB modules and SDK
│
└── trilateration/
    └── *.py                      # Standalone reference scripts showing the trilateration math on its own —
                                   # for reading/reference only, NOT meant to be run directly
```

### What each part is for

| Path | Purpose |
|---|---|
| `uwb_tracker/` (outer) | The actual buildable ROS2 package. This is the only folder that needs to go inside a ROS2 workspace. |
| `uwb_tracker/uwb_tracker/uwb_node.py` | Minimal node — reads serial, runs trilateration, publishes the tag's (x, y) as a `geometry_msgs/Point` on `/uwb_pose`. No visualization. |
| `uwb_tracker/uwb_tracker/uwb_node_rviz.py` | Everything `uwb_node.py` does, **plus** publishes the anchors, moving tag, and a motion trail for RViz. Use this one if you want to *see* the tracking, not just read numbers. |
| `datasheets/` | Reference PDFs for the UWB hardware/SDK. |
| `trilateration/` | Simple, standalone Python scripts showing just the distance→position math in isolation. Useful for understanding the algorithm — don't run these expecting a working ROS node, they're reference only. |

---

## Prerequisites

- Ubuntu with **ROS2** installed (Humble or later)
- Python 3.10+
- Two Python packages:

```bash
pip install pyserial numpy --break-system-packages
```

---

## Setup — cloning and building

**1. Clone the repository** (anywhere on your machine — this does *not* need to be inside your ROS2 workspace):

```bash
git clone <your-repo-url>
cd <repo-name>/uwb
```

**2. Copy only the ROS2 package into your workspace** — `datasheets/` and `trilateration/` stay where they are; only `uwb_tracker/` needs to move:

```bash
cp -r uwb_tracker ~/ros2_ws/src/
```

**3. Build it:**

```bash
cd ~/ros2_ws
colcon build --packages-select uwb_tracker
source install/setup.bash
```

> Re-run `source install/setup.bash` in every **new** terminal you open before using `ros2 run` — it's what tells that terminal your package exists.

---

## Serial port permissions

Your UWB board connects as something like `/dev/ttyACM0`. Linux restricts who can read/write that device by default, so you'll likely hit a `Permission denied` error the first time you run the node.

### Option A — quick fix (temporary)

```bash
sudo chmod 666 /dev/ttyACM0
```

Run this **right before** `ros2 run`, any time you get a permission error. Fine for a one-off test — but the permission resets every time the board is unplugged/replugged or the system reboots, so you'd need to repeat this command each time.

### Option B — permanent fix (recommended)

Add your user to the `dialout` group, which already has permission to access serial devices:

```bash
sudo usermod -aG dialout $USER
```

**This does not apply immediately** — group changes only take effect on your *next* login. Either:

```bash
sudo reboot
```

or log out and log back in manually.

**Verify it worked** after logging back in:

```bash
groups
```

You should see `dialout` somewhere in the output. Once confirmed, `/dev/ttyACM0` will just work with no `chmod` needed, permanently — even across reboots and reconnects.

---

## Running the node

**Basic version** — just coordinates, no visualization:

```bash
ros2 run uwb_tracker uwb_node
```

**Full version** — coordinates + RViz visualization data:

```bash
ros2 run uwb_tracker uwb_node_rviz
```

---

## Visualizing in RViz

There's no pre-saved RViz config anymore — set it up manually, once per session:

1. With `uwb_node_rviz` already running in one terminal, open a **new terminal** and launch RViz:
   ```bash
   rviz2
   ```
2. In the left panel, set **Fixed Frame** to `world` (near the top, under Global Options).
3. Click **Add** (bottom left) → **By topic** tab, and add each of the following:
   - `/tag_marker` → Marker
   - `/tag_path` → Path
   - `/anchor_markers` → MarkerArray

You should then see the four anchors, the moving tag, and its motion trail appear as `uwb_node_rviz` publishes data.

---

## Testing without physical hardware

No UWB chips on hand? `fake_uwb_simple.py` simulates 4 anchors and a moving tag, sending fake but realistic serial data — your node can't tell the difference.

**In one terminal**, run the simulator:

```bash
python3 fake_uwb_simple.py
```

It will print a line like:

```
Point your node's SERIAL_PORT at: /dev/pts/5
```

Leave this terminal running — closing it stops the fake data.

**In `uwb_node.py` or `uwb_node_rviz.py`**, temporarily change:

```python
self.SERIAL_PORT = "/dev/ttyACM0"
```

to the path the simulator printed:

```python
self.SERIAL_PORT = "/dev/pts/5"
```

Rebuild, then run the node as usual **in a second terminal**:

```bash
cd ~/ros2_ws
colcon build --packages-select uwb_tracker
source install/setup.bash
ros2 run uwb_tracker uwb_node_rviz
```

> Remember to change `SERIAL_PORT` back to `/dev/ttyACM0` before testing with real hardware again.

---

## Troubleshooting quick reference

| Symptom | Likely cause |
|---|---|
| `PermissionError: [Errno 13] Permission denied` | See [Serial Port Permissions](#serial-port-permissions) above |
| `No such file or directory: '/dev/ttyACM0'` | Board isn't plugged in, or wrong port — check `ls /dev/ttyACM*` |
| RViz viewport is blank | Fixed Frame doesn't match `"world"`, or camera is zoomed/angled away — try the Reset button |
| `No executable found` on `ros2 run` | Package wasn't rebuilt after changes — run `colcon build --packages-select uwb_tracker` again |
