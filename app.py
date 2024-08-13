from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def adjust_brightness_contrast(image, brightness=0, contrast=0):
    brightness = int((brightness - 50) * 2.55)
    contrast = int((contrast - 50) * 2.55)

    if brightness != 0:
        shadow = brightness if brightness > 0 else 0
        highlight = 255 if brightness > 0 else 255 + brightness
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow
        image = cv2.addWeighted(image, alpha_b, image, 0, gamma_b)

    if contrast != 0:
        alpha_c = 1.0 + contrast / 127.0
        gamma_c = -128.0 * alpha_c + 128.0
        image = cv2.addWeighted(image, alpha_c, image, 0, gamma_c)

    return image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        _, buffer = cv2.imencode('.jpg', image)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'image': encoded_image})
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/adjust', methods=['POST'])
def adjust():
    try:
        data = request.get_json()
        img_data = base64.b64decode(data['image'])
        image = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        brightness = int(data['brightness'])
        contrast = int(data['contrast'])
        adjusted_image = adjust_brightness_contrast(image, brightness, contrast)
        _, buffer = cv2.imencode('.jpg', adjusted_image)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'image': encoded_image})
    except Exception as e:
        logging.error(f"Error during adjustment: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
