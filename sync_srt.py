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

# def search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search):
#     """
#     forward_search: split chunk progressively from the left and match the remaining part with the text
#         example: chunk = "This is random text" --> "his is random text" --> "is is random text" ...
#     backward_search: split chunk progressivley from the right and match the remaining part with the text
#         example: chunk = "This is random text" --> "This is random tex" --> "This is random te" ...
#     """
#     if forward_search:
#         direction = 1
#         loop = range(len(text_chunk))
#     else:
#         direction = -1
#         loop = range(len(text_chunk), 0, direction)

#     for part_len in loop:
#         if forward_search:
#             part = text_chunk[part_len:]
#         else:
#             part = text_chunk[:part_len]
#         start_index = text.find(part)
#         if start_index != -1 and start_index + len(part) == len(text) and not forward_search:  # Part ends at the end of this entry
#             remaining_chunk = text_chunk[part_len:].strip()
#             timecode_end = entry.get('time_code_end')
#             entry_duration = entry.get('duration_in_milliseconds', 0)
#             part_duration = calculate_timecode_by_ratio(entry_duration, text, part)
#             timecode_start = hf.convert_millisec_to_timecode(
#                 hf.convert_time_string_to_millisec(timecode_end) - part_duration
#             )
#         elif start_index != -1 and start_index == 0 and forward_search: # Part start with the start of this entry
#             remaining_chunk = text_chunk[:part_len].strip()
#             timecode_start = entry.get('time_code_start')
#             entry_duration = entry.get('duration_in_milliseconds', 0)
#             part_duration = calculate_timecode_by_ratio(entry_duration, text, part)
#             timecode_end = hf.convert_millisec_to_timecode(
#                 hf.convert_time_string_to_millisec(timecode_start) + part_duration
#             )
#             # Look for the remaining chunk in the next entry
#             if entry_index + 1 < len(json_entries) and not forward_search:
#                 next_entry = json_entries[entry_index + 1]
#                 next_text = next_entry.get('text', '').replace("\n", " ").strip()
#                 if remaining_chunk in next_text:
#                     next_duration_ms = next_entry.get('duration_in_milliseconds', 0)
#                     next_start = next_entry.get('time_code_start')
#                     remaining_duration = calculate_timecode_by_ratio(next_duration_ms, next_text, remaining_chunk)
#                     timecode_end = hf.convert_millisec_to_timecode(
#                         hf.convert_time_string_to_millisec(next_start) + remaining_duration
#                     )
#                     return f"{timecode_start} --> {timecode_end}"

#             elif entry_index - 1 > 0 and forward_search:
#                 previous_entry = json_entries[entry_index - 1]
#                 previous_text = previous_entry.get('text', '').replace("\n", " ").strip()
#                 if remaining_chunk in previous_text:
#                     previous_duration_ms = previous_entry.get('duration_in_milliseconds')
#                     previous_end = previous_entry.get('time_code_end')
#                     remaining_duration = calculate_timecode_by_ratio(previous_duration_ms, previous_text, remaining_chunk)
#                     timecdoe_start = hf.convert_millisec_to_timecode(
#                         hf.convert_time_string_to_millisec(previous_end) - remaining_duration
#                     )
#                     return f"{timecode_start} --> {timecode_end}"
#     return None


