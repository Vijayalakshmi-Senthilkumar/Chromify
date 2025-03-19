
# Image Colorization Web App

## Overview
This project is a Flask-based web application that allows users to upload black-and-white images and get them colorized using OpenCV DNN. The application provides a user-friendly interface with drag-and-drop functionality, real-time preview, and download options.

## Features
- Upload black-and-white images for colorization
- Real-time preview of original and colorized images
- Adjustable image settings (brightness, contrast, saturation)
- Download the processed image
- Automatic cleanup of old files
- Secure session-based file management

## Technologies Used
- **Backend:** Flask, OpenCV, NumPy
- **Frontend:** HTML, CSS, JavaScript (with Fetch API)
- **Database:** JSON-based storage (for metadata tracking)
- **Model:** OpenCV Deep Learning (DNN) for image colorization

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Flask
- OpenCV
- NumPy

### Setup Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/image-colorization.git
   cd image-colorization
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Download the required model files and place them in the `model/` directory.
   - `colorization_deploy_v2.prototxt`
   - `colorization_release_v2.caffemodel`
   - `pts_in_hull.npy`
4. Run the Flask app:
   ```sh
   python app.py
   ```
5. Open a browser and go to:
   ```
   http://127.0.0.1:5000
   ```

## Usage
1. Drag and drop a black-and-white image or select one using the file input.
2. The image will be uploaded and processed automatically.
3. Adjust brightness, contrast, and saturation if needed.
4. Download the colorized image.

## Project Structure
```
image-colorization/
│-- static/
│   │-- uploads/          # Stores uploaded and processed images
│   │-- style.css         # Styles for the frontend
│   │-- script.js         # Handles frontend interactions
│-- templates/
│   │-- index.html        # Main HTML file
│-- model/                # Stores deep learning models
│-- utils/
│   │-- colorize.py       # Contains image processing logic
│-- app.py                # Main Flask application
│-- requirements.txt      # Dependencies
│-- README.md             # Project documentation
```

## API Endpoints
### 1. Upload and Colorize Image
**Endpoint:**
```http
POST /api/colorize
```
**Request:**
- Form-data with key `image`

**Response:**
```json
{
  "original": "/static/uploads/original.jpg",
  "colorized": "/static/uploads/colorized.jpg",
  "session_id": "1234-abcd"
}
```

### 2. Cleanup Files (Manual Cleanup)
**Endpoint:**
```http
POST /api/cleanup
```
**Request:**
```json
{
  "files": ["/static/uploads/original.jpg", "/static/uploads/colorized.jpg"],
  "session_id": "1234-abcd"
}
```

**Response:**
```json
{
  "status": "success",
  "files_removed": 2
}
```

## Future Enhancements
- Improve model accuracy with better training data
- Add user authentication
- Implement cloud-based storage

## License
This project is open-source and available under the MIT License.

