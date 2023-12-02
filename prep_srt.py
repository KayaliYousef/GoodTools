import re
import json
import copy
import random

import helper_functions

def srt_to_json(srt_file_path:str, text_len:int) -> None:
    # Read the SRT file

    with open(srt_file_path, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    # Split the content into blocks based on the blank lines
    srt_blocks = re.split(r'\n\s*\n', srt_content.strip())

    # Initialize a list to store JSON entries
    json_entries = []
    weights = []

    total_duration = 0  # Variable to store the total duration of the subtitle file
    total_characters = 0  # Variable to store the total number of characters in the subtitle file

    for block in srt_blocks:
        # Extract block number, time code, and text using regex
        match = re.match(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+)', block, re.DOTALL)

        if match:
            block_number, start_time, end_time, text = match.groups()
            num_characters = len(text)
            total_characters += num_characters

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
            num_characters = len(text)
            weight = (num_characters / total_characters) * 100
            weights.append(weight)

            # Create a dictionary for the JSON entry
            entry = {
                'block_number': int(block_number),
                'time_code': f'{start_time} --> {end_time}',
                'text': text.strip(),
                'num_characters': num_characters,
                'weight' : weight,
                'duration': duration
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

    # Save the JSON data to a file
    json_file_path = srt_file_path.replace('.srt', '_output.json')
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=2)


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

def divide_text_with_weights(text, weights):
    total_weights = sum(weights)
    percentages = [weight / total_weights for weight in weights]

    chunks = []
    start_index = 0
    options = ["add", "add"]

    for percentage in percentages:
        # Find the index where the split should occur based on white spaces
        end_index = start_index + int(percentage * len(text))
        if random.choice(options) == "add":
            while end_index < len(text) and not text[end_index].isspace():
                end_index += 1
        else:
            while end_index < len(text) and not text[end_index].isspace():
                end_index -= 1

        chunks.append(text[start_index:end_index].strip())
        start_index = end_index

    # Adding the remaining text, if any, to the last chunk
    if start_index < len(text):
        chunks[-1] += text[start_index:]

    return chunks

def reconstruct_srt_from_json_and_txt(json_file_path:str, txt_file_path:str, text_edit:object) -> None:
    # Load the JSON data
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    # Read the text file
    with open(txt_file_path, "r", encoding='utf-8') as file:
        text_content = file.read()
    
    weights = json_data["additional_info"]["weights_list"]
    # dict to save the translation into
    json_data_copy = copy.deepcopy(json_data)

    text_chuncks = divide_text_with_weights(text_content, weights)
    for text_block, json_entry in zip(text_chuncks, json_data_copy["entries"]):
        json_entry["text"] = text_block.strip()

    # for old_entry, new_entry in zip(json_data["entries"], json_data_copy["entries"]):
    #     old_text = old_entry["text"]
    #     new_text = new_entry["text"]
    #     if '\n' in old_text.strip():
    #         ratio = old_text.strip().split('\n')
    #         ratio = len(ratio[0].split())
    #         index = 0
    #         tracker = 0
    #         for i, letter in enumerate(new_text):
    #             if letter == " ":
    #                 tracker += 1
    #                 index = i
    #             if tracker == ratio:
    #                 break
    #         new_text_with_linebreak = new_text[:index]+"\n"+new_text[index+1:]
    #         new_entry["text"] = new_text_with_linebreak



    srt_content = json_to_srt(json_data_copy)

    # Save the result to a new file
    srt_file_path = txt_file_path.rsplit(".", 1)[0]+"_new.srt"
    with open(srt_file_path, "w", encoding='utf-8') as output_file:
        output_file.write(srt_content)

