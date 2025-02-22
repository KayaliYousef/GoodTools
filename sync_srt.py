from prep_srt import srt_to_json
import helper_functions as hf


def search_chunk_in_parts(text_chunk: str, text: str, entry: dict, 
                        entry_index: int, json_entries: list[dict], forward_search: bool) -> str | None:
    """
    Searches for a chunk in parts inside a text, either forward or backward.
    - Forward search splits the chunk progressively from the left.
    - Backward search splits the chunk progressively from the right.
    The search is done in the current entry first, and according to the type of the search (forward or backward) the next or previous entry will also be inspected to check if it contatins the remaining part of the chunk

        Parameters:
            text_chunk (str): Chunk of text to be searched for in the current entry then in the next
                            or previous entry
            text (str): Text from the current entry, part of the chunk could be contained in this text
            entry (dict): Python dictionary that contains information about SRT block, such as, text, timecodes, block duration...
            entry_index (int): The index of the entry inside the json_entries list
            json_entries (list[dict]): List of python dictionaries (each dict is an entry)
            forward_search (bool): Flag to determine the direction of the search, forward or backward

        Returns:
            str or None: SRT timecode with the format "hh:mm:ss,ms --> hh:mm:ss,ms" or None if search has failed
    """
    def get_part_and_index(text_chunk: str, text: str, forward_search: bool, part_len: int) -> tuple[str, int]:
        """
        Get the part of the chunk and its start index in the text.

            Notes:
                - This function is called inside a for loop where part_len is an index in a for loop that splits the text_chunk progressively samller by removing characters from the right or left according to the search direction (forward or backward)
        """
        part = text_chunk[part_len:] if forward_search else text_chunk[:part_len]
        return part, text.find(part)

    def calculate_timecodes(entry: dict, part: str, text_chunk: str, 
                            part_len: int, forward_search: bool) -> tuple[str, str, str]:
        """
        When part of the chunk is found in the text (from the current entry) using forward or backward search, then find the remaining part of the chunk (part to be searched) and calculate the timecodoes for the matching parts.

        - Forward search case: 
            - If part of the chunk matches part of the text in the forward case then the start of the matched part must align with the start of the text
            - Timecode start is the timecode start of this text (this entry)
            - Timecode end is the timecode start plus the duration of the matched part
            - In this case timecode end is final and timecode start must be corrected in the next step

        - Backward search case:
            - If part of the chunk matches part of the text in the backward case then the end of the matched part must align with the end of the text
            - Timecode end is the timecode end of this text (this entry)
            - Timecode start is the timecode end minus the duration of the matched part
            - In this case timecode start is final and timecode end must be corrected in the next step
        """
        entry_duration = entry.get('duration_in_milliseconds', 0)
        if forward_search:
            remaining_chunk = text_chunk[:part_len].strip()
            timecode_start = entry.get('time_code_start')
            part_duration = hf.calculate_timecode_by_ratio(entry_duration, text, part)
            timecode_end = hf.convert_millisec_to_timecode(
                hf.convert_time_string_to_millisec(timecode_start) + part_duration
            )
            return timecode_start, timecode_end, remaining_chunk
        else:
            remaining_chunk = text_chunk[part_len:].strip()
            timecode_end = entry.get('time_code_end')
            part_duration = hf.calculate_timecode_by_ratio(entry_duration, text, part)
            timecode_start = hf.convert_millisec_to_timecode(
                hf.convert_time_string_to_millisec(timecode_end) - part_duration
            )
            return timecode_start, timecode_end, remaining_chunk

    def handle_remaining_chunk(remaining_chunk: str, json_entries: list[dict], entry_index: int, 
                               forward_search: bool, timecode_start: str, timecode_end: str) -> str | None:
        """
        Handle remaining chunks by searching in adjacent entries.
        
        - Forward search case:
            - In this case we search in the previous entry and find the final timecode start
    
        - Backward search case
            - In this case we search in the next text and find the final timecode end
        """
        timecode = None
        if forward_search: 
            search_index = entry_index - 1
        else:
            search_index = entry_index + 1

        while search_index >= 0 and search_index < len(json_entries):
            
            searched_entry = json_entries[search_index]
            searched_text = searched_entry.get('text', '').replace("\n", " ").strip()
            searched_duration_ms = searched_entry.get('duration_in_milliseconds', 0)

            if remaining_chunk in searched_text:

                if forward_search:
                    searched_end = searched_entry.get('time_code_end')
                    remaining_duration = hf.calculate_timecode_by_ratio(searched_duration_ms, searched_text, remaining_chunk)
                    timecode_start = hf.convert_millisec_to_timecode(
                    hf.convert_time_string_to_millisec(searched_end) - remaining_duration
                    )
                    timecode = f"{timecode_start} --> {timecode_end}"
                    return timecode

                else:
                    searched_start = searched_entry.get('time_code_start')
                    remaining_duration = hf.calculate_timecode_by_ratio(searched_duration_ms, searched_text, remaining_chunk)
                    timecode_end = hf.convert_millisec_to_timecode(
                    hf.convert_time_string_to_millisec(searched_start) + remaining_duration
                    )
                    timecode = f"{timecode_start} --> {timecode_end}"
                    return timecode
                
                
            else: # searched_text is in remaining_chunk
                    
                if forward_search:
                    remaining_chunk = remaining_chunk[:len(searched_text)].strip()
                else:
                    remaining_chunk = remaining_chunk[len(searched_text):].strip()

            if forward_search: 
                search_index -= 1
            else:
                search_index += 1

    # Determine the loop direction based on search type
    loop = range(len(text_chunk)) if forward_search else range(len(text_chunk), -1, -1)

    for part_len in loop:
        part, start_index = get_part_and_index(text_chunk, text, forward_search, part_len)
        if start_index == -1:
            continue
        
        if (forward_search and start_index == 0) or (not forward_search and start_index + len(part) == len(text)):
            timecode_start, timecode_end, remaining_chunk = calculate_timecodes(entry, part, text_chunk, part_len, forward_search)
            timecode = handle_remaining_chunk(remaining_chunk, json_entries, entry_index, forward_search, timecode_start, timecode_end)
            if timecode:
                return timecode

    return None

