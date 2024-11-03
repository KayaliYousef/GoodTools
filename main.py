import difflib
import glob
import os
import re
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTextEdit, QRadioButton, QFileDialog, QCheckBox
from PyQt5.QtGui import QIcon, QTextCursor

import convention_validator as cv
import sort
import srt_vtt_converter
import prep_srt
import correct_intersected_srt
import helper_functions

VERSION = "1.5.3"

class UI(QMainWindow):
  # constructor
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi('assets/good_tools.ui', self)

        self.setWindowIcon(QIcon('assets/palmtree.png'))
        self.setWindowTitle(f"GoodTools {VERSION}")

        # Define Widgets
        # Labels
        # Check Boxes
        self.srtPrepDeleteJsonCheckBox = self.findChild(QCheckBox, "srtPrepDeleteJsonCheckBox")
        self.srtPrepDeleteTxtCheckBox = self.findChild(QCheckBox, "srtPrepDeleteTxtCheckBox")
        # Radio Buttons
        self.srtRadioButton = self.findChild(QRadioButton, "srtRadioButton")
        self.txtRadioButton = self.findChild(QRadioButton, "txtRadioButton")
        self.csvRadioButton = self.findChild(QRadioButton, "csvRadioButton")
        # Push Buttons
        self.comparePushButton = self.findChild(QPushButton, "comparePushButton")
        self.sortPushButton = self. findChild(QPushButton, "sortPushButton")
        self.convertPushButton = self.findChild(QPushButton, "convertPushButton")
        self.cleanPushButton =self.findChild(QPushButton, "cleanPushButton")
        self.validatePushButton = self.findChild(QPushButton, "validatePushButton")
        self.checkSequencePushButton = self.findChild(QPushButton, "checkSequencePushButton")
        self.prepSrtPushButton = self.findChild(QPushButton, "prepSrtPushButton")
        self.reConstructSrtPushButton = self.findChild(QPushButton, "reConstructSrtPushButton")
        self.fileDialog1 = self.findChild(QPushButton, "fileDialog1")    
        self.fileDialog2 = self.findChild(QPushButton, "fileDialog2")
        self.srtPrepLoadSrtfileDialog = self.findChild(QPushButton, "srtPrepLoadSrtfileDialog")
        self.srtPrepLoadJsonfileDialog = self.findChild(QPushButton, "srtPrepLoadJsonfileDialog")
        self.srtPrepLoadTxtfileDialog = self.findChild(QPushButton, "srtPrepLoadTxtfileDialog")
        # Entries
        self.firstFileName = self.findChild(QTextEdit, "firstFile")
        self.secondFileName = self.findChild(QTextEdit, "secondFile")
        self.validateFeedbackTextEdit = self.findChild(QTextEdit, "validateFeedbackTextEdit")
        self.checkSequenceFeedbackTextEdit = self.findChild(QTextEdit, "checkSequenceFeedbackTextEdit")
        self.srtPrepLoadSrtTextEdit = self.findChild(QTextEdit, "srtPrepLoadSrtTextEdit")
        self.srtPrepLoadJsonTextEdit = self.findChild(QTextEdit, "srtPrepLoadJsonTextEdit")
        self.srtPrepLoadTxtTextEdit = self.findChild(QTextEdit, "srtPrepLoadTxtTextEdit")
        self.srtPrepFeedbackTextEdit = self.findChild(QTextEdit, "srtPrepFeedbackTextEdit")
        # Connect Buttons
        self.comparePushButton.clicked.connect(self.compare)
        self.sortPushButton.clicked.connect(self.sort_srt)
        self.convertPushButton.clicked.connect(self.convert)
        self.cleanPushButton.clicked.connect(self.clean)
        self.validatePushButton.clicked.connect(self.validate_srt)
        self.checkSequencePushButton.clicked.connect(self.check_timecode_sequence)
        self.fileDialog1.clicked.connect(self.browse1)
        self.fileDialog2.clicked.connect(self.browse2)
        self.srtPrepLoadSrtfileDialog.clicked.connect(self.browse_load_srt_to_prep)
        self.srtPrepLoadJsonfileDialog.clicked.connect(self.browse_load_json_to_reconstruct_srt)
        self.srtPrepLoadTxtfileDialog.clicked.connect(self.browse_load_txt_to_reconstruct_srt)
        self.prepSrtPushButton.clicked.connect(self.prepare_srt_for_deepl)
        self.reConstructSrtPushButton.clicked.connect(self.reconstruct_srt_from_json)

    def browse1(self):
        self.firstFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt *.srt)")
        self.firstFileName.setText(fname[0])
    def browse2(self):
        self.secondFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt *.srt)")
        self.secondFileName.setText(fname[0])
    def browse_load_srt_to_prep(self):
        self.srtPrepLoadSrtTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.srt)")
        self.srtPrepLoadSrtTextEdit.setText(fname[0])
    def browse_load_json_to_reconstruct_srt(self):
        self.srtPrepLoadJsonTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.json)")
        self.srtPrepLoadJsonTextEdit.setText(fname[0])
    def browse_load_txt_to_reconstruct_srt(self):
        self.srtPrepLoadTxtTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt)")
        self.srtPrepLoadTxtTextEdit.setText(fname[0])


    """Compare Tab"""
    # function to compare two files (srt or txt) and output the difference in an html file
    def compare(self):
        fname1 = self.firstFileName.toPlainText().replace("file:///", "").replace("\\", "/")
        fname2 = self.secondFileName.toPlainText().replace("file:///", "").replace("\\", "/")
        if self.srtRadioButton.isChecked():
            text1 = helper_functions.clean_srt(fname1)
            text2 = helper_functions.clean_srt(fname2)
            # Split the texts into lines
            lines1 = text1.splitlines()
            lines2 = text2.splitlines()
            html_diff = difflib.HtmlDiff().make_file(lines1, lines2)
            # Make output file name
            outputName = fname1.replace(".srt", "").replace("\\", "/").split("/")
            outputName = outputName[-1]
            # Write the HTML diff to a file
            with open(outputName+'.html', 'w', encoding="utf-8") as f:
                f.write(html_diff)

        elif self.txtRadioButton.isChecked():
            text1 = self.read_txt(fname1)
            text2 = self.read_txt(fname2)
            # Split the texts into lines
            lines1 = text1.splitlines()
            lines2 = text2.splitlines()
            html_diff = difflib.HtmlDiff().make_file(lines1, lines2)
            # Make output file name
            outputName = fname1.replace(".txt", "").replace("\\", "/").split("/")
            outputName = outputName[-1]
            # Write the HTML diff to a file
            with open(outputName+'.html', 'w', encoding="utf-8") as f:
                f.write(html_diff)

        elif self.csvRadioButton.isChecked():
            lines1 = self.read_csv(fname1)
            lines2 = self.read_csv(fname2)
            html_diff = difflib.HtmlDiff().make_file(lines1, lines2)
            # Make output file name
            outputName = fname1.replace(".csv", "").replace("\\", "/").split("/")
            outputName = outputName[-1]
            # Write the HTML diff to a file
            with open(outputName+'.html', 'w', encoding="utf-8") as f:
                f.write(html_diff)

    def read_txt(self, txt_file_path:str) -> str:
        path = re.sub(r"\\", "/", txt_file_path)
        with open(path, "r", encoding="utf-8") as txt_file:
            txt = txt_file.read()
        return txt
    
    def read_csv(self, csv_file_path:str) -> list[str]:
        path = re.sub(r"\\", "/", csv_file_path)
        with open(path, "r", encoding="utf-8") as csv_file:
            lines = csv_file.readlines()
            return lines
    
    """Sort Tab"""
    def sort_srt(self):
        files = sort.get_files()
        sort.sort(files)

    """Convert Tab"""
    # function to convert files between srt and vtt
    def convert(self):
        srt_files = helper_functions.get_files("srt")
        vtt_files = helper_functions.get_files("vtt")
        for file in srt_files:
            srt_vtt_converter.convert_srt_to_vtt(file)
        for file in vtt_files:
            srt_vtt_converter.convert_vtt_to_srt(file)

    """Clean Tab"""
    def clean(self):
        srt_files = helper_functions.get_files("srt")
        for file in srt_files:
            helper_functions.srt_to_plaintext(file)

    """Validate Tab"""
    def validate_srt(self) -> str:
        srt_files = helper_functions.get_files("srt")
        if not len(srt_files):
            self.validateFeedbackTextEdit.setPlainText("No Files Found")
            return

        unvalid_files = []
        for file in srt_files:
            text = cv.clean_srt(file)

            brackets_count_valid = cv.validate_brackets_count(text)
            no_missing_round_brackets = cv.find_missing_round_brackets(text)
            no_missing_square_brackets = cv.find_missing_square_brackets(text)
            no_missing_curly_brackets = cv.find_missing_curly_brackets(text)
            dot_space_after_bracket_valid = cv.validate_dot_space_after_round_bracket(text)
            before_square_brackets_valid = cv.validate_before_square_brackets(text)
            before_curly_brackets_valid = cv.validate_before_curly_brackets(text)
            inside_square_brackets = cv.validate_inside_square_brackets(text)

            if brackets_count_valid and dot_space_after_bracket_valid and before_square_brackets_valid and before_curly_brackets_valid and no_missing_round_brackets and no_missing_square_brackets and no_missing_curly_brackets and inside_square_brackets:
                pass

            else: 
                unvalid_files.append(file)

        if not unvalid_files:
            self.validateFeedbackTextEdit.setHtml("<font color='green'>All Files are Valid</font>")
        else:
            self.validateFeedbackTextEdit.setHtml("<font color='red'>Following files are not Valid</font>")
            for file in unvalid_files:
                temp_text = self.validateFeedbackTextEdit.toHtml()
                temp_text = f"{temp_text}{file}"
                self.validateFeedbackTextEdit.setHtml(temp_text)

    """Check Sequence Tab"""
    def clean_extra_white_spaces(self, srt_file:str):
        lines = []
        with open(srt_file, "r", encoding='utf-8') as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines]
        with open(srt_file, "w", encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")

    def check_timecode_sequence(self):
        srt_files = helper_functions.get_files("srt")
        if not len(srt_files):
            self.checkSequenceFeedbackTextEdit.setPlainText("No Files Found")
            return
        #* List to save the error in the timecode wether it's in the same block or between one block and the next block
        error_within_one_block = {}
        error_between_two_blocks = {}
        block_index_errors = {}
        white_space_in_block_index_error = {}
        empty_row_errors = {}
        block_format_error = {}
        
        #? Open the SRT files
        for file in srt_files:
            error_within_one_block.update({f"{file}":[]})
            error_between_two_blocks.update({f"{file}":[]})
            block_index_errors.update({f"{file}":[]})
            white_space_in_block_index_error.update({f"{file}":[]})
            empty_row_errors.update({f"{file}":[]})
            block_format_error.update({f"{file}":[]})
            block_index = 0
            block_index_indexes = []

            with open(file, "r", encoding='utf-8') as srt_file:
                #? Read the contents of the file
                srt_contents = srt_file.read()
            with open(file, "r", encoding='utf-8') as srt_file:
                srt_contents_lines = srt_file.readlines()
            #? find the timecodes
            pattern = r"\d+.*\d+.*\d+.*\d+.*\d+.*\d+.*\d+.*\d+"
            srt_timecodes = re.findall(pattern, srt_contents)
            #? Find errors in timecodes
            for line in srt_timecodes:
                if len(line.strip()) != 29:
                    block_format_error[f"{file}"].append(line)
                    continue
                try:
                    start, end = helper_functions.convert_timecode_to_millisec(line)
                    if start > end:
                        error_within_one_block[f"{file}"].append(line)
                except:
                    block_format_error[f"{file}"].append(line)

            for i in range(len(srt_timecodes) - 1):
                try:
                    _, current_block_end = helper_functions.convert_timecode_to_millisec(srt_timecodes[i])
                except:
                    if not srt_timecodes[i] in block_format_error[f"{file}"]:
                        block_format_error[f"{file}"].append(srt_timecodes[i])
                    continue
                try:
                    next_block_start, _ = helper_functions.convert_timecode_to_millisec(srt_timecodes[i + 1])
                except:
                    if not srt_timecodes[i + 1] in block_format_error[f"{file}"]:
                        block_format_error[f"{file}"].append(srt_timecodes[i + 1])
                    continue
                if current_block_end > next_block_start:
                    error_between_two_blocks[f"{file}"].append(srt_timecodes[i].strip())
                    error_between_two_blocks[f"{file}"].append(srt_timecodes[i + 1].strip())
                    
            
            #! Find errors in Block indexes
            for i, line in enumerate(srt_contents_lines):
                if line.strip().isdigit():
                    block_index_indexes.append(i)
                    block_index += 1
                    if int(line.strip()) != block_index:
                        block_index_errors[f"{file}"].append(block_index)
                    if any(char == ' ' for char in line):
                        white_space_in_block_index_error[f"{file}"].append(block_index)

            #* Find errors in empty rows
            for i in block_index_indexes:
                if i == 0:
                    continue
                if srt_contents_lines[i-1] != "\n":
                    empty_row_errors[f"{file}"].append(f"Missing empty row at line {i}")
                if srt_contents_lines[i-2] == "\n":
                    empty_row_errors[f"{file}"].append(f"Extra row at line {i}")
                if srt_contents_lines[i+1] == "\n":
                    empty_row_errors[f"{file}"].append(f"Extra row at line {i+2}")
                if srt_contents_lines[i+2] == "\n":
                    empty_row_errors[f"{file}"].append(f"Extra row at line {i+3}")

        #? count will be greater than 0 if there were error in the srt files
        count = 0
        for val1, val2, val3, val4, val5, val6 in zip(error_within_one_block.values(), error_between_two_blocks.values(), block_index_errors.values(), white_space_in_block_index_error.values(), empty_row_errors.values(), block_format_error.values()):
            if val1 or val2 or val3 or val4 or val5 or val6: count += 1  

        #* No errors were found  
        if count == 0:
            self.checkSequenceFeedbackTextEdit.setHtml("<font color='green'>All Files are Correct</font>")

        #! Errors were found 
        else:
            self.checkSequenceFeedbackTextEdit.setHtml("<font color='#116b01'>Color Codes:</font><br><font color='#6b0101'>File name; </font><font color='#ff8000'>Timing error within the same block; </font><font color='#014d6b'>Timing error between two blocks; </font><font color='#039169'>Block index error; </font><font color='#6b4401'>Empty/Extra row error; </font><font color='#690391'>Timecode format error.</font>")
            
            for file in srt_files:
                if error_within_one_block[f"{file}"] or error_between_two_blocks[f"{file}"] or block_index_errors[f"{file}"] or white_space_in_block_index_error[f"{file}"] or empty_row_errors[f"{file}"] or block_format_error[f"{file}"]:
                    temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<br><font color='#6b0101'><u>{file}</u></font>"
                    self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                #* Errors within one block
                if error_within_one_block[f"{file}"]:
                    print("Error within the same block")
                    for error in error_within_one_block[f"{file}"]:
                        temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#ff8000'>{error}</font>"
                        self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                #* Errors between two blocks
                if error_between_two_blocks[f"{file}"]:
                    print("Error between two blocks")
                    for i in range(0, len(error_between_two_blocks[f"{file}"]) - 1, 2):
                        temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#014d6b'>{error_between_two_blocks[f'{file}'][i]} ---- {error_between_two_blocks[f'{file}'][i + 1]}</font>"
                        self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                    correct_intersected_srt.correct_intersected_blocks(file)
                    temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<font color='green'>Corrected intersection between timeblocks for file: {file}</font>"
                    self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                    
                #* Errors in block index
                if block_index_errors[f"{file}"]:
                    for error in block_index_errors[f"{file}"]:
                        temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#039169'>Block Index {error} is wrong or missing</font>"
                        self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                #* Errors in block index (white spaces)
                if white_space_in_block_index_error[f"{file}"]:
                    errors = white_space_in_block_index_error[f"{file}"]
                    errors = [str(error) for error in errors]
                    temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                    if len(errors) == 1:
                        temp_text = f"{temp_text}<font color='#039169'>Extra white space at Block Index {errors[0]}</font>"
                    else:
                        temp_text = f"{temp_text}<font color='#039169'>Extra white spaces at Block Indices: {','.join(errors)}</font>"
                    self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                    self.clean_extra_white_spaces(file)
                    temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<font color='green'>Cleaned white spaces from file: {file}</font>"
                    self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                # * Missing empty rows
                if empty_row_errors[f"{file}"]:
                    for error in empty_row_errors[f"{file}"]:
                        temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#6b4401'>{error}</font>"
                        self.checkSequenceFeedbackTextEdit.setHtml(temp_text)
                #* Errors in timecode format
                if block_format_error[f"{file}"]:
                    for error in block_format_error[f"{file}"]:
                        temp_text = self.checkSequenceFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#690391'>{error}</font>"
                        self.checkSequenceFeedbackTextEdit.setHtml(temp_text)

    """Prep SRT Tab"""
    def prepare_srt_for_deepl(self):
        srt_file = self.srtPrepLoadSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")

        if srt_file:
            text_len = helper_functions.sub_srt_codes(srt_file, output_in_input_path=True)
            txt_to_append = f"<font color='#014d6b'>Successfully removed SRT timestamps and generated a text file containing chunks, each with a maximum length of 5000 characters.<font color='#014d6b'>Output saved to:</font> <font color='#039169'>{srt_file.rsplit('.', 1)[0]}.txt</font><br>"
            helper_functions.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)

            prep_srt.srt_to_json(srt_file,  text_len)
            txt_to_append = f'<font color="#014d6b">Successfully saved SRT time stamps from </font> <font color="#039169">{srt_file.split("/")[-1]}</font> <font color="#014d6b">in JSON.<br>Output saved to:</font> <font color="#039169">{srt_file.replace(".srt", "_output.json")}</font><br>'
            helper_functions.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            
    def reconstruct_srt_from_json(self):
        json_file = self.srtPrepLoadJsonTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        txt_file = self.srtPrepLoadTxtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if json_file and txt_file:
            prep_srt.reconstruct_srt_from_json_and_txt(json_file, txt_file, self.srtPrepFeedbackTextEdit)
            txt_to_append = f"<font color='#014d6b'>Successfully reconstructed SRT from JSON and TXT.</font><br><font color='#014d6b'>Output saved to</font> <font color='#039169'>{txt_file.rsplit('.', 1)[0]+'_new.srt'}</font><br>"
            helper_functions.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            if self.srtPrepDeleteJsonCheckBox.isChecked():
                os.remove(json_file)
                txt_to_append = f"<font color='#014d6b'>Successfully removed</font> <font color='#6b0101'>{json_file}</font>"
                helper_functions.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            if self.srtPrepDeleteTxtCheckBox.isChecked():
                os.remove(txt_file)
                txt_to_append = f"<font color='#014d6b'>Successfully removed</font> <font color='#6b0101'> {txt_file}</font>"
                helper_functions.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    root = UI()
    root.show()
    sys.exit(app.exec_())