def search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search):
    """
    Searches for a chunk in parts of the text, either forward or backward.
    - Forward search splits the chunk progressively from the left.
    - Backward search splits the chunk progressively from the right.
    """
    def get_part_and_index(text_chunk, forward_search, part_len):
        """Get the part of the chunk and its start index in the text."""
        part = text_chunk[part_len:] if forward_search else text_chunk[:part_len]
        return part, text.find(part)

    def calculate_timecodes(entry, part, text_chunk, part_len, forward_search):
        """Calculate timecodes for matching parts."""
        entry_duration = entry.get('duration_in_milliseconds', 0)
        if forward_search:
            remaining_chunk = text_chunk[:part_len].strip()
            timecode_start = entry.get('time_code_start')
            part_duration = calculate_timecode_by_ratio(entry_duration, text, part)
            timecode_end = hf.convert_millisec_to_timecode(
                hf.convert_time_string_to_millisec(timecode_start) + part_duration
            )
            return timecode_start, timecode_end, remaining_chunk
        else:
            remaining_chunk = text_chunk[part_len:].strip()
            timecode_end = entry.get('time_code_end')
            part_duration = calculate_timecode_by_ratio(entry_duration, text, part)
            timecode_start = hf.convert_millisec_to_timecode(
                hf.convert_time_string_to_millisec(timecode_end) - part_duration
            )
            return timecode_start, timecode_end, remaining_chunk

    def handle_remaining_chunk(remaining_chunk, json_entries, entry_index, forward_search, timecode_start, timecode_end):
        """Handle remaining chunks by searching in adjacent entries."""
        if forward_search and entry_index - 1 >= 0:  # Search in the previous entry
            previous_entry = json_entries[entry_index - 1]
            previous_text = previous_entry.get('text', '').replace("\n", " ").strip()
            if remaining_chunk in previous_text:
                previous_duration_ms = previous_entry.get('duration_in_milliseconds', 0)
                previous_end = previous_entry.get('time_code_end')
                remaining_duration = calculate_timecode_by_ratio(previous_duration_ms, previous_text, remaining_chunk)
                timecode_start = hf.convert_millisec_to_timecode(
                    hf.convert_time_string_to_millisec(previous_end) - remaining_duration
                )
                return f"{timecode_start} --> {timecode_end}"
        elif not forward_search and entry_index + 1 < len(json_entries):  # Search in the next entry
            next_entry = json_entries[entry_index + 1]
            next_text = next_entry.get('text', '').replace("\n", " ").strip()
            if remaining_chunk in next_text:
                next_duration_ms = next_entry.get('duration_in_milliseconds', 0)
                next_start = next_entry.get('time_code_start')
                remaining_duration = calculate_timecode_by_ratio(next_duration_ms, next_text, remaining_chunk)
                timecode_end = hf.convert_millisec_to_timecode(
                    hf.convert_time_string_to_millisec(next_start) + remaining_duration
                )
                return f"{timecode_start} --> {timecode_end}"
        return None

    # Determine the loop direction based on search type
    loop = range(len(text_chunk)) if forward_search else range(len(text_chunk), 0, -1)

    for part_len in loop:
        part, start_index = get_part_and_index(text_chunk, forward_search, part_len)
        if start_index == -1:
            continue

        if (forward_search and start_index == 0) or (not forward_search and start_index + len(part) == len(text)):
            timecode_start, timecode_end, remaining_chunk = calculate_timecodes(entry, part, text_chunk, part_len, forward_search)
            result = handle_remaining_chunk(remaining_chunk, json_entries, entry_index, forward_search, timecode_start, timecode_end)
            if result:
                return result

    return None


def find_chunk_timecode(text_chunk, json_entries, current_time):
    """Finds or calculates the timecode for a given text chunk, handling cases where the chunk spans multiple entries."""
    text_chunk = text_chunk.replace("\n", " ").strip()
    timecode = None

    for entry_index, entry in enumerate(json_entries):
        text = entry.get('text', '').replace("\n", " ").strip()
        if not text:
            continue

        # Case 1: Exact match
        if text_chunk == text:
            timecode = entry.get('time_code')

            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                current_time = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())

            return timecode, current_time

        # Case 2: Chunk is fully contained within this entry
        if len(text) > len(text_chunk) and text_chunk in text:
            start_index = text.find(text_chunk)
            if start_index != -1:
                timecode = calculate_timecodes_for_subtext(entry, text, text_chunk, start_index)

                time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
                if current_time > time_found:
                    continue
                else:
                    current_time = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())

                return timecode, current_time

        # Case 3: The entry text is fully contained within the chunk
        if text in text_chunk:
            timecode = calculate_timecodes_across_blocks(text_chunk, entry_index, json_entries)

            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                current_time = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())

            return timecode, current_time

        # Case 4: Chunk spans multiple entries, we do a forward search or a backward search
        timecode = search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search=False)

        if timecode: 
            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                current_time = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())

            return timecode, current_time
        

        timecode = search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search=True)

        if timecode: 
            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                current_time = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())

            return timecode, current_time
                    
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


