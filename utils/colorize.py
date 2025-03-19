"""
Utility for image colorization using OpenCV DNN.

Credits: 
    1. https://github.com/opencv/opencv/blob/master/samples/dnn/colorization.py
    2. http://richzhang.github.io/colorization/
    3. https://github.com/richzhang/colorization/
"""

import numpy as np
import cv2
import os

# Get the current directory for relative paths
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(CURRENT_DIR, 'model')

# Paths to load the model
PROTOTXT = os.path.join(MODEL_DIR, 'colorization_deploy_v2.prototxt')
POINTS = os.path.join(MODEL_DIR, 'pts_in_hull.npy')
MODEL = os.path.join(MODEL_DIR, 'colorization_release_v2.caffemodel')

def load_colorization_model():
    """
    Load the colorization model and prepare it for inference.
    
    Returns:
        net: The loaded neural network model
    """
    # Load the Model
    net = cv2.dnn.readNetFromCaffe(PROTOTXT, MODEL)
    pts = np.load(POINTS)

    # Load centers for ab channel quantization used for rebalancing.
    class8 = net.getLayerId("class8_ab")
    conv8 = net.getLayerId("conv8_313_rh")
    pts = pts.transpose().reshape(2, 313, 1, 1)
    net.getLayer(class8).blobs = [pts.astype("float32")]
    net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]
    
    return net

def colorize_image(input_path, output_path):
    """
    Colorize a black and white image and save the result
    
    Args:
        input_path (str): Path to input black and white image
        output_path (str): Path to save the colorized output image
    
    Returns:
        bool: True if successful, raises exception otherwise
    """
    # Ensure model directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Check if model files exist
    if not os.path.exists(PROTOTXT) or not os.path.exists(POINTS) or not os.path.exists(MODEL):
        raise FileNotFoundError(
            "Model files not found. Please download the required model files. "
            "See the original colorize.py file for download links."
        )
    
    # Load the model
    net = load_colorization_model()
    
    # Load the input image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Could not read image at {input_path}")
    
    scaled = image.astype("float32") / 255.0
    lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)

    resized = cv2.resize(lab, (224, 224))
    L = cv2.split(resized)[0]
    L -= 50

    # Colorize the image
    net.setInput(cv2.dnn.blobFromImage(L))
    ab = net.forward()[0, :, :, :].transpose((1, 2, 0))

    ab = cv2.resize(ab, (image.shape[1], image.shape[0]))

    L = cv2.split(lab)[0]
    colorized = np.concatenate((L[:, :, np.newaxis], ab), axis=2)

    colorized = cv2.cvtColor(colorized, cv2.COLOR_LAB2BGR)
    colorized = np.clip(colorized, 0, 1)

    colorized = (255 * colorized).astype("uint8")
    
    # Save the colorized image
    cv2.imwrite(output_path, colorized)
    
    return True

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    import argparse
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str, required=True,
        help="path to input black and white image")
    ap.add_argument("-o", "--output", type=str, required=True,
        help="path to save the colorized output image")
    args = vars(ap.parse_args())
    
    colorize_image(args["image"], args["output"])