def calculate_timecodes_for_subtext(entry: dict, text: str, text_chunk: str, start_index: int) -> str:
    """
    Handles the case where the chunk is fully contained in the text, we have here three scenario:
    
    - Scenario 1: Chunk is at the start of the text. Here the timecode start of the chunk is the timecode start of the text,
    and the timecode end of the chunk is the timecode start of the text plus the chunk duration ratio in the text 
    - Scenario 2: Chunk is at the end of the text. Here the timecode end of the chunk is the timecode end of the text,
    and the timecode start of the chunk is the timecode end minus the chunk duration ratio in the text
    - Scenario 3: Chunk is in the middle of the text. Here we find the extra text before and after the chunk in the text,
    and calculate thier durations then calculate the timecode start and end of the chunk using the durations and the timecodes start and end of the text
    
        Parameters:
            entry (dict): Python dictionary holding information about the SRT block
            text (str): The text of the srt block (same text in the entry dict)
            text_chunk (str): Chunk to be found in the text
            start_index (int): The start location of the chunk in the text
        Returns:
            str: Timecode of the chunk with the format "hh:mm:ss,ms --> hh:mm:ss,ms"
    """

    timecode_duration = entry.get('duration_in_milliseconds', 0)
    timecode_start = hf.convert_time_string_to_millisec(entry.get('time_code_start'))
    timecode_end = hf.convert_time_string_to_millisec(entry.get('time_code_end'))

    if start_index == 0: # chunk is at the start of the text
        chunk_duration = hf.calculate_timecode_by_ratio(timecode_duration, text, text_chunk)
        timecode_end = timecode_start + chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"
    
    elif start_index + len(text_chunk) == len(text): # chunk is at the end of the text
        chunk_duration = hf.calculate_timecode_by_ratio(timecode_duration, text, text_chunk)
        timecode_end = hf.convert_time_string_to_millisec(entry.get('time_code_end'))
        timecode_start = timecode_end - chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"

    else: # chunk is in the middle of the text
        text_before_chunk = text[:start_index]
        text_after_chunk = text[start_index + len(text_chunk):]
        text_before_chunk_duration = hf.calculate_timecode_by_ratio(timecode_duration, text, text_before_chunk)
        text_after_chunk_duration = hf.calculate_timecode_by_ratio(timecode_duration, text, text_after_chunk)
        timecode_start = timecode_start + text_before_chunk_duration
        timecode_end = timecode_end - text_after_chunk_duration
        return f"{hf.convert_millisec_to_timecode(timecode_start)} --> {hf.convert_millisec_to_timecode(timecode_end)}"

