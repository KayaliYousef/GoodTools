from flask import Flask, render_template, request, redirect, flash, url_for, send_file, stream_with_context, after_this_request
from werkzeug.utils import secure_filename
import os
import difflib
import secrets
import helper_functions as hf
import tempfile
import sort
import io
import srt_vtt_converter
import re
import correct_intersected_srt

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
            
            if file1_extension.lower() != file2_extension.lower():
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

@app.route('/process_srt', methods=['GET', 'POST'])
def process_srt():

    if request.method == "POST":
        srt_file = request.files['srt-file']
        try:
            srt_file_name = secure_filename(srt_file.filename)

            srt_file_extension = srt_file_name.rsplit(".", 1)[-1]

            if srt_file_extension.lower() != "srt" and srt_file_extension.lower() != "vtt":
                flash('The uploaded file type is not supported. Please upload .srt or .vtt files only', 'info')
                return redirect(request.url)
            
            srt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_file_name)
            srt_file.save(srt_file_path)

            if 'action' in request.form:

                if request.form['action'] == 'sort':

                    if srt_file_extension.lower() == "srt":
                        sort.sort(srt_file_path)
                        output_extension = "_sorted.srt"
                    
                    else:
                        flash('This function only accepts SRT files', 'info')

                elif request.form['action'] == 'convert-srt-vtt':

                    if srt_file_extension.lower() == "srt":
                        srt_vtt_converter.convert_srt_to_vtt(srt_file_path)
                        output_extension = ".vtt"

                    elif srt_file_extension.lower() == "vtt":
                        srt_vtt_converter.convert_vtt_to_srt(srt_file_path)
                        output_extension = ".srt"  

                    else:
                        flash('This function only accepts SRT or VTT files', 'info')

                elif request.form['action'] == "clean-srt":

                    if srt_file_extension.lower() == "srt":
                        hf.srt_to_plaintext(srt_file_path)
                        output_extension = ".txt" 

                    else:
                        flash('This function only accepts SRT files', 'info')

                elif request.form['action'] == "check-srt-sequence":

                    if srt_file_extension.lower() == "srt":
                        error_within_one_block = []
                        error_between_two_blocks = []
                        block_index_errors = []
                        white_space_in_block_index_error = []
                        empty_row_errors = []
                        block_format_error = []

                        with open(srt_file_path, "r", encoding='utf-8') as srt_file:
                            # Read the contents of the file
                            srt_contents = srt_file.read()
                            srt_contents_lines = srt_contents.split("\n")


                        # timestamp pattern
                        pattern = r"\d+.*\d+.*\d+.*\d+.*\d+.*\d+.*\d+.*\d+"
                        # find all timestamps
                        srt_timecodes = re.findall(pattern, srt_contents)

                        # Find errors in timecodes
                        # Errors within the same timecode
                        for line in srt_timecodes:
                            if len(line.strip()) != 29:
                                block_format_error.append(line)
                                continue
                            try:
                                start, end = hf.convert_timecode_to_millisec(line)
                                if start > end:
                                    error_within_one_block.append(line)
                            except:
                                block_format_error.append(line)

                        # Errors between two timecodes
                        for i in range(len(srt_timecodes) - 1):
                            try:
                                _, current_block_end = hf.convert_timecode_to_millisec(srt_timecodes[i])
                            except:
                                if not srt_timecodes[i] in block_format_error:
                                    block_format_error.append(srt_timecodes[i])
                                continue
                            try:
                                next_block_start, _ = hf.convert_timecode_to_millisec(srt_timecodes[i + 1])
                            except:
                                if not srt_timecodes[i + 1] in block_format_error:
                                    block_format_error.append(srt_timecodes[i + 1])
                                continue
                            if current_block_end > next_block_start:
                                error_between_two_blocks.append(srt_timecodes[i].strip())
                                error_between_two_blocks.append(srt_timecodes[i + 1].strip())

                        block_index = 0
                        block_index_indexes = []
                            
                        # Find errors in Block indexes
                        for i, line in enumerate(srt_contents_lines):
                            if line.strip().isdigit():
                                block_index_indexes.append(i)
                                block_index += 1
                                if int(line.strip()) != block_index:
                                    block_index_errors.append(block_index)
                                if any(char == ' ' for char in line):
                                    white_space_in_block_index_error.append(block_index)

                        # Find errors in empty rows
                        for i in block_index_indexes:
                            if i == 0:
                                continue
                            if srt_contents_lines[i-1] != "\n" and srt_contents_lines[i-1] != '':
                                empty_row_errors.append(f"Missing empty row at line {i}")
                            if srt_contents_lines[i-2] == "\n" or srt_contents_lines[i-2] == '':
                                empty_row_errors.append(f"Extra row at line {i}")
                            if srt_contents_lines[i+1] == "\n" or srt_contents_lines[i+1] == '':
                                empty_row_errors.append(f"Extra row at line {i+2}")
                            if srt_contents_lines[i+2] == "\n" or srt_contents_lines[i+2] == '':
                                empty_row_errors.append(f"Extra row at line {i+3}")


                        if error_within_one_block or error_between_two_blocks or block_index_errors or white_space_in_block_index_error or empty_row_errors or block_format_error:
                            
                            if error_within_one_block:
                                flash("Timing error within the same block")
                                for error in error_within_one_block:
                                    flash(f"{error}", "info")

                            if error_between_two_blocks:
                                flash("Timing error between two blocks")
                                for error in error_between_two_blocks:
                                    flash(f"{error}", "info")
                                correct_intersected_srt.correct_intersected_blocks(srt_file_path)
                                flash("Corrected intersection between timeblocks")

                            if block_index_errors:
                                for error in block_index_errors:
                                    flash(f"Block Index {error} is wrong or missing", "info")

                            if white_space_in_block_index_error:
                                if len(white_space_in_block_index_error) == 1:
                                    flash(f"Extra white space at Block Index {white_space_in_block_index_error[0]}</font>")
                                else:
                                    flash(f"Extra white spaces at Block Indices: {','.join(white_space_in_block_index_error)}", "info")
                                hf.clean_extra_white_spaces(srt_file_path)
                                flash("Cleaned white spaces from SRT file")

                            if empty_row_errors:
                                flash("Empty/Extra row error")
                                for error in empty_row_errors:
                                    flash(f"{error}", "info")

                            if block_format_error:
                                flash("Timecode format error")
                                for error in block_format_error:
                                    flash(f"{error}", "info")

                            if error_between_two_blocks or white_space_in_block_index_error:
                                output_extension = ".srt"
                            else:
                                os.remove(srt_file_path)
                                return redirect(request.url)

                        else:
                            flash("No errors were found", "info")
                            os.remove(srt_file_path)
                            return redirect(request.url)
                            
                    else:
                        flash('This function only accepts SRT files', 'info')
                    
                elif request.form['action'] == "sync":
                    if srt_file_extension.lower() == "srt":

                        if request.form['sync-option'] == "Normal":
                            print("First Case")
                        elif request.form['sync-option'] == "Short":
                            print("Second case")
                        else:
                            print("Third case")
                            print(request.form.get("min-input"))
                            print(request.form.get("max-input"))
                        os.remove(srt_file_path)
                        return redirect(request.url)

                


                # This file is being created by other functions like (sort, convert between srt/vtt and clean)
                tempfile_path = srt_file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0] + output_extension
                print(tempfile_path)
                # Read file into memory
                with open(tempfile_path, "rb") as f:
                    file_bytes = io.BytesIO(f.read())

                os.remove(srt_file_path)
                # Delete immediately since file content is in memory
                try:
                    os.remove(tempfile_path)
                except Exception as e:
                    app.logger.error(f"Error deleting temp file {tempfile_path}: {e}")

                # Send file for download
                return send_file(
                    file_bytes,
                    as_attachment=True,
                    download_name=f'output{output_extension}',
                    mimetype='text/plain'
                )
                        
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
        
    return render_template('process_srt.html')

@app.route('/srt_prep')
def srt_prep():
    return render_template('srt_prep.html')

if __name__ == '__main__':
    app.run(debug=True)