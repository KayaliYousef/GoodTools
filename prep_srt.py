import re
import json
import copy

import helper_functions as hf

def srt_to_json(srt_file_path:str, save_json=True) -> None | dict:
    """
    Conver SRT to JSON format extracting information about the SRT

        Parameters:
            srt_file_path (str): Path to the SRT file
            save_json (bool): If True saves the python dict into a JSON file in the same folder with the SRT file
                            If False returns a python dict
                        
        Returns:
            None or dict: None if save_json is True, else returns a python dict
    """
    
    # Read the SRT file
    with open(srt_file_path, 'r', encoding='utf-8') as file:
        srt_content = file.readlines()

    # make sure the the srt lines don't have extry white spaces after each line
    srt_content = [line.strip() for line in srt_content]
    srt_content = "\n".join(srt_content)

    # Split the content into blocks based on the blank lines
    srt_blocks = re.split(r'\n\s*\n', srt_content.strip())

    # Initialize a list to store JSON entries
    json_entries = []
    weights = []

    total_duration = 0  # Variable to store the total duration of the subtitle file
    total_characters = 0  # Variable to store the total number of characters in the subtitle file

    r"""
    - Grouping pattern
    - first group (\d+) matches the block number
    - second group (\d{2}:\d{2}:\d{2},\d{1,3}) matches the start of the time code
    - third group (\d{2}:\d{2}:\d{2},\d{1,3}) matchs the end of the time code
    - forth group (.+) matches the text
    """
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{1,3}) --> (\d{2}:\d{2}:\d{2},\d{1,3})\n(.+)'
    for block in srt_blocks:
        # Extract block number, time code, and text using regex
        match = re.match(pattern, block, re.DOTALL)

        if match:
            block_number, start_time, end_time, text = match.groups()
            num_characters = len(text)
            total_characters += num_characters

    for block in srt_blocks:
        # Extract block number, time code, and text using regex
        match = re.match(pattern, block, re.DOTALL)

        if match:
            block_number, start_time, end_time, text = match.groups()

            # Calculate the duration of the subtitle block
            start_seconds = hf.convert_time_string_to_millisec(start_time) / 1000
            end_seconds = hf.convert_time_string_to_millisec(end_time) / 1000
            duration = end_seconds - start_seconds

            # Calculate the number of characters in the text
            num_characters = len(text)
            # Claculate the ratio of the text from this block to the tatal text
            weight = (num_characters / total_characters) * 100
            weights.append(weight)

            # Create a dictionary for the JSON entry
            entry = {
                'block_number': int(block_number),
                'time_code': f'{start_time} --> {end_time}',
                'time_code_start': start_time,
                'time_code_end': end_time,
                'text': text.strip(),
                'linebreak_in_text': True if '\n' in text else False,
                'num_characters': num_characters,
                'weight' : weight,
                'duration_in_seconds': duration,
                'duration_in_milliseconds': duration * 1000,
            }

            # Append the entry to the list
            json_entries.append(entry)

            # Update total duration and total characters
            total_duration += duration

    # Calculate average characters per second
    average_characters_per_second = total_characters / total_duration if total_duration > 0 else 0

    # Additional information to include in the JSON file
    additional_info = {
        'total_duration': total_duration,
        'total_characters': total_characters,
        'total_weight': sum(weights),
        'weights_list': weights,
        'average_characters_per_second': average_characters_per_second,
        'total_blocks': len(json_entries)
    }

    # Combine JSON entries and additional information
    result = {'entries': json_entries, 'additional_info': additional_info}

    if save_json:
        # Save the JSON data to a file
        json_file_path = srt_file_path.replace('.srt', '_output.json')
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=2)
    
    else:
        return result

def json_to_srt(json_data: dict) -> str:
    """
    Convert JSON to SRT format

        Parameters:
            json_data (dict): Python dictionary containing the necessary information for the SRT

        Returns:
            str: SRT formatted string
    """
    # Extract entries and additional information
    entries = json_data.get('entries', [])

    # Initialize an empty string to store the SRT content
    srt_content = ''

    for entry in entries:
        # Extract information from the JSON entry
        block_number = entry.get('block_number', '')
        time_code = entry.get('time_code', '')
        text = entry.get('text', '')

        # Create the SRT block
        srt_block = f"{block_number}\n{time_code}\n{text}\n\n"

        # Append the SRT block to the content
        srt_content += srt_block

    return srt_content