def calculate_timecodes_across_blocks(text_chunk: str, current_index: int, json_entries: list[dict]) -> str:
    """
    Handles the case where the text is contained in the chunk, which means that the chunk spans multiple entries.
    Here we have three scenarios:

    Scenario 1: Text starts with the start of the chunk. In this case the timecode start of the chunk is the timecode start of the text, and the timecode end of the chunk is somewhere in the next entries so we search forward.

    Scenario 2: Text ends with the end of the chunk. In this case the timecode end of the chunk is the timecode end of the text, and the timecode start of the chunk is somewhere in the previous entries so we search backwards.

    Scenario 3: Text starts in the middle of the chunk and ends also in the middle of the chunk. Here we must look forward and backward to find the remaining chunks in the next and previous entries.
    
        Parameters:
            text_chunk (str): Chunk of text to be found in the entries
            current_index (int): The index of the current entry
            json_entries (list(dict)): List of python dictionaries containing information about the block from the original SRT file

        Returns
            str: SRT timecode in the format "hh:mm:ss,ms --> hh:mm:ss,ms"
    """
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

def process_remaining_text(json_entries: list[dict], current_index: int, text_found: str, 
                            text_chunk: str, search_forward: bool) -> str:
    """
    This function is a helper for the function calculate_timecodes_across_blocks which handles the case where the text is contained in the chunk, this function will search the next or previous entries for the rest of the chunk

        Parameters:
            json_entries (list(dict)): List of python dictionaries containing information about the block from the original SRT file
            current_index (int): The index of the current entry
            text_found (str): The text of the current entry
            text_chunk (str): Chunk of text to be found in the entries
            search_forward (bool): Flag to determine the direction of the search
                                True: search in the next entries
                                False: search in the previous entries

        Returns:
            str: SRT time code in the format "hh:mm:ss,ms"
    """
    timecode = None
    if search_forward:
        search_index = 1
        # remaining_text is the text from the chunk to be searched for
        remaining_text = text_chunk[len(text_found):].strip()
    else:
        search_index = -1
        # remaining_text is the text from the chunk to be searched for
        remaining_text = text_chunk[:len(text_found)].strip()

    # keep looping until the full chunk is found or we have reached the first or last element in the entries list
    while text_found.strip() != text_chunk.strip() and current_index + search_index < len(json_entries) and current_index + search_index >= 0:

        # the next or previous entry (detemined by the search direction)
        next_entry = json_entries[current_index + search_index]
        # the text from the next or previous entry
        next_text = next_entry.get('text', '').replace("\n", " ").strip()
        # the duration in ms from the next or previous entry
        next_duration = next_entry.get('duration_in_milliseconds', 0)
        # next (or previous) text is fully (or partaly) found in the remaining text
        if next_text in remaining_text:
            # next text and remaining text are equal (end of search)
            if remaining_text.strip() == next_text.strip():
                if search_forward:
                    timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_end'))
                else:
                    timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_start'))
                break
            
            # next (or previous) text is in remaining text
            else: 
                if search_forward:
                    text_found = text_found.strip() + " " + remaining_text[len(next_text):].strip()
                    remaining_text = remaining_text[len(next_text):].strip()
                else:
                    text_found = remaining_text[len(next_text):].strip() + " " + text_found.strip()
                    remaining_text = remaining_text[:len(next_text)].strip()

                chunk_duration = hf.calculate_timecode_by_ratio(next_duration, next_text, remaining_text)

                if search_forward:
                    timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_start')) + chunk_duration
                else:
                    timecode = hf.convert_time_string_to_millisec(next_entry.get('time_code_end')) - chunk_duration


        else: # remaining text is found inside next text
            chunk_duration = hf.calculate_timecode_by_ratio(next_duration, next_text, remaining_text)
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

