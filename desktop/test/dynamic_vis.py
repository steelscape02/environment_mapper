import numpy as np
import open3d as o3d
from mock_sensor_stream import mock_sensor_stream

def dynamic_vis():
    #initialize the sensor data stream
    sensor = mock_sensor_stream(10_000,2,noise=0.2)
    init_points, init_colors = next(sensor)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(init_points)
    pcd.colors = o3d.utility.Vector3dVector(init_colors)

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="Live Sensor Stream (Screen Refresh Rate)", width=1280, height=720)
    vis.add_geometry(pcd)

    def update_callback(vis_obj):
        try:
            # Get new set of points
            new_points, new_colors = next(sensor)

            # Get a new set of points
            pcd.points = o3d.utility.Vector3dVector(new_points)
            pcd.colors = o3d.utility.Vector3dVector(new_colors)

            # Update geometry to reflect new pane
            vis_obj.update_geometry(pcd)
        except StopIteration:
            pass
        
        # keep loop running
        return True

    # Register callback, which is run once per frame (should be close to monitor refresh rate)
    vis.register_animation_callback(update_callback)
    vis.run()
    vis.destroy_window()