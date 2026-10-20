import numpy as np
from pathlib import Path

#import test funcs
from point_generator import sphere_points
from static_vis import static_visualizer

output_path = (
    Path(__file__).resolve().parent.parent
    / "test_outputs"
    / "sphere.xyz"
)

def main():
    #generate a point cloud and save
    pts = sphere_points(50000, radius=2.0, noise=0.05, seed=42)
    np.savetxt(output_path, pts, fmt="%.6f")

    static_visualizer(output_path)

if __name__ == "__main__":
    main()