def find_chunk_timecode(text_chunk: str, json_entries: list[dict], current_time: int) -> str | None:
    """
    Matches a text chunk with all entries to find or calculate the timecode for this chunk. This function is being called for every block in the output srt list, where for each block the timecode is None at the start. To avoid cases where some chunks of the text may repeat over the text and in this case we will only find the first match and use its timecode, we take the current time in consideration so that we could skip an iteration if the chunk matches but the current time is larger than the time of this match. We have four main cases for matching:

    - Case 1: Chunk matches exactly with the text entry
    - Case 2: Chunk fully contained in the text entry
    - Case 3: Text entry is full contained in the chunk
    - Case 4: Chunk spans multiple entries, then we macht part of the chunk with the text and keep searching forward or backward

        Parameters:
            text_chunk (str): Input string that should be matched and found in the text
            json_entries (list[dict]): List of python dictionaries (each dict is an entry)
            current_time (int): The time of the last timecode found in milliseconds, this parameter start at 0 then gets updated each iteration in the for loop where this funciton is called

        Returns:
            str or None: Timecode with the format "hh:mm:ss,ms -> hh:mm:ss,ms" or None if search has failed an no timecode was found

    """
    text_chunk = text_chunk.replace("\n", " ").strip()
    timecode = None

    # iterate over all entries
    for entry_index, entry in enumerate(json_entries):
        text = entry.get('text', '').replace("\n", " ").strip()
        entry_time_end = entry.get('time_code_end')
        entry_time_end_in_ms = hf.convert_time_string_to_millisec(entry_time_end)
        if current_time > entry_time_end_in_ms:
            continue
        if not text:
            continue

        # Case 1: Exact match
        if text_chunk == text:
            timecode = entry.get('time_code')

            # time found is the timecode end in milliseconds
            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                # updtae the current time 
                current_time = time_found

            return timecode, current_time

        # Case 2: Chunk is fully contained within this entry
        elif text_chunk in text:
            start_index = text.find(text_chunk)
            if start_index != -1:
                timecode = calculate_timecodes_for_subtext(entry, text, text_chunk, start_index)

                # time found is the timecode end in milliseconds
                time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
                if current_time > time_found:
                    continue
                else:
                    # updtae the current time
                    current_time = time_found

                return timecode, current_time

        # Case 3: The entry text is fully contained within the chunk
        elif text in text_chunk:
            timecode = calculate_timecodes_across_blocks(text_chunk, entry_index, json_entries)

            # time found is the timecode end in milliseconds
            time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
            if current_time > time_found:
                continue
            else:
                # updtae the current time
                current_time = time_found

            return timecode, current_time

        # Case 4: Chunk spans multiple entries, where part of the chunk is contained in the entry
        # in this case we do a forward search and a backward search to find the part of the chunk
        # that is contained in the entry, then according to the search direction we look for the 
        # remaining part of the chunk in the next entry or in the previous entry
        else:
            timecode = search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search=False)

            if timecode: 
                # time found is the timecode end in milliseconds
                time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
                if current_time > time_found:
                    continue
                else:
                    # updtae the current time
                    current_time = time_found

                return timecode, current_time
            
            timecode = search_chunk_in_parts(text_chunk, text, entry, entry_index, json_entries, forward_search=True)

            if timecode: 
                # time found is the timecode end in milliseconds
                time_found = hf.convert_time_string_to_millisec(timecode.split("-->")[1].strip())
                if current_time > time_found:
                    continue
                else:
                    # updtae the current time
                    current_time = time_found

                return timecode, current_time
                    
    # return None  # Fallback for unmatched chunks

def sync(srt_flie, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations, output_file=None):
    # Main Processing
    json_data = srt_to_json(srt_flie, save_json=False)
    entries = json_data.get('entries', [])
    text = ' '.join(line.strip() for line in hf.clean_srt(srt_flie).splitlines())
    output_srt_list = []
    block_number = 1

    # keep looping until we reach the end of the text
    while text:
        # split the text into three part. line1, line2, and the remaining of the text
        # line1 and line2 lengths should be between max_char_per_line and min_char_per_line
        # if hashtag_found is True this function will return line1 and line2 in the variable line1 without the '##'
        line1, line2, extra_text, hashtag_found = hf.split_text_with_max_char(text, max_char_per_line, min_char_per_line, split_at_punctuation, punctuations)

        # update the text variable with the remaining text
        text = extra_text
        # hashtag symbol '##' is found 
        if hashtag_found:
            block_text = f"{line1.strip()}"
        else:
            block_text = f"{line1.strip()}\n{line2.strip()}"

        output_srt_list.append({
            "block_number": block_number,
            "time_code": None,
            "text": block_text,
        })

        block_number += 1

        # add the hashtag in a seperated block
        if hashtag_found: 
            output_srt_list.append({
                "block_number": block_number,
                "time_code": None,
                "text": "##",
            })
            block_number += 1

    current_time = 0
    for output in output_srt_list:
        if output["time_code"] is None:
            text_chunk = output['text'].replace("\n", " ").strip()
            output["time_code"], current_time = find_chunk_timecode(text_chunk, entries, current_time)

    if output_file is not None:
        output_name = output_file
    else:
        output_name = srt_flie.rsplit(".", 1)[0] + "_out.srt"
    with open(output_name, "w", encoding='utf-8') as f:
        for block in output_srt_list:
            f.write(f"{block['block_number']}\n{block['time_code']}\n{block['text']}\n\n")

if __name__ == "__main__":
    sync("input.srt", 42, 30, False, None, "output.srt")