import difflib
import glob
import re
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QTextEdit, QRadioButton, QFileDialog
from PyQt5.QtGui import QIcon

import convention_validator as cv
import sort
import srt_vtt_converter

class UI(QMainWindow):
  # constructor
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi('assets/good_tools.ui', self)

        self.setWindowIcon(QIcon('assets/palmtree.png'))
        self.setWindowTitle("GoodTools")

        # Define Widgets
        # Labels
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
        self.fileDialog1 =self.findChild(QPushButton, "fileDialog1")    
        self.fileDialog2 =self.findChild(QPushButton, "fileDialog2")
        # Entries
        self.firstFileName = self.findChild(QTextEdit, "firstFile")
        self.secondFileName = self.findChild(QTextEdit, "secondFile")
        self.validateFeedbackTextEdit = self.findChild(QTextEdit, "validateFeedbackTextEdit")

        # Connect Buttons
        self.comparePushButton.clicked.connect(self.compare)
        self.sortPushButton.clicked.connect(self.sort_srt)
        self.convertPushButton.clicked.connect(self.convert)
        self.cleanPushButton.clicked.connect(self.clean)
        self.validatePushButton.clicked.connect(self.validate_srt)
        self.fileDialog1.clicked.connect(self.browse1)
        self.fileDialog2.clicked.connect(self.browse2)

    def browse1(self):
        self.firstFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt) (*.srt)")
        self.firstFileName.setText(fname[0])
    def browse2(self):
        self.secondFileName.setText("")
        fname = QFileDialog.getOpenFileName(self, "choose file", ".", "(*.txt) (*.srt)")
        self.secondFileName.setText(fname[0])


    # function to get files in directory
    def get_files(self, extension:str) -> list[str]:
        files = []
        for file in glob.glob("*."+extension):
            files.append(file)
        return files

    # function to convert files between srt and vtt
    def convert(self):
        srt_files = self.get_files("srt")
        vtt_files = self.get_files("vtt")
        for file in srt_files:
            srt_vtt_converter.convert_srt_to_vtt(file)
        for file in vtt_files:
            srt_vtt_converter.convert_vtt_to_srt(file)

    def sort_srt(self):
        files = sort.get_files()
        sort.sort(files)

    # function to compare two files (srt or txt) and output the difference in an html file
    def compare(self):
        fname1 = self.firstFileName.toPlainText().replace("file:///", "")
        fname2 = self.secondFileName.toPlainText().replace("file:///", "")
        if self.srtRadioButton.isChecked():
            text1 = self.clean_srt(fname1)
            text2 = self.clean_srt(fname2)
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


    def clean(self):
        srt_files = self.get_files("srt")
        for file in srt_files:
            self.srt_to_plaintext(file)

    # function to remove time code and block indexes from srt
    def clean_srt(self, srt_file_path:str) -> str:
        path = re.sub(r"\\", "/", srt_file_path)
        with open(path, 'r', encoding="utf-8") as f:
            text = f.readlines()
        # remove time codes and subtitle block indexes
        cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
        # remove empty lines
        cleaned_lines = [line for line in cleaned_lines if line.strip()]
        return '\n'.join(cleaned_lines)
    
    # function to cenvert srt to plain text removing the line breaks and adding new line breaks after every dot
    def srt_to_plaintext(self, srt_file_path:str) -> str:
        path = re.sub(r"\\", "/", srt_file_path)
        with open(path, 'r', encoding="utf-8") as f:
            text = f.readlines()
        # remove time codes and subtitle block indexes
        cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
        # remove empty lines
        cleaned_lines = [line for line in cleaned_lines if line.strip()]
        # remove line breaks
        cleaned_lines = [line.strip() for line in cleaned_lines]
        # join the text together
        cleaned_lines = ''.join(cleaned_lines)
        # add line breaks after dots
        cleaned_lines = re.sub(r'\.(?![\.\.])\s*', '.\n', cleaned_lines)
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].split(".")
        fileName = fileName[0]
        with open(f"{fileName}.txt", "w") as vtt_file:
            vtt_file.write(cleaned_lines)
    
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
        
    def validate_srt(self) -> str:
        srt_files = self.get_files("srt")
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
                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    root = UI()
    root.show()
    sys.exit(app.exec_())