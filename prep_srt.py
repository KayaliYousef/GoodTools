import re
import json
import copy

import helper_functions

def srt_to_json(srt_file_path:str, text_len:int) -> int:
    # Read the SRT file
    with open(srt_file_path, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    # Split the content into blocks based on the blank lines
    srt_blocks = re.split(r'\n\s*\n', srt_content.strip())

    # Initialize a list to store JSON entries
    json_entries = []

    total_duration = 0  # Variable to store the total duration of the subtitle file
    total_characters = 0  # Variable to store the total number of characters in the subtitle file

    for block in srt_blocks:
        # Extract block number, time code, and text using regex
        match = re.match(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+)', block, re.DOTALL)

        if match:
            block_number, start_time, end_time, text = match.groups()

            # Calculate the duration of the subtitle block
            start_seconds = int(start_time[:2]) * 3600 + int(start_time[3:5]) * 60 + int(start_time[6:8]) + int(start_time[9:]) / 1000
            end_seconds = int(end_time[:2]) * 3600 + int(end_time[3:5]) * 60 + int(end_time[6:8]) + int(end_time[9:]) / 1000
            duration = end_seconds - start_seconds

            # Calculate the number of characters in the text
            num_characters = len(re.sub(r'\s', '', text))

            # Create a dictionary for the JSON entry
            entry = {
                'block_number': int(block_number),
                'time_code': f'{start_time} --> {end_time}',
                'text': text.strip(),
                'num_characters': num_characters,
                'duration': duration
            }

            # Append the entry to the list
            json_entries.append(entry)

            # Update total duration and total characters
            total_duration += duration
            total_characters += num_characters

    # Calculate average characters per second
    average_characters_per_second = total_characters / total_duration if total_duration > 0 else 0

    # Additional information to include in the JSON file
    additional_info = {
        'total_duration': total_duration,
        'total_characters': {
            'without_white_spaces_or_separators': total_characters,
            'with_white_spaces_and_separators': text_len
        },
        'average_characters_per_second': average_characters_per_second,
        'total_blocks': len(json_entries)
    }

    # Combine JSON entries and additional information
    result = {'entries': json_entries, 'additional_info': additional_info}

    # Save the JSON data to a file
    json_file_path = srt_file_path.replace('.srt', '_output.json')
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=2)

    return result["additional_info"]["total_blocks"]

def json_to_srt(json_data: str) -> str:
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

def reconstruct_srt_from_json_and_txt(json_file_path:str, txt_file_path:str, text_edit:object, sep="$$$$") -> int:
    # Load the JSON data
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    # Read the text file
    with open(txt_file_path, "r", encoding='utf-8') as file:
        text_content = file.read()
    
    total_blocks = json_data["additional_info"]["total_blocks"]
    total_seps = text_content.count(sep)

    if total_blocks == total_seps:
        text_blocks = text_content.split(sep)
        text_blocks = text_blocks[1:]
        print(len(text_blocks), total_blocks)
        # dict to save the translation into
        json_data_copy = copy.deepcopy(json_data)
        for text_block, json_entry in zip(text_blocks, json_data_copy["entries"]):
            json_entry["text"] = text_block.strip()

        for old_entry, new_entry in zip(json_data["entries"], json_data_copy["entries"]):
            old_text = old_entry["text"]
            new_text = new_entry["text"]
            if '\n' in old_text.strip():
                ratio = old_text.strip().split('\n')
                ratio = len(ratio[0].split())
                index = 0
                tracker = 0
                for i, letter in enumerate(new_text):
                    if letter == " ":
                        tracker += 1
                        index = i
                    if tracker == ratio:
                        break
                new_text_with_linebreak = new_text[:index]+"\n"+new_text[index+1:]
                new_entry["text"] = new_text_with_linebreak

        srt_content = json_to_srt(json_data_copy)

        # Save the result to a new file
        srt_file_path = txt_file_path.rsplit(".", 1)[0]+"_new.srt"
        with open(srt_file_path, "w", encoding='utf-8') as output_file:
            output_file.write(srt_content)
        return 0
    else:
        txt_to_append = f"<font color='red'>The total number of translation blocks ({total_blocks}) doesn't match with the total number of inserted seperators ({total_seps})"
        helper_functions.append_to_textedit(text_edit, txt_to_append)
        return 1

