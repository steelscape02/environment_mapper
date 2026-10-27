import numpy as np
import open3d as o3d
import serial
import threading
import queue
from math import sin,cos,radians

q = queue.Queue()
stop = threading.Event()
points = np.empty((0, 3))
pcd = o3d.geometry.PointCloud()

#UART parameters
PORT = "COM9"
BAUD = 115200
ENCODING = "ASCII"

#Testing radius
R=1

def uart_read(encoding:str,port:str,baud:int = 9600,timeout:float=1):
    with serial.Serial(port, baud, timeout=timeout) as ser:
        while not stop.is_set():
            line = ser.readline()
            if not line:
                continue
            try:
                pan, tilt, dist = map(float, line.decode(encoding,errors='ignore').strip().split(","))
            except ValueError:
                continue  # partial/garbled line

            #enqueue the new point
            q.put((pan, tilt, dist))

def update_callback(vis_obj):
    global points

    new = []
    while True:
        try:
            pan, tilt, d = q.get_nowait()
        except queue.Empty:
            break
        new.append(to_xyz(d, tilt, pan))

    if new:
        new_points = np.asarray(new, dtype=np.float64).reshape(-1, 3)
        points = np.vstack((points, new_points))
        pcd.points = o3d.utility.Vector3dVector(points)
        vis_obj.update_geometry(pcd)

    return False

def to_xyz(r, elevation, azimuth):
    el = radians(elevation)
    az = radians(azimuth)
    x = r * cos(el) * cos(az)
    y = r * cos(el) * sin(az)
    z = r * sin(el)
    return (x, y, z)

threading.Thread(target=uart_read, args=(ENCODING,PORT,BAUD), daemon=True).start()

vis = o3d.visualization.Visualizer()

pcd.points = o3d.utility.Vector3dVector(np.zeros((1, 3)))
vis.create_window(window_name="Live Sensor Stream", width=1280, height=720)

pcd.points = o3d.utility.Vector3dVector(
    np.array([[-R, -R, -R], [R, R, R]], dtype=np.float64)
)
vis.add_geometry(pcd)

opt = vis.get_render_option()
opt.point_size = 3.0

ctr = vis.get_view_control()
ctr.set_constant_z_near(0.01)
ctr.set_constant_z_far(100)

vis.register_animation_callback(update_callback)

vis.run()
vis.destroy_window()
stop.set()