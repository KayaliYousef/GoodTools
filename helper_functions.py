import glob
import re

"""Helper Functions"""

def append_to_textedit(text_edit:object, text:str) -> None:
    """
    Appends input text to text_edit object and move the cursor to the end (scroll to bottom)

        Parameters:
            text_edit (object): PyQt TextEdit object to append text to it
            text (str): Input string to be append to the end of the TextEdit Object

        Returns:
            None
    """
    temp_text = text_edit.toHtml()
    appended_text = f"{temp_text}{text}"
    text_edit.setHtml(appended_text)
    cursor = text_edit.textCursor()
    cursor.movePosition(cursor.End)
    text_edit.setTextCursor(cursor)

def get_files(extension:str) -> list[str]:
    """
    Retrieves a list of files with the specified extension from the current working directory.

        Parameters:
            extension (str): The file extension to search for (e.g., 'txt', 'csv', 'jpg').
                            Do not include a leading period (e.g., use 'txt' instead of '.txt').

        Returns:
            list[str]: A list of file names that have the specified extension.
                    Returns an empty list if no matching files are found.

        Example:
            >>> get_files("txt")
            ['file1.txt', 'notes.txt']

        Notes:
            - The search is case-sensitive; files with uppercase extensions (e.g., '.TXT') will
            not be matched unless specified exactly.
            - The function searches only in the current working directory.
    """
    files = []
    for file in glob.glob("*."+extension):
        files.append(file)
    return files

def clean_srt(srt_file_path:str) -> str:
    """
    Removes time codes, block numbers and empty lines from a given srt file

        Parameters:
            srt_file_path (str): The path to the srt file

        Returns:
            str: The input srt file without time codes or block numbers. Line breaks are
                not removed from the srt.

        Example:
            srt_content = '''
            1
            00:00:00,120 --> 00:00:01,640
            Over the last year, 
            we have witnessed

            2
            00:00:01,640 --> 00:00:03,880
            what is the greatest crime of the 21st
            '''
            >>> clean_srt(srt_path)
            '''
            Over the last year, 
            we have witnessed
            what is the greatest crime of the 21st
            '''       
    """
    path = re.sub(r"\\", "/", srt_file_path)
    with open(path, 'r', encoding="utf-8") as f:
        text = f.readlines()
    # remove time codes and subtitle block indexes
    cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
    # remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line.strip()]
    return ''.join(cleaned_lines)

def convert_time_string_to_millisec(time_string:str) -> int:
    """
    Convert only one part of the timecode to millisec

        Parameters:
            time_string (str): Time code in the format hh:mm:ss,ms

        Returns:
            int: The converted time string in milliseconds

        Example:
            >>> convert_time_string_to_millisec("00:08:43,281")
            523281
    """
    # hours, minutes seconds and miliseconds
    h, m, s = time_string.split(":")
    # seconds and miliseocnds
    s, ms = s.split(",")

    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def convert_timecode_to_millisec(timecode:str) -> tuple[int, int]:
    """
    Convert both parts of the SRT time code to milliseconds.

        Parameters:
            timecode (str): SRT timecode to be converted to milliseconds

        Returns:
            tuple(int, int): Both parts of the SRT timecode converted in milliseconds
    
        Example:
            >>> convert_timecode_to_millisec("00:04:11,878 --> 00:04:12,715")
           (251878, 252715)
    """
    start, end = timecode.split("-->")
    start = convert_time_string_to_millisec(start)
    end = convert_time_string_to_millisec(end)
    return start, end

def convert_millisec_to_timecode(milliseconds: int) -> str:
    """
    Convert input given in milliseconds into timecode with the following format hh:mm:ss,ms

        Parameters:
            milliseconds (int): Input integer in milliseconds to be converted to timecode
        
        Returns:
            str: Timecode string with the formant hh:mm:ss,ms

        Raises:
            TypeError: If the input (milliseconds) is not an integer.

        Example:
            >>> convert_millisec_to_timecode(251878)
            '00:04:11,878'
    """
    if not isinstance(milliseconds, int):
        raise TypeError(f"milliseconds must be an integer")
    hours = milliseconds // 3600000
    minutes = (milliseconds // 60000) % 60
    seconds = (milliseconds // 1000) % 60
    milliseconds_remainder = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds_remainder:03}"


def srt_to_plaintext(srt_file_path:str, output_in_input_path=False) -> None:
    """
    Converts srt to plain text removing time codes, block numbers and line breaks, then adds a new line break after every dot

        Parameters:
            srt_file_path (srt): The path to the srt file
            output_in_input_path (bool): Flag to control where the output file should be saved
                                        - True: The output will be saved where the input file is located
                                        - False: The output will be saved where the program is executed

        Returns:
            None

    """
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

    # output should be saved where input file is located
    if output_in_input_path:
        fileName = srt_file_path.rsplit(".", 1)[0]
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].rsplit(".", 1)[0]
    
    with open(f"{fileName}.txt", "w", encoding='utf-8') as srt_file:
        srt_file.write(cleaned_lines)

