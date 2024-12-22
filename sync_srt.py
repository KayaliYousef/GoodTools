from prep_srt import srt_to_json, split_in_half
from correct_intersected_srt import correct_intersected_blocks
import helper_functions as hf

# Constants
BREAKERS = [".", ",", "?", ":", "!"]
MAX_CHAR_PER_LINE = 42
MIN_CHAR_PER_LINE = 21

# Helper Functions
def find_first_breaker(text: str, breakers: list):
    """Finds the first occurrence of a breaker in the text and handles special cases."""
    for i, char in enumerate(text):
        if char in breakers:
            # Handle specific cases
            if char == '.' and i + 2 < len(text) and text[i + 1:i + 3] == '..':
                return i + 2, '...'
            elif char == '?' and i + 1 < len(text):
                if text[i + 1] in ['!', '?']:
                    return i + 1, text[i + 1]
            return i, char
    return len(text) - 1, ''  # Default to end of text if no breaker found

def split_text_by_index(text, index):
    """Splits text into two parts at the given index."""
    return text[:index + 1], text[index + 1:]

def split_text_by_whitespace(text, max_index):
    """Finds the last whitespace before max_index to split the text."""
    whitespace_index = text[:max_index].rfind(' ')
    return text[:whitespace_index], text[whitespace_index + 1:]

def calculate_timecode_by_ratio(timecode_duration, full_text, text_chunk):
    """Calculates the proportional duration for a text chunk."""
    return int(len(text_chunk) / len(full_text) * timecode_duration)

def find_chunk_timecode(text_chunk, json_entries):
    """Finds or calculates the timecode for a given text chunk, handling cases where the chunk spans multiple entries."""
    text_chunk = text_chunk.replace("\n", " ").strip()

    for entry_index, entry in enumerate(json_entries):
        text = entry.get('text', '').replace("\n", " ").strip()
        if not text:
            continue

        # Case 1: Exact match
        if text_chunk == text:
            return entry.get('time_code')

        # Case 2: Chunk is fully contained within this entry
        if len(text) > len(text_chunk):
            start_index = text.find(text_chunk)
            if start_index != -1:
                return calculate_timecodes_for_subtext(entry, text, text_chunk, start_index)

        # Case 3: The entry text is fully contained within the chunk
        if text in text_chunk:
            return calculate_timecodes_across_blocks(text_chunk, entry_index, json_entries)

        # Case 4: Chunk spans multiple entries
        for part_len in range(len(text_chunk), 0, -1):
            part = text_chunk[:part_len]
            start_index = text.find(part)
            if start_index != -1 and start_index + len(part) == len(text):  # Part ends at the end of this entry
                remaining_chunk = text_chunk[part_len:].strip()
                timecode_end = entry.get('time_code_end')
                duration_ms = entry.get('duration_in_milliseconds', 0)
                part_duration = calculate_timecode_by_ratio(duration_ms, text, part)
                timecode_start = hf.convert_millisec_to_timecode(
                    hf.convert_time_string_to_millisec(timecode_end) - part_duration
                )

                # Look for the remaining chunk in the next entry
                if entry_index + 1 < len(json_entries):
                    next_entry = json_entries[entry_index + 1]
                    next_text = next_entry.get('text', '').replace("\n", " ").strip()
                    if remaining_chunk in next_text:
                        next_duration_ms = next_entry.get('duration_in_milliseconds', 0)
                        next_start = next_entry.get('time_code_start')
                        remaining_duration = calculate_timecode_by_ratio(
                            next_duration_ms, next_text, remaining_chunk
                        )
                        timecode_end = hf.convert_millisec_to_timecode(
                            hf.convert_time_string_to_millisec(next_start) + remaining_duration
                        )
                        return f"{timecode_start} --> {timecode_end}"

    return None  # Fallback for unmatched chunks


