from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
from openai import OpenAI
import os
import base64

# Initialize Flask App
app = Flask(__name__, template_folder='../templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac'}

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Checks if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def encode_file_to_base64(filepath):
    """Encodes a file to Base64."""
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')


@app.route('/')
def home():
    """Displays the homepage."""
    return 'Welcome! This is a Flask application for audio transcription.</br><a href="/upload">heres to transcribe your sound.</a>'


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        api_key = request.form['api_key']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            output_srt_path = os.path.join(
                app.config['UPLOAD_FOLDER'], os.path.splitext(filename)[0] + ".srt")

            transcribe_status = transcribe_audio(
                file_path, output_srt_path, api_key)
            if os.path.exists(output_srt_path):
                base64_data = encode_file_to_base64(output_srt_path)
                download_link = f"data:text/plain;base64,{base64_data}"
                return (f"{transcribe_status}<br>"
                        f"<a href='{download_link}' download='{os.path.splitext(filename)[0]}.srt'>Download SRT File</a>")
            else:
                return "Transcription failed. Output file not found."
        else:
            return "Invalid file type."
    return render_template('upload.html')


def encode_file_to_base64(filepath):
    """ Encodes a file to Base64. """
    with open(filepath, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
    return encoded_string


def transcribe_audio(input_audio_path, output_srt_path, api_key, language='en', response_format='srt'):
    """Transcribes audio using OpenAI API and saves to an .srt file."""
    try:
        client = OpenAI(api_key=api_key)
        with open(input_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format
            )
        if transcript:
            with open(output_srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(transcript)
            return "Transcription successful!"
        return "Transcription completed but no content was returned."
    except Exception as e:
        return f"An error occurred during transcription: {str(e)}"


@app.route('/download_base64/<filename>')
def download_base64(filename):
    """Returns a base64 encoded string of the file for download."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return "File not found.", 404

    try:
        with open(file_path, "rb") as file:
            file_content = base64.b64encode(file.read()).decode('utf-8')
        return file_content
    except Exception as e:
        return f"Failed to process the file: {str(e)}", 500


@app.route('/about')
def about():
    """Provides information about the application."""
    return 'This application demonstrates audio transcription using the OpenAI API.'


if __name__ == "__main__":
    app.run(debug=True)
