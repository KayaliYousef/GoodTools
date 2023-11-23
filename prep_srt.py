import re
import json

def srt_to_json(srt_file_path):
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
        'total_characters': total_characters,
        'average_characters_per_second': average_characters_per_second,
        'total_blocks': len(json_entries)
    }

    # Combine JSON entries and additional information
    result = {'entries': json_entries, 'additional_info': additional_info}

    # Save the JSON data to a file
    json_file_path = srt_file_path.replace('.srt', '_output.json')
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=2)

    print(f'Successfully converted {srt_file_path} to JSON. Output saved to {json_file_path}')

# Example usage:
srt_file_path = 'القضية/Watch How CNN Profits from Genocide in Gaza.en.srt'
srt_to_json(srt_file_path)
