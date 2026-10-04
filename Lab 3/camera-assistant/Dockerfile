FROM ghcr.io/blakeblackshear/frigate@sha256:9594684d8d16734d3b9eaede807f8caa78e500a117fb77b82e48aa6232e77ff6
# Use one coherent cv2 package at the upstream version, without GUI libraries.
RUN python3 -m pip uninstall --break-system-packages -y opencv-contrib-python opencv-python-headless \
 && python3 -m pip install --break-system-packages --no-cache-dir --no-deps opencv-contrib-python-headless==4.11.0.86 \
 && python3 -c "import cv2; print(cv2.__version__)"
