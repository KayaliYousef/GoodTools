from flask import Flask, render_template, request, redirect, flash, url_for, send_file
from werkzeug.utils import secure_filename
import os
import difflib
import secrets
import helper_functions as hf
import sort
import io
import srt_vtt_converter
import re
import correct_intersected_srt
import sync_srt
import prep_srt
import zipfile

PUNCTUATION_LIST = [".", ",", "?", ":", "!"]
MAX_CHAR_PER_LINE_NORMAL = 42
MIN_CHAR_PER_LINE_NORMAL = 30
MAX_CHAR_PER_LINE_SHORT = 30
MIN_CHAR_PER_LINE_SHORT = 20

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
    try:
        srt_file_path = os.path.join(UPLOAD_FOLDER, "corrected.srt")
        os.remove(srt_file_path)
    except:
        pass
    
    if request.method == "POST":
        file1 = request.files['file1']
        file2 = request.files['file2']

        try:
            file1_name = secure_filename(file1.filename)
            file2_name = secure_filename(file2.filename)

            file1_extension = file1_name.rsplit(".", 1)[-1]
            file2_extension = file2_name.rsplit(".", 1)[-1]
            
            if file1_extension.lower() != file2_extension.lower():
                flash('Both files must have the same extension', 'warning')
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

            else:
                flash("Only .srt, .txt and .csv file formats are supported", "warning")
                # Clean up uploaded files
                os.remove(file1_path)
                os.remove(file2_path)
                return redirect(request.url)

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

    try:
        srt_file_path = os.path.join(UPLOAD_FOLDER, "corrected.srt")
        os.remove(srt_file_path)
    except:
        pass

    if request.method == "POST":
        app.logger.info("POST request detected")
        srt_file = request.files['srt-file']
        app.logger.info("Pulled the uploaded file")
        try:
            srt_file_name = secure_filename(srt_file.filename)
            app.logger.info("Secured file name")
            srt_file_extension = srt_file_name.rsplit(".", 1)[-1]

            if srt_file_extension.lower() != "srt" and srt_file_extension.lower() != "vtt":
                flash('The uploaded file type is not supported. Please upload .srt or .vtt files only', 'warning')
                return redirect(request.url)
            
            srt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_file_name).replace("\\", "/")
            app.logger.info("Created file path")
            srt_file.save(srt_file_path)
            app.logger.info("File was successfully uploaded")

            if 'action' in request.form:

                if request.form['action'] == 'sort':
                    app.logger.info("Sort button pressed")
                    if srt_file_extension.lower() == "srt":
                        sort.sort(srt_file_path)
                        output_extension = "_sorted.srt"
                    
                    else:
                        flash('Only SRT file format is accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)

                elif request.form['action'] == 'convert-srt-vtt':
                    app.logger.info("Convert SRT/VTT button pressed")
                    if srt_file_extension.lower() == "srt":
                        srt_vtt_converter.convert_srt_to_vtt(srt_file_path)
                        output_extension = ".vtt"

                    elif srt_file_extension.lower() == "vtt":
                        srt_vtt_converter.convert_vtt_to_srt(srt_file_path)
                        output_extension = ".srt"  

                    else:
                        flash('Only SRT/VTT file formats are accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)

                elif request.form['action'] == "clean-srt":
                    app.logger.info("Clean SRT button pressed")
                    if srt_file_extension.lower() == "srt":
                        hf.srt_to_plaintext(srt_file_path)
                        output_extension = ".txt" 

                    else:
                        flash('Only SRT file format is accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)

                elif request.form['action'] == "check-srt-sequence":
                    app.logger.info("Check SRT sequence button pressed")
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
                                flash("Timing error within the same block", "header")
                                for error in error_within_one_block:
                                    flash(f"{error}", "body")

                            if error_between_two_blocks:
                                flash("Timing error between two blocks", "header")
                                for error in error_between_two_blocks:
                                    flash(f"{error}", "body")
                                flash("Corrected intersection between timeblocks", "header")
                                correct_intersected_srt.correct_intersected_blocks(srt_file_path)

                            if block_index_errors:
                                for error in block_index_errors:
                                    flash(f"Block Index {error} is wrong or missing", "header")

                            if white_space_in_block_index_error:
                                if len(white_space_in_block_index_error) == 1:
                                    flash(f"Extra white space at Block Index {white_space_in_block_index_error[0]}", "header")
                                else:
                                    flash("Extra white spaces at Block Indices:", "header")
                                    flash(f"{','.join(white_space_in_block_index_error)}", "body")
                                hf.clean_extra_white_spaces(srt_file_path)
                                flash("Cleaned white spaces from SRT file", "header")

                            if empty_row_errors:
                                flash("Empty/Extra row error", "header")
                                for error in empty_row_errors:
                                    flash(f"{error}", "body")

                            if block_format_error:
                                flash("Timecode format error", "header")
                                for error in block_format_error:
                                    flash(f"{error}", "body")

                            if error_between_two_blocks or white_space_in_block_index_error:
                                os.rename(srt_file_path, os.path.join(srt_file_path.rsplit("/", 1)[0], "corrected.srt"))
                                return redirect(url_for("download_page"))
                            else:
                                os.remove(srt_file_path)
                                return redirect(request.url)

                        else:
                            flash("No errors were found", "success")
                            os.remove(srt_file_path)
                            return redirect(request.url)
                            
                    else:
                        flash('Only SRT file format is accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)
                    
                elif request.form['action'] == "sync":
                    app.logger.info("Sync button pressed")
                    if srt_file_extension.lower() == "srt":
                        app.logger.info("File type was validated")
                        punctuations = PUNCTUATION_LIST
                        if request.form.get("split-at-punctuation"):
                            split_at_punctuation = True
                        else:
                            split_at_punctuation = False

                        if request.form['sync-option'] == "Normal":
                            app.logger.info("Sync-option 'Normal' was chosen")
                            max_char_per_line = MAX_CHAR_PER_LINE_NORMAL
                            min_char_per_line = MIN_CHAR_PER_LINE_NORMAL
            
                        elif request.form['sync-option'] == "Short":
                            app.logger.info("Sync-option 'Short' was chosen")
                            max_char_per_line = MAX_CHAR_PER_LINE_SHORT
                            min_char_per_line = MIN_CHAR_PER_LINE_SHORT
                        else:
                            app.logger.info("Sync-option 'Custom' was chosen")
                            max_char_per_line = int(request.form.get("max-input"))
                            min_char_per_line = int(request.form.get("min-input"))
                            if min_char_per_line > max_char_per_line:
                                min_char_per_line, max_char_per_line = max_char_per_line, min_char_per_line
                        sort.sort(srt_file_path, edit_original_file=True)
                        app.logger.info("File was Sorted successfully")
                        hf.clean_extra_white_spaces(srt_file_path)
                        app.logger.info("Whitespaces were successfully removed")
                        correct_intersected_srt.correct_intersected_blocks(srt_file_path)
                        app.logger.info("Intersected translation blocks were corrected successfully")
                        sync_srt.sync(srt_file_path, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations, srt_file_path)
                        app.logger.info("File was successfully synchronized")
                        output_extension = ".srt"

                    else:
                        flash('Only SRT file format is accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)

                
                # This file is being created by other functions like (sort, convert between srt/vtt and clean)
                tempfile_path = srt_file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0] + output_extension
                # Read file into memory
                with open(os.path.join(UPLOAD_FOLDER, tempfile_path), "rb") as f:
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


@app.route('/download')
def download_page():
    return render_template("download.html")

@app.route("/download/file")
def download_file():
    # Read file into memory
    srt_file_path = os.path.join(UPLOAD_FOLDER, "corrected.srt")
    with open(srt_file_path, "rb") as f:
        file_bytes = io.BytesIO(f.read())

    os.remove(srt_file_path)

    return send_file(
        file_bytes,
        as_attachment=True,
        download_name="corrected.srt",
        mimetype='text/plain'
    )

@app.route('/srt_prep', methods=['GET', 'POST'])
def srt_prep():
    try:
        srt_file_path = os.path.join(UPLOAD_FOLDER, "corrected.srt")
        os.remove(srt_file_path)
    except:
        pass

    if request.method == "POST":
        try:
            if "action" in request.form:

                if request.form["action"] == "prep-srt":
                    srt_file = request.files['srt-file']
                    srt_file_name = secure_filename(srt_file.filename)
                    srt_file_extension = srt_file_name.rsplit(".", 1)[-1]
                    srt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], srt_file_name)
                    srt_file.save(srt_file_path)

                    if srt_file_extension.lower() == "srt":
                        hf.sub_srt_codes(srt_file_path, save_output_where_input_is_located=True)
                        prep_srt.srt_to_json(srt_file_path)

                        text_file_path = srt_file_path.rsplit(".", 1)[0] + ".txt"
                        json_file_path = srt_file_path.rsplit(".", 1)[0] + "_output.json"

                        # Create an in-memory ZIP file
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            # Add text file
                            with open(text_file_path, "rb") as f:
                                zf.writestr("output.txt", f.read())
                            
                            # Add json file
                            with open(json_file_path, "rb") as f:
                                zf.writestr("output.json", f.read())

                        # Go back to the beginning of the BytesIO buffer
                        zip_buffer.seek(0)

                        try:
                            os.remove(srt_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting srt file {srt_file_path}: {e}")
                        
                        try:
                            os.remove(text_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting text file {text_file_path}: {e}")

                        try:
                            os.remove(json_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting json file {json_file_path}: {e}")

                        # Send zip file to client
                        return send_file(
                            zip_buffer,
                            as_attachment=True,
                            download_name="files.zip",
                            mimetype="application/zip"
                        )

                    else:
                        flash('Only SRT file format is accepted', 'warning')
                        os.remove(srt_file_path)
                        return redirect(request.url)

                else:

                    punctuations = PUNCTUATION_LIST
                    if request.form.get("split-at-punctuation"):
                        split_at_punctuation = True
                    else:
                        split_at_punctuation = False

                    if request.form['sync-option'] == "Normal":
                        app.logger.info("Sync-option 'Normal' was chosen")
                        max_char_per_line = MAX_CHAR_PER_LINE_NORMAL
                        min_char_per_line = MIN_CHAR_PER_LINE_NORMAL
        
                    elif request.form['sync-option'] == "Short":
                        app.logger.info("Sync-option 'Short' was chosen")
                        max_char_per_line = MAX_CHAR_PER_LINE_SHORT
                        min_char_per_line = MIN_CHAR_PER_LINE_SHORT
                    else:
                        app.logger.info("Sync-option 'Custom' was chosen")
                        max_char_per_line = int(request.form.get("max-input"))
                        min_char_per_line = int(request.form.get("min-input"))
                        if min_char_per_line > max_char_per_line:
                            min_char_per_line, max_char_per_line = max_char_per_line, min_char_per_line

                    json_file = request.files['json-file']
                    json_file_name = secure_filename(json_file.filename)
                    json_file_extension = json_file_name.rsplit(".", 1)[-1]
                    json_file_path = os.path.join(app.config['UPLOAD_FOLDER'], json_file_name)
                    json_file.save(json_file_path)

                    text_file = request.files['text-file']
                    text_file_name = secure_filename(text_file.filename)
                    text_file_extension = text_file_name.rsplit(".", 1)[-1]
                    text_file_path = os.path.join(app.config['UPLOAD_FOLDER'], text_file_name)
                    text_file.save(text_file_path)

                    if json_file_extension.lower() == "json" and text_file_extension.lower() == "txt":
                        prep_srt.reconstruct_srt_from_json_and_txt(json_file_path, text_file_path)

                        reconstructed_file_path = text_file_path.rsplit(".", 1)[0]+"_new.srt"
                        sync_srt.sync(reconstructed_file_path, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations, reconstructed_file_path)

                        with open(reconstructed_file_path, "rb") as f:
                            file_bytes = io.BytesIO(f.read())

                        try:
                            os.remove(json_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting json file {json_file_path}: {e}")

                        try:
                            os.remove(text_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting text file {text_file_path}: {e}")

                        try:
                            os.remove(reconstructed_file_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting reconstructed srt file {reconstructed_file_path}: {e}")

                        # Send file for download
                        return send_file(
                            file_bytes,
                            as_attachment=True,
                            download_name=f'output.srt',
                            mimetype='text/plain'
                        )
                    
                    else:
                        flash("The uploaded file formats are not correct please upload the json and txt files", "warning")
                        os.remove(json_file_path)
                        os.remove(text_file_path)
                        return redirect(request.url)


        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)

        
    return render_template('srt_prep.html')

if __name__ == '__main__':
    app.run(debug=True)