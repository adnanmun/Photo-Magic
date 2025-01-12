from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
)
import os
import cv2
import numpy as np

# Initialize the Flask app
app = Flask(__name__)

# Set upload and filtered folders
UPLOAD_FOLDER = "uploads"
FILTERED_FOLDER = "filtered"
ADJUSTED_FOLDER = "adjusted"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["FILTERED_FOLDER"] = FILTERED_FOLDER
app.config["ADJUSTED_FOLDER"] = ADJUSTED_FOLDER

# Ensure folders exist
for folder in [UPLOAD_FOLDER, FILTERED_FOLDER, ADJUSTED_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# Helper function to clear specific folders
def clear_folder(folder):
    for file in os.listdir(folder):
        os.remove(os.path.join(folder, file))


# Helper function to get the first file from a folder
def get_first_file(folder):
    files = os.listdir(folder)
    return files[0] if files else None


# Route for the homepage
@app.route("/")
def home():
    image_path = get_first_file(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", image_path=image_path)


# Route to handle image uploads
@app.route("/upload", methods=["POST"])
def upload_file():
    clear_folder(app.config["UPLOAD_FOLDER"])
    clear_folder(app.config["FILTERED_FOLDER"])
    clear_folder(app.config["ADJUSTED_FOLDER"])

    file = request.files.get("file")
    if not file or file.filename == "":
        return "No file selected", 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    return redirect(url_for("home"))


# Route to apply filters
@app.route("/apply_filter/<filter_name>", methods=["POST"])
def apply_filter(filter_name):
    original_filename = get_first_file(app.config["UPLOAD_FOLDER"])
    if not original_filename:
        return jsonify({"error": "No image uploaded"}), 400

    original_img_path = os.path.join(app.config["UPLOAD_FOLDER"], original_filename)
    img = cv2.imread(original_img_path)

    # Apply filter
    filters = {
        "grayscale": lambda img: cv2.cvtColor(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR
        ),
        "sepia": lambda img: np.clip(
            cv2.transform(
                img,
                np.array(
                    [
                        [0.272, 0.534, 0.131],
                        [0.349, 0.686, 0.168],
                        [0.393, 0.769, 0.189],
                    ]
                ),
            ),
            0,
            255,
        ),
        "negative": cv2.bitwise_not,
        "cool": lambda img: cv2.add(img, (20, 15, 0)),
        "warm": lambda img: cv2.add(img, (0, 15, 20)),
    }

    if filter_name in filters:
        img = filters[filter_name](img)
    else:
        return jsonify({"error": "Invalid filter"}), 400

    filtered_path = os.path.join(app.config["FILTERED_FOLDER"], original_filename)
    cv2.imwrite(filtered_path, img)

    return jsonify(
        {
            "filtered_image_url": url_for("filtered_file", filename=original_filename),
            "reset_sliders": True,
        }
    )


# Route to adjust brightness and contrast
@app.route("/adjust_image", methods=["POST"])
def adjust_image():
    filename = get_first_file(app.config["FILTERED_FOLDER"]) or get_first_file(
        app.config["UPLOAD_FOLDER"]
    )
    if not filename:
        return jsonify({"error": "No image to adjust"}), 400

    img_path = os.path.join(
        (
            app.config["FILTERED_FOLDER"]
            if filename in os.listdir(app.config["FILTERED_FOLDER"])
            else app.config["UPLOAD_FOLDER"]
        ),
        filename,
    )
    img = cv2.imread(img_path)

    if img is None:
        return jsonify({"error": "Image could not be loaded"}), 400

    brightness = int(request.form.get("brightness", 0))
    contrast = int(request.form.get("contrast", 0))

    # Apply contrast
    alpha = 1 + (contrast / 100.0)
    img = cv2.convertScaleAbs(img, alpha=alpha)

    # Apply brightness
    img = np.clip(img.astype(np.float32) + brightness, 0, 255).astype(np.uint8)

    adjusted_path = os.path.join(app.config["ADJUSTED_FOLDER"], filename)
    if not cv2.imwrite(adjusted_path, img):
        return jsonify({"error": "Failed to save adjusted image"}), 500

    return jsonify({"adjusted_image_url": url_for("adjusted_file", filename=filename)})


# Route to apply the adjusted image as the new original
@app.route("/apply_changes", methods=["POST"])
def apply_changes():
    filename = get_first_file(app.config["ADJUSTED_FOLDER"]) or get_first_file(
        app.config["FILTERED_FOLDER"]
    )
    if not filename:
        return "No image to apply", 400

    src_path = os.path.join(
        (
            app.config["ADJUSTED_FOLDER"]
            if filename in os.listdir(app.config["ADJUSTED_FOLDER"])
            else app.config["FILTERED_FOLDER"]
        ),
        filename,
    )
    dest_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    os.replace(src_path, dest_path)
    return jsonify({"new_image_url": url_for("uploaded_file", filename=filename)})


# Routes to serve files
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/filtered/<filename>")
def filtered_file(filename):
    return send_from_directory(app.config["FILTERED_FOLDER"], filename)


@app.route("/adjusted/<filename>")
def adjusted_file(filename):
    return send_from_directory(app.config["ADJUSTED_FOLDER"], filename)


# Routes to clear folders
@app.route("/clear_duplicates", methods=["POST"])
def clear_duplicates():
    clear_folder(app.config["FILTERED_FOLDER"])
    clear_folder(app.config["ADJUSTED_FOLDER"])
    return "", 204


@app.route("/clear_images", methods=["POST"])
def clear_images():
    for folder in [UPLOAD_FOLDER, FILTERED_FOLDER, ADJUSTED_FOLDER]:
        clear_folder(folder)
    return "", 204


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
