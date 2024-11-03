import glob
import re

"""Helper Functions"""
# function to append txt to textedit and move the cursor to the end
def append_to_textedit(text_edit:object, text:str) -> None:
    temp_text = text_edit.toHtml()
    appended_text = f"{temp_text}{text}"
    text_edit.setHtml(appended_text)
    cursor = text_edit.textCursor()
    cursor.movePosition(cursor.End)
    text_edit.setTextCursor(cursor)

# function to get files in directory
def get_files(extension:str) -> list[str]:
    files = []
    for file in glob.glob("*."+extension):
        files.append(file)
    return files

# function to remove time code and block indexes from srt
def clean_srt(srt_file_path:str) -> str:
    path = re.sub(r"\\", "/", srt_file_path)
    with open(path, 'r', encoding="utf-8") as f:
        text = f.readlines()
    # remove time codes and subtitle block indexes
    cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
    # remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line.strip()]
    return '\n'.join(cleaned_lines)

def convert_timecode_to_millisec(timecode:str) -> tuple[int, int]:
    start, end = timecode.split("-->")
    #* hours, minutes seconds and miliseconds
    h_start, m_start, s_start = start.split(":")
    #* seconds and miliseocnds
    s_start, ms_start = s_start.split(",")
    #* hours, minutes seconds and miliseconds
    h_end, m_end, s_end = end.split(":")
    #* seconds and miliseocnds
    s_end, ms_end = s_end.split(",")
    start = int(h_start) * 3600000 + int(m_start) * 60000 + int(s_start) * 1000 + int(ms_start)
    end = int(h_end) * 3600000 + int(m_end) * 60000 + int(s_end) * 1000 + int(ms_end)
    return start, end

def convert_millisec_to_timecode(milliseconds: int) -> str:
    hours = milliseconds // 3600000
    minutes = (milliseconds // 60000) % 60
    seconds = (milliseconds // 1000) % 60
    milliseconds_remainder = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds_remainder:03}"


# function to cenvert srt to plain text removing the line breaks and adding new line breaks after every dot
def srt_to_plaintext(srt_file_path:str, output_in_input_path=False) -> str:
    path = re.sub(r"\\", "/", srt_file_path)
    with open(path, 'r', encoding="utf-8") as f:
        text = f.readlines()
    # remove time codes and subtitle block indexes
    cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
    # remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line.strip()]
    # remove line breaks and replace them with a white space
    cleaned_lines = [line.strip()+" " for line in cleaned_lines]
    # join the text together
    cleaned_lines = ''.join(cleaned_lines)
    # add line breaks after dots
    cleaned_lines = re.sub(r'\.(?![\.\.])\s*', '.\n', cleaned_lines)
    if output_in_input_path:
        fileName = srt_file_path.rsplit(".", 1)[0]
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].rsplit(".", 1)[0]
    with open(f"{fileName}.txt", "w", encoding='utf-8') as srt_file:
        srt_file.write(cleaned_lines)

def sub_srt_codes(srt_file_path:str, output_in_input_path=False) -> tuple[int, int]:
    path = re.sub(r"\\", "/", srt_file_path)
    with open(path, 'r', encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(r'^\d+\n.*\n', re.MULTILINE)
    # Replace the matches with the modified format
    text = re.sub(pattern, "", text)
    # split the text into lines
    text = text.splitlines()
    # remove empty lines
    text = [line for line in text if line.strip()]
    # strip lines
    text = [line.strip() for line in text]
    # rejoin the text back together with white spaces between lines
    text = ' '.join(text)

    # splitting the text into lines with maximum length of 5000 characters
    new_text = ""
    marker = 0
    tracker = 0
    previous_dot_index = 0
    dot_index = 0
    max_number_of_characters = 5000
    for i, char in enumerate(text):
        tracker += 1
        if '.' in char:
            dot_index = i
        if tracker >= max_number_of_characters and dot_index != previous_dot_index:
            text_chunk = text[marker:dot_index+1].strip()
            new_text += text_chunk + "\n\n"
            marker = dot_index+1
            tracker = i - dot_index+1
            previous_dot_index = dot_index
        if tracker < max_number_of_characters and i == len(text)-1:
            text_chunk = text[marker:].strip()
            new_text += text_chunk
        
    
    if output_in_input_path:
        fileName = srt_file_path.rsplit(".", 1)[0]
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].rsplit(".", 1)[0]
    with open(f"{fileName}.txt", "w", encoding='utf-8') as srt_file:
        srt_file.write(new_text)

    return len(new_text)