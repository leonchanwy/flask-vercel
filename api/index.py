from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
import os
import base64
from openai import OpenAI

# Initialize Flask App
app = Flask(__name__, template_folder='../templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')


def transcribe_audio(input_audio_path, output_srt_path, api_key, language='en', response_format='srt'):
    try:
        client = OpenAI(api_key=api_key)
        with open(input_audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format
            )
            transcript = response["result"]

        with open(output_srt_path, 'w', encoding='utf-8') as srt_file:
            srt_file.write(transcript)

        return "Transcription successful!"
    except Exception as e:
        return f"An error occurred during transcription: {str(e)}"


@app.route('/')
def home():
    return 'Welcome! This is a Flask application for audio transcription.</br><a href="/upload">Click here to transcribe your audio file.</a>'


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
                return (f"{transcribe_status}<br><a href='{download_link}' download='{os.path.splitext(filename)[0]}.srt'>Download SRT File</a>")
            else:
                return "Transcription failed. Output file not found."
        else:
            return "Invalid file type."
    return render_template('upload.html')


@app.route('/about')
def about():
    return 'This application demonstrates audio transcription using the OpenAI API.'


if __name__ == "__main__":
    app.run(debug=True)
