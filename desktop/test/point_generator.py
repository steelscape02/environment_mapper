import numpy as np

def sphere_points(n, radius=1.0, center=(0, 0, 0), noise=0.0, seed=None):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)   # unit vectors
    pts = v * radius + np.asarray(center)
    if noise > 0:
        pts += rng.normal(scale=noise, size=pts.shape)  # simulate sensor noise
    return pts