def calculate_timecodes_for_subtext(entry, text, text_chunk, start_index):
    """Calculates timecodes when a chunk is found within a text entry."""
    timecode_duration = entry.get('duration_in_milliseconds', 0)
    timecode_start = hf.convert_time_string_to_millisec(entry.get('time_code_start'))
    timecode_end = hf.convert_time_string_to_millisec(entry.get('time_code_end'))

    if start_index == 0: # chunk is at the start of the text
        chunk_duration = calculate_timecode_by_ratio(timecode_duration, text, text_chunk)
        timecode_end = timecode_start + chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"
    
    elif start_index + len(text_chunk) == len(text): # chunk is at the end of the text
        chunk_duration = calculate_timecode_by_ratio(timecode_duration, text, text_chunk)
        timecode_end = hf.convert_time_string_to_millisec(entry.get('time_code_end'))
        timecode_start = timecode_end - chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"

    else: # chunk is in the middle of the text
        text_before_chunk = text[:start_index]
        text_after_chunk = text[start_index + len(text_chunk):]
        text_before_chunk_duration = ( calculate_timecode_by_ratio(timecode_duration, text, text_before_chunk))
        text_after_chunk_duration = ( calculate_timecode_by_ratio(timecode_duration, text, text_after_chunk))
        timecode_start = timecode_start + text_before_chunk_duration
        timecode_end = timecode_end - text_after_chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"

def calculate_timecodes_across_blocks(text_chunk, current_index, json_entries):
    """Handles cases where a text chunk spans across multiple blocks."""
    entry = json_entries[current_index]
    text = entry.get('text', '').replace("\n", " ").strip()

    next_entry = json_entries[current_index + 1]
    next_text = next_entry.get('text', '').replace("\n", " ").strip()
    next_duration = next_entry.get('duration_in_milliseconds', 0)

    previous_entry = json_entries[current_index - 1]
    previous_text = previous_entry.get('text', '').replace("\n", " ").strip()
    previous_duration = previous_entry.get('duration_in_milliseconds', 0)

    text_index = text_chunk.find(text)

    if text_index == 0: # text is at the start of the chunk
        timecode_start = entry.get('time_code_start')
        remaining_text = text_chunk[len(text):].strip()
        chunk_duration = calculate_timecode_by_ratio(next_duration, next_text, remaining_text)
        timecode_end = hf.convert_time_string_to_millisec(next_entry.get('time_code_start')) + chunk_duration
        return f"{timecode_start} --> {hf.convert_millisec_to_timecode(timecode_end)}"
    
    elif text_index + len(text) == len(text_chunk): # text is at the end of the chunk
        timecode_end = entry.get('time_code_end')
        remaining_text = text_chunk[:len(text)].strip()
        chunk_duration = calculate_timecode_by_ratio(previous_duration, previous_text, remaining_text)
        timecode_start = hf.convert_time_string_to_millisec(previous_entry.get('time_code_end')) - chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {timecode_end}"

    return "Time code not found across blocks"

# Main Processing
json_data = srt_to_json("input.srt", save_json=False)
entries = json_data.get('entries', [])
text = ' '.join(line.strip() for line in hf.clean_srt("english.srt").splitlines())
output_srt_list = []

block_number = 1
while text:
    index, breaker = find_first_breaker(text, BREAKERS)
    text_until_breaker, rest_of_text = split_text_by_index(text, index)
    text = rest_of_text.strip()

    while len(text_until_breaker) < MIN_CHAR_PER_LINE and breaker not in {'.', '...', '?'}:
        index, breaker = find_first_breaker(text, BREAKERS)
        next_chunk, text = split_text_by_index(text, index)
        text_until_breaker += " " + next_chunk.strip()

    if len(text_until_breaker) <= MAX_CHAR_PER_LINE:
        output_srt_list.append({
            "block_number": block_number,
            "time_code": find_chunk_timecode(text_until_breaker, entries),
            "text": text_until_breaker.strip(),
        })
    elif len(text_until_breaker) <= MAX_CHAR_PER_LINE * 2:
        output_srt_list.append({
            "block_number": block_number,
            "time_code": find_chunk_timecode(text_until_breaker, entries),
            "text": split_in_half(text_until_breaker),
        })
    else:
        part1, part2 = split_text_by_whitespace(text_until_breaker, MAX_CHAR_PER_LINE * 2)
        output_srt_list.append({
            "block_number": block_number,
            "time_code": find_chunk_timecode(part1, entries),
            "text": split_in_half(part1),
        })
        text = part2.strip() + " " + text.strip()

    block_number += 1

with open("output.srt", "w", encoding='utf-8') as f:
    for block in output_srt_list:
        f.write(f"{block['block_number']}\n{block['time_code']}\n{block['text']}\n\n")

correct_intersected_blocks("output.srt")