def sub_srt_codes(srt_file_path:str, output_in_input_path=False) -> int:
    """
    Converts SRT file into plain text removing block numbers, time codes and empty lines from a SRT file.
    Then splits the text into chunks with maximum length of 5000 characters

        Parameters:
        srt_file_path (srt): The path to the srt file
        output_in_input_path (bool): Flag to control where the output file should be saved
                                    - True: The output will be saved where the input file is located
                                    - False: The output will be saved where the program is executed

        Returns:
            int: The length of the output text after converting to plain text and splitting into chuncks
            
    """
    path = re.sub(r"\\", "/", srt_file_path)
    with open(path, 'r', encoding="utf-8") as f:
        text = f.read()
    # pattern that should match with digit or more then line break then a line that ends with a linebreak,
    # which correspond to block number line then timecode line in a SRT file format.
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
        
    # output should be saved where the input file is located
    if output_in_input_path:
        fileName = srt_file_path.rsplit(".", 1)[0]
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].rsplit(".", 1)[0]
    with open(f"{fileName}.txt", "w", encoding='utf-8') as srt_file:
        srt_file.write(new_text)

    return len(new_text)


def find_first_breaker(text: str, breakers: list) -> tuple[int, str]:
    """
    Finds the first occurrence of a breaker in the text.
    If the breaker is a dot the following two characters of the breaker will be checked as well in case they are also dots ('...' case).
    If the breaker is a question mark the following character will be searched in case the character is another question mark or an exclamation mark ('??' or '?! case)
    If the breaker is a dot or a comma we check the character after the break, if the character is a digit we ignore this breaker (15.000 or 15,000)
    
        Parameters:
            text (str): Text to be searched for a breaker
            breakers (list): List of breakers such as ['.', ',', ':'] to be searched for in the text

        Returns:
            tuple(int, str): The index of the breaker found in the text and the breaker it self

        Example:
            >>> find_first_breaker("Hello, world", ['.', ',', ':', '?', '!'])
            (5, ',')
    """
    for i, char in enumerate(text):
        if char in breakers:
            # Handle specific cases
            if char == '.' or char == ',' and text[i + 1].isdigit() and text[i - 1].isdigit():
                continue
            elif char == '.' and i + 2 < len(text) and text[i + 1:i + 3] == '..':
                return i + 2, '...'
            elif char == '?' and i + 1 < len(text):
                if text[i + 1] in ['!', '?']:
                    return i + 1, text[i + 1]
            return i, char
    return len(text) - 1, ''  # Default to end of text if no breaker found

def split_text_by_index(text: str, index: int) -> tuple[str, str]:
    """
    Splits a string into two parts at the specified index.

        Parameters:
            text (str): The input string to be split.
            index (int): The position at which the string should be divided.
                        The character at this index will be included in the first part.

        Returns:
            tuple[str, str]: A tuple containing two strings:
                            - The first string includes characters from the start of the input
                            string up to and including the character at the specified index.
                            - The second string contains the remaining characters from the input
                            string after the specified index.

        Raises:
            ValueError: If the index is out of bounds for the given string.

        Example:
            >>> split_text_by_index("hello world", 4)
            ('hello', ' world')
    """
    return text[:index + 1] , text[index + 1:]

def split_text_by_whitespace(text: str, max_index: int):
    """
    Splits the text at a given index if the text at the index is a whitespace, otherwise start a search for the first occurance of a whitespace left to the given index.
    
        Parameters:
            text (str): The input string to be split
            max_index (int): Index at which or before it the text should be split 

        Returns:
            tuple(str, str): A tuple containing two strings:
                            - The first string includes characters from the start of the text up to
                            a whitespace at or abefore max_index
                            - The second string contains the remaining characters for the text

        Example:
            >>> split_text_by_whitespace("Hello world, this is an example text", 18)
            ('Hello world, this', 'is an example text')

    """
    whitespace_index = text[:max_index].rfind(' ')
    return text[:whitespace_index], text[whitespace_index:]

def calculate_timecode_by_ratio(timecode_duration, full_text, text_chunk):
    """
    Calculates the proportional duration for a text chunk from the full text, given the full duration of the text.

        Parameters:
            timecode_duration (int): The duration of the full text (in millisecond)
            full_text (str): The input text string
            text_chunk (str): A chunk of the full text
        Returns:
            int: The duration of the text chunk
        Example:
            >>> calculate_timecode_by_ratio(1500, "Hello, world", "Hello")
            625
    """
    return int(len(text_chunk) / len(full_text) * timecode_duration)

def split_text_with_max_char(text, max_char_per_line):
    def find_split_index(s):
        """Find the index to split the text at the nearest whitespace."""
        if len(s) <= max_char_per_line:
            return len(s)
        for i in range(max_char_per_line, 0, -1):
            if s[i].isspace():
                return i
        return max_char_per_line  # In case no whitespace is found

    # Find split for the first line
    split_index = find_split_index(text)
    line_one = text[:split_index]
    remaining_text = text[split_index:]

    # Find split for the second line
    split_index = find_split_index(remaining_text)
    line_two = remaining_text[:split_index]
    remaining_text = remaining_text[split_index:]

    return line_one, line_two, remaining_text