from flask import Flask, render_template, request, Response
import os
import base64
from openai import OpenAI
import io

# Initialize Flask App
app = Flask(__name__, template_folder='../templates')
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'flac'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET'])
def home():
    # Assuming an index.html file under templates folder
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    api_key = request.form['api_key']
    if file and allowed_file(file.filename):
        output_srt_content = transcribe_audio(file, api_key)
        if output_srt_content:
            base64_data = base64.b64encode(
                output_srt_content.encode()).decode('utf-8')
            download_link = f"data:text/plain;base64,{base64_data}"
            return f"Transcription successful!<br><a href='{download_link}' download='transcript.srt'>Download SRT File</a>"
        else:
            return "Transcription failed."
    else:
        return "Invalid file type."


def transcribe_audio(audio_file, api_key):
    try:
        client = OpenAI(api_key=api_key)
        audio_file.seek(0)  # Reset file pointer
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language='en',
            response_format='srt'
        )
        transcript = response["choices"][0]["text"] if response["choices"] else ''
        return transcript
    except Exception as e:
        print(f"An error occurred during transcription: {str(e)}")
        return None


@app.route('/about')
def about():
    return "This application demonstrates audio transcription using the OpenAI API."


if __name__ == "__main__":
    app.run(debug=True)