def divide_text_with_weights(text: str, weights: list[float]) -> list[str]:
    """
    Divide plain text into chunks of text using weights from the original SRT file, each chunk represents a SRT block text

        Parameters:
            text (str): Plain text to be divided into chunks
            weights (list of floats): List of weights (floats) to be used to divide the text

        Returns:
            list of strings: Each string is an STR block text 
    """

    percentages = [weight / 100 for weight in weights]

    chunks = []
    start_index = 0
    """
    - When splitting the text block using percentages, we ensure that the split occurs only at whitespace. 
    - To achieve this, we keep adding characters to the text until we encounter a whitespace, then make the split. 
    - However, this approach can disrupt the balance of the text distribution, leading to some blocks at the end 
    - having no text at all. 
    - To resolve this issue, we use a modifier that tracks the number of extra characters added to the current block. 
    - This count is then subtracted from the next block, ensuring that all blocks contain some text and maintain 
    - a more even distribution.
    """

    modifier = 0

    for percentage in percentages:
        # Find the index where the split should occur based on white spaces
        end_index = start_index + round(percentage * len(text)) - modifier
        modifier = 0

        # this loop ensures that the end index is a whitespace, 
        # it also counts how many extra characters were added to this chunk
        while end_index < len(text) and not text[end_index].isspace():
            end_index += 1
            modifier += 1

        # add the chunk to the list
        chunks.append(text[start_index:end_index].strip())
        # update the start index
        start_index = end_index

    # Adding the remaining text, if any, to the last chunk
    if start_index < len(text):
        chunks[-1] += text[start_index:]

    return chunks

def split_in_half(text: str, max_char_per_line=33) -> str:
    """
    Splits a text in half if the length of the text exceeds a max number of characters. While splitting this function ensures that the split occurs only at a white space and the difference in length between the two lines is as small as possible

        Parameters:
            text (str): Input text to be splitted in half
            max_char_per_line (int): The maximum number of characters allowed,
                                    only if the length of the text is larger than this number,
                                    then the text will be splitted in half

        Returns:
            str: The input text splitted in half
    """
    # text length is greater than the max allowed character per line
    if len(text) > max_char_per_line:
        # two variables that mark the middle of the text
        mid_forward = len(text) // 2
        mid_backward = len(text) // 2
        mid = 0

        # if the middle of the text is not a white space, search forward for a white space
        while mid_forward < len(text) and not text[mid_forward].isspace():
            mid_forward += 1

        # if the middle of the text is not a white space, search backward for a white space
        while mid_backward >= 0 and not text[mid_backward].isspace():
            mid_backward -= 1

        # check for the difference between character in the splitted lines (in both cases) and choose the smaller
        diff_forward = len(text[:mid_forward].strip()) - len(text[mid_forward:].strip())
        diff_backward = len(text[:mid_backward].strip()) - len(text[mid_backward:].strip())
        if abs(diff_forward) >= abs(diff_backward):
            mid = mid_backward
        else:
            mid = mid_forward

        splitted_text = text[:mid].strip() + "\n" + text[mid:].strip()

        return splitted_text
    # text length is smaller than or equal the max allowed character per line
    else:
        return text

def reconstruct_srt_from_json_and_txt(json_file_path:str, txt_file_path:str) -> None:
    """
    Reconstructs SRT using the SRT original data saved in JSON and the SRT text as palin text as input

        Parameters:
            json_file_path (str): Path to JSON file
            txt_file_path (str): Path to TEXT file

        Returns:
            None
    """
    # Load the JSON data
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    # Read the text file
    with open(txt_file_path, "r", encoding='utf-8') as file:
        text_content = file.read()
    
    # get the weights of the original SRT blocks
    weights = json_data["additional_info"]["weights_list"]
    # dict to save the output into
    json_data_copy = copy.deepcopy(json_data)

    # divide the text into chunks using the weights from the original SRT
    text_chuncks = divide_text_with_weights(text_content, weights)

    # write the new chunks (translated) in the place of the old chunks (original language)
    for text_block, json_entry in zip(text_chuncks, json_data_copy["entries"]):
        text_block = split_in_half(text_block)
        json_entry["text"] = text_block.strip()

    # convert the JSON with the new chunks into SRT
    srt_content = json_to_srt(json_data_copy)

    # Save the result to a new file
    srt_file_path = txt_file_path.rsplit(".", 1)[0]+"_new.srt"
    with open(srt_file_path, "w", encoding='utf-8') as output_file:
        output_file.write(srt_content)