def process_remaining_text(json_entries, current_index, text_found, text_chunk, search_forward):
    timecode = None
    if search_forward:
        search_index = 1
        remaining_text = text_chunk[len(text_found):].strip()
    else:
        search_index = -1
        remaining_text = text_chunk[:len(text_found)].strip()

    while text_found.strip() != text_chunk.strip():
        
        next_entry = json_entries[current_index + search_index]
        next_text = next_entry.get('text', '').replace("\n", " ").strip()
        next_duration = next_entry.get('duration_in_milliseconds', 0)
        if next_text in remaining_text: # next text is fully (or partaly) found in the remaining text
            if search_forward:
                text_found = text_found.strip() + " " + remaining_text[len(next_text):].strip()
                remaining_text = remaining_text[len(next_text):]
            else:
                text_found = remaining_text[len(next_text):].strip() + " " + text_found.strip()
                remaining_text = remaining_text[:len(next_text)]

            chunk_duration = calculate_timecode_by_ratio(next_duration, next_text, remaining_text)

            if search_forward:
                timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_start')) + chunk_duration
            else:
                timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_end')) - chunk_duration


        else: # remaining text is found inside next text
            chunk_duration = calculate_timecode_by_ratio(next_duration, next_text, remaining_text)
            if search_forward:
                timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_start')) + chunk_duration
            else:
                timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_end')) - chunk_duration
            break

        if search_forward:
            search_index += 1
        else:
            search_index -= 1

    return hf.convert_millisec_to_timecode(timecode)

def calculate_timecodes_across_blocks(text_chunk, current_index, json_entries):
    """Handles cases where a text chunk spans across multiple blocks."""
    entry = json_entries[current_index]
    text = entry.get('text', '').replace("\n", " ").strip()
    text_index = text_chunk.find(text)

    if text_index == 0: # text is at the start of the chunk
        timecode_start = entry.get('time_code_start')
        timecode_end = process_remaining_text(json_entries, current_index, text, text_chunk, search_forward=True)
        return f"{timecode_start} --> {timecode_end}"
    
    elif text_index + len(text) == len(text_chunk): # text is at the end of the chunk
        timecode_end = entry.get('time_code_end')
        timecode_start = process_remaining_text(json_entries, current_index, text, text_chunk, search_forward=False)
        return f"{timecode_start} --> {timecode_end}" 

    else: # text is in the middle of the chunk
        timecode_start = process_remaining_text(json_entries, current_index, text, text_chunk[:text_index].strip(), search_forward=False)
        timecode_end = process_remaining_text(json_entries, current_index, text, text_chunk[text_index + len(text):].strip(), search_forward=True)
        return f"{timecode_start} --> {timecode_end}"

# Main Processing
json_data = srt_to_json("input.srt", save_json=False)
entries = json_data.get('entries', [])
text = ' '.join(line.strip() for line in hf.clean_srt("input.srt").splitlines())
output_srt_list = []

block_number = 1
while text:
    # find first occurance of a breaker in the current text
    index, breaker = find_first_breaker(text, BREAKERS)
    # split the text at the found breaker
    text_until_breaker, rest_of_text = split_text_by_index(text, index)
    # text after breaker is the new text
    text = rest_of_text.strip()

    # if text until breaker is too short, keep taking chunk form the rest of the text unitl text_until_breaker larger than threshold
    while len(text_until_breaker) < MIN_CHAR_PER_LINE and breaker not in {'.', '...', '?'}:
        index, breaker = find_first_breaker(text, BREAKERS)
        next_chunk, text = split_text_by_index(text, index)
        text_until_breaker += " " + next_chunk.strip()

    # text until breaker fits in a single line
    if len(text_until_breaker) <= MAX_CHAR_PER_LINE:
        output_srt_list.append({
            "block_number": block_number,
            # "time_code": find_chunk_timecode(text_until_breaker, entries),
            "time_code": None,
            "text": text_until_breaker.strip(),
        })
    # text until breaker should be fitted in two lines
    elif len(text_until_breaker) <= MAX_CHAR_PER_LINE * 2:
        output_srt_list.append({
            "block_number": block_number,
            # "time_code": find_chunk_timecode(text_until_breaker, entries),
            "time_code": None,
            "text": split_in_half(text_until_breaker),
        })
    # text until breaker doesn't fit in two lines so we fill two lines and append the rest to the rest of the text 
    else:
        part1, part2 = split_text_by_whitespace(text_until_breaker, MAX_CHAR_PER_LINE * 2)
        output_srt_list.append({
            "block_number": block_number,
            # "time_code": find_chunk_timecode(part1, entries),
            "time_code": None,
            "text": split_in_half(part1),
        })
        text = part2.strip() + " " + text.strip()

    block_number += 1

current_time = 0
for output in output_srt_list:
    if output["time_code"] is None:
        text_chunk = output['text'].replace("\n", " ").strip()
        output["time_code"], current_time = find_chunk_timecode(text_chunk, entries, current_time)

with open("output.srt", "w", encoding='utf-8') as f:
    for block in output_srt_list:
        f.write(f"{block['block_number']}\n{block['time_code']}\n{block['text']}\n\n")

# correct_intersected_blocks("output.srt")

