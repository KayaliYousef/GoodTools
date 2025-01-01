import helper_functions

def correct_intersected_blocks(srt_file: str, buffer=5) -> None:
    """
    Corret the timing of SRT blocks, if two adjacent blocks are overlapping this function will re-calculate the timing for those blocks seperating them adding a buffer in milliseconds between them

        Parameters:
            srt_file (str): Path to the SRT file
            buffer (int): Time in millisecond to add between two intersecting blocks after seperating them

        Returns:
            None
    """
    # list to save corrected time stamp, at first the time stamps will be saved in parts
    # [block_1_timestamp_start, block_1_time_stamp_end, block_2_time_stamp_start, ...]
    # then the time stamps will be paried together inside the list
    corrected_srt_timescodes = []

    # Read the SRT files
    with open(srt_file, 'r', encoding='utf-8') as f:
        srt_content = f.readlines()

    # extract the timecodes for the SRT file
    srt_timecodes = [line for line in srt_content if "-->" in line]
    # iterate over the timecodes
    for i in range(len(srt_timecodes)-1):
        # get the start and end of the current SRT block in milliseconds
        current_block_start, current_block_end = helper_functions.convert_timecode_to_millisec(srt_timecodes[i])
        # get the start and end of the next SRT block in milliseconds
        next_block_start, next_block_end = helper_functions.convert_timecode_to_millisec(srt_timecodes[i+1])

        # add the start of the first time code to the output list (first time stamp can't be wrong)
        if i == 0: corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_start))

        # check for timing error (overlapping) between two blocks
        # the end of the current block is larger than the start of the next block
        if current_block_end > next_block_start:
            # get the difference between the end of the current block and the start of the next block then halve it
            diff = ((current_block_end - next_block_start) // 2) 
            # correct the time stamps then add them to the output list
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_end - diff - buffer))
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_start + diff + buffer))
        # the end of the current block is smaller or equal the start of the next block (no error case)
        else:
            # add the time stamps to the output list
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_end))
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_start))

        # add end of the last time code
        if i == len(srt_timecodes)-2: corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_end))

    # pairing adjacent elements to reconstruct timecodes
    corrected_srt_timescodes = [f"{corrected_srt_timescodes[i]} --> {corrected_srt_timescodes[i + 1]}" for i in range(0, len(corrected_srt_timescodes) - 1, 2)]

    # List to save the modified SRT content
    updated_srt_content = []

    # Counter to track the position in corrected timecodes
    timecode_index = 0

    # Iterate through the original SRT content
    for line in srt_content:
        line = line.strip()  # Strip whitespace from the line once
        if "-->" in line:  # Check if the line contains a timecode
            updated_srt_content.append(corrected_srt_timescodes[timecode_index].strip())
            timecode_index += 1
        else:
            updated_srt_content.append(line)

    with open(srt_file, "w", encoding='utf-8') as f:
            for line in updated_srt_content:
                f.write(f"{line}\n")


