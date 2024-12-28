#!/usr/bin/env python

import difflib
import json
import os
import re
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTextEdit, QRadioButton, QFileDialog, QCheckBox, QTabWidget, QComboBox
from PyQt5.QtGui import QIcon

import convention_validator as cv
import correct_intersected_srt
import helper_functions as hf
import prep_srt
import sort
import srt_vtt_converter
import sync_srt

VERSION = "1.5.5"

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
        self.splitAtPunctuationCheckBox = self.findChild(QCheckBox, "splitAtPunctuationCheckBox")
        self.srtPrepSplitAtPunctuationCheckBox = self.findChild(QCheckBox, "srtPrepSplitAtPunctuationCheckBox")
        # Radio Buttons
        self.srtRadioButton = self.findChild(QRadioButton, "srtRadioButton")
        self.txtRadioButton = self.findChild(QRadioButton, "txtRadioButton")
        self.csvRadioButton = self.findChild(QRadioButton, "csvRadioButton")
        # Push Buttons
        self.comparePushButton = self.findChild(QPushButton, "comparePushButton")
        self.sortPushButton = self. findChild(QPushButton, "sortPushButton")
        self.convertPushButton = self.findChild(QPushButton, "convertPushButton")
        self.cleanPushButton =self.findChild(QPushButton, "cleanPushButton")
        self.synchronizePushButton = self.findChild(QPushButton, "synchronizePushButton")
        self.validatePushButton = self.findChild(QPushButton, "validatePushButton")
        self.checkSequencePushButton = self.findChild(QPushButton, "checkSequencePushButton")
        self.prepSrtPushButton = self.findChild(QPushButton, "prepSrtPushButton")
        self.reConstructSrtPushButton = self.findChild(QPushButton, "reConstructSrtPushButton")
        self.fileDialog1 = self.findChild(QPushButton, "fileDialog1")    
        self.fileDialog2 = self.findChild(QPushButton, "fileDialog2")
        self.processSrtFileDialogPushButton = self.findChild(QPushButton, "processSrtFileDialogPushButton")
        self.srtPrepLoadSrtfileDialog = self.findChild(QPushButton, "srtPrepLoadSrtfileDialog")
        self.srtPrepLoadJsonfileDialog = self.findChild(QPushButton, "srtPrepLoadJsonfileDialog")
        self.srtPrepLoadTxtfileDialog = self.findChild(QPushButton, "srtPrepLoadTxtfileDialog")
        # Entries
        self.firstFileName = self.findChild(QTextEdit, "firstFile")
        self.secondFileName = self.findChild(QTextEdit, "secondFile")
        self.validateFeedbackTextEdit = self.findChild(QTextEdit, "validateFeedbackTextEdit")
        self.processSrtFeedbackTextEdit = self.findChild(QTextEdit, "processSrtFeedbackTextEdit")
        self.srtPrepLoadSrtTextEdit = self.findChild(QTextEdit, "srtPrepLoadSrtTextEdit")
        self.srtPrepLoadJsonTextEdit = self.findChild(QTextEdit, "srtPrepLoadJsonTextEdit")
        self.srtPrepLoadTxtTextEdit = self.findChild(QTextEdit, "srtPrepLoadTxtTextEdit")
        self.srtPrepFeedbackTextEdit = self.findChild(QTextEdit, "srtPrepFeedbackTextEdit")
        self.processSrtTextEdit = self.findChild(QTextEdit, "processSrtTextEdit")
        # ComboBoxes
        self.synchronizeComboBox = self.findChild(QComboBox, "synchronizeComboBox")
        self.prepSrtComboBox = self.findChild(QComboBox, "prepSrtComboBox")
        # Tab
        self.tab = self.findChild(QTabWidget, "tabWidget")
        self.tab.removeTab(2) # remove the validate srt tab TODO update this index if new tabs were added
        # Connect Buttons
        self.comparePushButton.clicked.connect(self.compare)
        self.sortPushButton.clicked.connect(self.sort_srt)
        self.convertPushButton.clicked.connect(self.convert)
        self.cleanPushButton.clicked.connect(self.clean)
        self.synchronizePushButton.clicked.connect(self.synchronize)
        self.validatePushButton.clicked.connect(self.validate_srt)
        self.checkSequencePushButton.clicked.connect(self.check_timecode_sequence)
        self.fileDialog1.clicked.connect(self.browse1)
        self.fileDialog2.clicked.connect(self.browse2)
        self.srtPrepLoadSrtfileDialog.clicked.connect(self.browse_load_srt_to_prep)
        self.srtPrepLoadJsonfileDialog.clicked.connect(self.browse_load_json_to_reconstruct_srt)
        self.srtPrepLoadTxtfileDialog.clicked.connect(self.browse_load_txt_to_reconstruct_srt)
        self.processSrtFileDialogPushButton.clicked.connect(self.browse_process_srt_tab)
        self.prepSrtPushButton.clicked.connect(self.prepare_srt_for_translation)
        self.reConstructSrtPushButton.clicked.connect(self.reconstruct_srt_from_json)

        # init combobox
        self.synchronizeComboBox.addItems(["Normal", "Short", "Adjust in assets/config.json"])
        self.synchronizeComboBox.setCurrentIndex(0)

        self.prepSrtComboBox.addItems(["Normal", "Short", "Adjust in assets/config.json"])
        self.prepSrtComboBox.setCurrentIndex(0)

        self.adjust_window_config()

    def browse1(self):
        self.firstFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt *.TXT *.srt *.SRT *.csv *.CSV)")
        self.firstFileName.setText(fname[0])

    def browse2(self):
        self.secondFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt *.TXT *.srt *.SRT *.csv *.CSV)")
        self.secondFileName.setText(fname[0])

    def browse_load_srt_to_prep(self):
        self.srtPrepLoadSrtTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.srt *.SRT)")
        self.srtPrepLoadSrtTextEdit.setText(fname[0])

    def browse_load_json_to_reconstruct_srt(self):
        self.srtPrepLoadJsonTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.json *.JSON)")
        self.srtPrepLoadJsonTextEdit.setText(fname[0])

    def browse_load_txt_to_reconstruct_srt(self):
        self.srtPrepLoadTxtTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt *.TXT)")
        self.srtPrepLoadTxtTextEdit.setText(fname[0])

    def browse_process_srt_tab(self):
        self.processSrtTextEdit.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.srt *.SRT *.vtt *.VTT)")
        self.processSrtTextEdit.setText(fname[0])

    def closeEvent(self, event):
        # get the index of the tab that was opened before closing the programm and save the index to the config file
        hf.adjust_json_file("assets/config.json", "tab_index", int(self.tab.currentIndex()))
        hf.adjust_json_file("assets/config.json", "window_width", int(self.width()))
        hf.adjust_json_file("assets/config.json", "window_height", int(self.height()))
        hf.adjust_json_file("assets/config.json", "window_x", int(self.x()))
        hf.adjust_json_file("assets/config.json", "window_y", int(self.y()))

    def adjust_window_config(self):
        with open("assets/config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.tab.setCurrentIndex(data["tab_index"])
        self.setGeometry(data["window_x"], data["window_y"], data["window_width"], data["window_height"])


    """Compare Tab"""
    # function to compare two files (srt or txt) and output the difference in an html file
    def compare(self):
        fname1 = self.firstFileName.toPlainText().replace("file:///", "").replace("\\", "/")
        fname2 = self.secondFileName.toPlainText().replace("file:///", "").replace("\\", "/")
        if self.srtRadioButton.isChecked():
            text1 = hf.clean_srt(fname1)
            text2 = hf.clean_srt(fname2)
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
        fname = self.processSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if os.path.isfile(fname):
            try:
                new_file_name = QFileDialog.getSaveFileName(self, "Save File", f"{fname}", "All Files(*)")[0]
                sort.sort(fname, output_file=new_file_name)
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Sorting finished!", "green")
            except Exception as e:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"{e}", "red")

        else:
            files = hf.get_files("srt")
            if files:
                for file in files:
                    sort.sort(file)
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Sorting finished!", "green")
            else:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"No Files Found", "black")

    """Convert Tab"""
    # function to convert files between srt and vtt
    def convert(self):
        fname = self.processSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if os.path.isfile(fname):
            try:
                if fname.lower().endswith(".srt"):
                    new_file_name = QFileDialog.getSaveFileName(self, "Save File", f"{fname.lower().replace('.srt', '.vtt')}", "All Files(*)")[0]
                    srt_vtt_converter.convert_srt_to_vtt(fname, new_file_name)
                elif fname.lower().endswith(".vtt"):
                    new_file_name = QFileDialog.getSaveFileName(self, "Save File", f"{fname.lower().replace('.vtt', '.srt')}", "All Files(*)")[0]
                    srt_vtt_converter.convert_vtt_to_srt(fname, new_file_name)
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Convert done!", "green")
            except Exception as e:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"{e}", "red")

        else:
            srt_files = hf.get_files("srt")
            vtt_files = hf.get_files("vtt")
            for file in srt_files:
                srt_vtt_converter.convert_srt_to_vtt(file)
            for file in vtt_files:
                srt_vtt_converter.convert_vtt_to_srt(file)
            
            hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Convert done!", "green")

    """Clean Tab"""
    def clean(self):
        fname = self.processSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if os.path.isfile(fname):
            try:
                if fname.lower().endswith(".srt"):
                    new_file_name = QFileDialog.getSaveFileName(self, "Save File", f"{fname.lower().replace('.srt', '.txt')}", "All Files(*)")[0]
                    hf.srt_to_plaintext(fname, output_file=new_file_name)
                    hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Text generation finished!", "green")
            except Exception as e:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"{e}", "red")

        else:
            srt_files = hf.get_files("srt")
            if srt_files:
                for file in srt_files:
                    hf.srt_to_plaintext(file)
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Text generation finished!", "green")
            else:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"No Files Found", "black")

    """Validate Tab"""
    def validate_srt(self) -> str:
        srt_files = hf.get_files("srt")
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
        fname = self.processSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if os.path.isfile(fname):
            srt_files = [fname]
        else:
            srt_files = hf.get_files("srt")
        if not len(srt_files):
            self.processSrtFeedbackTextEdit.setPlainText("No Files Found")
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
                    start, end = hf.convert_timecode_to_millisec(line)
                    if start > end:
                        error_within_one_block[f"{file}"].append(line)
                except:
                    block_format_error[f"{file}"].append(line)

            for i in range(len(srt_timecodes) - 1):
                try:
                    _, current_block_end = hf.convert_timecode_to_millisec(srt_timecodes[i])
                except:
                    if not srt_timecodes[i] in block_format_error[f"{file}"]:
                        block_format_error[f"{file}"].append(srt_timecodes[i])
                    continue
                try:
                    next_block_start, _ = hf.convert_timecode_to_millisec(srt_timecodes[i + 1])
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
            if os.path.isfile(fname):
                self.processSrtFeedbackTextEdit.setHtml("<font color='green'>File is Correct</font>")
            else:
                self.processSrtFeedbackTextEdit.setHtml("<font color='green'>All Files are Correct</font>")

        #! Errors were found 
        else:
            self.processSrtFeedbackTextEdit.setHtml("<font color='#116b01'>Color Codes:</font><br><font color='#6b0101'>File name; </font><font color='#ff8000'>Timing error within the same block; </font><font color='#014d6b'>Timing error between two blocks; </font><font color='#039169'>Block index error; </font><font color='#6b4401'>Empty/Extra row error; </font><font color='#690391'>Timecode format error.</font>")
            
            for file in srt_files:
                if error_within_one_block[f"{file}"] or error_between_two_blocks[f"{file}"] or block_index_errors[f"{file}"] or white_space_in_block_index_error[f"{file}"] or empty_row_errors[f"{file}"] or block_format_error[f"{file}"]:
                    temp_text = self.processSrtFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<br><font color='#6b0101'><u>{file}</u></font>"
                    self.processSrtFeedbackTextEdit.setHtml(temp_text)
                #* Errors within one block
                if error_within_one_block[f"{file}"]:
                    print("Error within the same block")
                    for error in error_within_one_block[f"{file}"]:
                        temp_text = self.processSrtFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#ff8000'>{error}</font>"
                        self.processSrtFeedbackTextEdit.setHtml(temp_text)
                #* Errors between two blocks
                if error_between_two_blocks[f"{file}"]:
                    print("Error between two blocks")
                    for i in range(0, len(error_between_two_blocks[f"{file}"]) - 1, 2):
                        temp_text = self.processSrtFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#014d6b'>{error_between_two_blocks[f'{file}'][i]} ---- {error_between_two_blocks[f'{file}'][i + 1]}</font>"
                        self.processSrtFeedbackTextEdit.setHtml(temp_text)
                    correct_intersected_srt.correct_intersected_blocks(file)
                    temp_text = self.processSrtFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<font color='green'>Corrected intersection between timeblocks for file: {file}</font>"
                    self.processSrtFeedbackTextEdit.setHtml(temp_text)
                    
                #* Errors in block index
                if block_index_errors[f"{file}"]:
                    for error in block_index_errors[f"{file}"]:
                        temp_text = self.processSrtFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#039169'>Block Index {error} is wrong or missing</font>"
                        self.processSrtFeedbackTextEdit.setHtml(temp_text)
                #* Errors in block index (white spaces)
                if white_space_in_block_index_error[f"{file}"]:
                    errors = white_space_in_block_index_error[f"{file}"]
                    errors = [str(error) for error in errors]
                    temp_text = self.processSrtFeedbackTextEdit.toHtml()
                    if len(errors) == 1:
                        temp_text = f"{temp_text}<font color='#039169'>Extra white space at Block Index {errors[0]}</font>"
                    else:
                        temp_text = f"{temp_text}<font color='#039169'>Extra white spaces at Block Indices: {','.join(errors)}</font>"
                    self.processSrtFeedbackTextEdit.setHtml(temp_text)
                    self.clean_extra_white_spaces(file)
                    temp_text = self.processSrtFeedbackTextEdit.toHtml()
                    temp_text = f"{temp_text}<font color='green'>Cleaned white spaces from file: {file}</font>"
                    self.processSrtFeedbackTextEdit.setHtml(temp_text)
                # * Missing empty rows
                if empty_row_errors[f"{file}"]:
                    for error in empty_row_errors[f"{file}"]:
                        temp_text = self.processSrtFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#6b4401'>{error}</font>"
                        self.processSrtFeedbackTextEdit.setHtml(temp_text)
                #* Errors in timecode format
                if block_format_error[f"{file}"]:
                    for error in block_format_error[f"{file}"]:
                        temp_text = self.processSrtFeedbackTextEdit.toHtml()
                        temp_text = f"{temp_text}<font color='#690391'>{error}</font>"
                        self.processSrtFeedbackTextEdit.setHtml(temp_text)

    """Prep SRT Tab"""
    def prepare_srt_for_translation(self):
        srt_file = self.srtPrepLoadSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")

        if srt_file:
            text_len = hf.sub_srt_codes(srt_file, save_output_where_input_is_located=True)
            txt_to_append = f"<font color='#014d6b'>Successfully removed SRT timestamps and generated a text file containing chunks, each with a maximum length of 5000 characters.<font color='#014d6b'>Output saved to:</font> <font color='#039169'>{srt_file.rsplit('.', 1)[0]}.txt</font><br>"
            hf.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)

            prep_srt.srt_to_json(srt_file,  text_len)
            txt_to_append = f'<font color="#014d6b">Successfully saved SRT time stamps from </font> <font color="#039169">{srt_file.split("/")[-1]}</font> <font color="#014d6b">in JSON.<br>Output saved to:</font> <font color="#039169">{srt_file.replace(".srt", "_output.json")}</font><br>'
            hf.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            
    def reconstruct_srt_from_json(self):
        json_file = self.srtPrepLoadJsonTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        txt_file = self.srtPrepLoadTxtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")
        if json_file and txt_file:
            prep_srt.reconstruct_srt_from_json_and_txt(json_file, txt_file)
            srt_file_path = txt_file.rsplit(".", 1)[0]+"_new.srt"
            max_char_per_line, min_char_per_line, split_at_punctuation, punctuations = self.get_sync_config(self.prepSrtComboBox)
            sync_srt.sync(srt_file_path, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations, srt_file_path)
            txt_to_append = f"<font color='#014d6b'>Successfully reconstructed SRT from JSON and TXT.</font><br><font color='#014d6b'>Output saved to</font> <font color='#039169'>{txt_file.rsplit('.', 1)[0]+'_new.srt'}</font><br>"
            hf.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            if self.srtPrepDeleteJsonCheckBox.isChecked():
                os.remove(json_file)
                txt_to_append = f"<font color='#014d6b'>Successfully removed</font> <font color='#6b0101'>{json_file}</font>"
                hf.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
            if self.srtPrepDeleteTxtCheckBox.isChecked():
                os.remove(txt_file)
                txt_to_append = f"<font color='#014d6b'>Successfully removed</font> <font color='#6b0101'> {txt_file}</font>"
                hf.append_to_textedit(self.srtPrepFeedbackTextEdit, txt_to_append)
    
    def get_sync_config(self, combobox):
        # get user input
        punctuations = None
        if self.splitAtPunctuationCheckBox.isChecked():
            split_at_punctuation = True
        else:
            split_at_punctuation = False

        with open("assets/config.json", "r", encoding='utf-8') as f:
            config_data = json.load(f)

        punctuations = config_data["punctuations"]

        sync_combobox_index = combobox.currentIndex()
        if sync_combobox_index == 0:
            max_char_per_line = 42
            min_char_per_line = 30
        elif sync_combobox_index == 1:
            max_char_per_line = 30
            min_char_per_line = 20
        else:
            max_char_per_line = config_data["max_char_per_line"]
            min_char_per_line = config_data["min_char_per_line"]

        return max_char_per_line, min_char_per_line, split_at_punctuation, punctuations

    def synchronize(self):
        fname = self.processSrtTextEdit.toPlainText().replace("file:///", "").replace("\\", "/")

        max_char_per_line, min_char_per_line, split_at_punctuation, punctuations = self.get_sync_config(self.synchronizeComboBox)
        
        if os.path.isfile(fname):
            new_file_name = QFileDialog.getSaveFileName(self, "Save File", f"{fname}", "All Files(*)")[0]
            srt_files = [fname]
        else:
            srt_files = hf.get_files("srt")

        for srt_file in srt_files:
            sort.sort(srt_file, edit_original_file=True)
            self.clean_extra_white_spaces(srt_file)
            correct_intersected_srt.correct_intersected_blocks(srt_file)
            try:
                if os.path.isfile(fname):
                    sync_srt.sync(srt_file, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations, new_file_name)
                else:
                    sync_srt.sync(srt_file, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations)
            except Exception as e:
                hf.write_to_textedit(self.processSrtFeedbackTextEdit, f"{e}", "red")
                return

        hf.write_to_textedit(self.processSrtFeedbackTextEdit, "Synchronization finished!", "green")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    root = UI()
    root.show()
    sys.exit(app.exec_())