from flask import Flask, render_template, request, redirect, flash, url_for, send_file, stream_with_context
from werkzeug.utils import secure_filename
import os
import difflib
import secrets
import helper_functions as hf
import tempfile

app = Flask(__name__)

# Generate a secure random secret key
app.secret_key = secrets.token_hex(16)  # 32-character hexadecimal string

UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return redirect(url_for('compare'))

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    if request.method == "POST":
        file1 = request.files['file1']
        file2 = request.files['file2']

        try:
            file1_name = secure_filename(file1.filename)
            file2_name = secure_filename(file2.filename)

            file1_extension = file1_name.rsplit(".", 1)[-1]
            file2_extension = file2_name.rsplit(".", 1)[-1]
            
            if file1_extension != file2_extension:
                flash('Both files must have the same extension', 'info')
                return redirect(request.url)

            file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1_name)
            file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2_name)

            file1.save(file1_path)
            file2.save(file2_path)

            if file1_extension.lower() == 'srt':
                lines1 = hf.clean_srt(file1_path).splitlines()
                lines2 = hf.clean_srt(file2_path).splitlines()
                diff_html = difflib.HtmlDiff().make_file(lines1, lines2)

            elif file1_extension.lower() == "txt" or file1_extension.lower() == "csv":
                with open(file1_path, "r", encoding="utf-8") as f:
                    lines1 = f.readlines()
                with open(file2_path, "r", encoding="utf-8") as f:
                    lines2 = f.readlines()
                diff_html = difflib.HtmlDiff().make_file(lines1, lines2)

            # Clean up uploaded files
            os.remove(file1_path)
            os.remove(file2_path)

            # Render template with diff content
            return render_template('diff_result.html', diff_content=diff_html)

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))

    return render_template('compare.html')

@app.route('/process_srt')
def process_srt():
    return render_template('process_srt.html')

@app.route('/srt_prep')
def srt_prep():
    return render_template('srt_prep.html')

if __name__ == '__main__':
    app.run(debug=True)