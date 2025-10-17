def test_laplacian():
    import numpy as np
    import cv2
    from core.preprocessing import laplacian_variance
    img = np.zeros((100,100), dtype=np.uint8)
    assert laplacian_variance(img) >= 0
