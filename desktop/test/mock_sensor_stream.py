import numpy as np

# Simulated sensor stream generator at 60 Hz
def mock_sensor_stream(n : int, radius:float=1.0, center:tuple=(0, 0, 0), noise:float=0.0, seed=None):
    """
    Mock data stream generator. Modified from ``point_generator``.

    :param n: Number of points to generate per iteration.
    :type n: int
    :param radius: Radius of the sphere.
    :type radius: float
    :param center: Center point of the sphere as ``(x, y, z)``.
    :type center: tuple
    :param noise: Standard deviation of Gaussian noise to add to the generated points.
    :type noise: float
    :param seed: Random seed for reproducible sampling. If ``None``, entropy is derived from the OS.
    :type seed: int or None
    """

    # create a random generator
    rng = np.random.default_rng(seed)

    while True:
        v = rng.normal(size=(n, 3))
        v /= np.linalg.norm(v, axis=1, keepdims=True)   # unit vectors
        pts = v * radius + np.asarray(center)
        if noise > 0:
            pts += rng.normal(scale=noise, size=pts.shape)  # simulate sensor noise

        # get some pretty colors
        colors = np.random.rand(n, 3).astype(np.float64)
        yield pts, colors