import open3d as o3d
from os import PathLike

def static_visualizer(filename:PathLike):
    """Load and display a point cloud from a file.

    The loaded point cloud is printed to the console and displayed in an
    Open3D visualization window.

    :param filename: Path to the point-cloud file to load.
    :type filename: PathLike
    :returns: None.
    :rtype: None
    """
    pcd = o3d.io.read_point_cloud(filename)
    print(pcd)
    o3d.visualization.draw_geometries([pcd])