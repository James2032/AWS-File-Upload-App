
import boto3
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from markupsafe import escape

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

s3 = boto3.client("s3", region_name="us-east-1")
bucket_name = "jamshed-file-upload-app"
folder = "project-uploads/"

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        file = request.files.get("file")

        if file and file.filename:
            filename = secure_filename(file.filename)

            if filename:
                try:
                    s3.upload_fileobj(file, bucket_name, folder + filename)
                    message = f"{filename} uploaded successfully!"
                except Exception:
                    app.logger.exception("Upload failed")
                    message = "Upload failed."
        else:
            message = "Please select a file."

    files_html = ""

    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=folder
        )

        for obj in response.get("Contents", []):
            filename = obj["Key"].removeprefix(folder)

            if filename:
                files_html += f"""
                <li>
                    {escape(filename)}
                    <form action="/delete" method="POST"
                          style="display:inline;">
                        <input type="hidden" name="filename"
                               value="{escape(filename)}">
                        <button type="submit">Delete</button>
                    </form>
                </li>
                """

    except Exception:
        app.logger.exception("Could not list files")
        files_html = "<li>Could not load files.</li>"

    return f"""
    <h1>My AWS File Upload Website</h1>

    <p>Select a file to upload:</p>

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Upload to S3</button>
    </form>

    <p>{escape(message)}</p>

    <h2>Uploaded Files</h2>
    <ul>{files_html}</ul>
    """

@app.route("/delete", methods=["POST"])
def delete_file():
    filename = request.form.get("filename", "")

    if not filename or secure_filename(filename) != filename:
        return "Invalid filename", 400

    try:
        s3.delete_object(
            Bucket=bucket_name,
            Key=folder + filename
        )
    except Exception:
        app.logger.exception("Delete failed")
        return "Could not delete file", 500

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)

