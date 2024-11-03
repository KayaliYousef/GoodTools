import re
import helper_functions

def correct_intersected_blocks(srt_file):
    modified_srt = []
    corrected_srt_timescodes = []
    buffer = 5 # in ms

    with open(srt_file, 'r', encoding='utf-8') as f:
        srt_content = f.readlines()

    srt_timecodes = [line for line in srt_content if "-->" in line]
    for i in range(len(srt_timecodes)-1):
        current_block_start, current_block_end = helper_functions.convert_timecode_to_millisec(srt_timecodes[i])
        next_block_start, next_block_end = helper_functions.convert_timecode_to_millisec(srt_timecodes[i+1])

        # add the start of the first time code
        if i == 0: corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_start))

        # check if timing error between two blocks
        if current_block_end > next_block_start:
            diff = ((current_block_end - next_block_start) // 2) 
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_end - diff - buffer))
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_start + diff + buffer))
        else:
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(current_block_end))
            corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_start))

        # add end of the last time code
        if i == len(srt_timecodes)-2: corrected_srt_timescodes.append(helper_functions.convert_millisec_to_timecode(next_block_end))

    # pairing adjacent elements to reconstruct timecodes
    corrected_srt_timescodes = [f"{corrected_srt_timescodes[i]} --> {corrected_srt_timescodes[i + 1]}" for i in range(0, len(corrected_srt_timescodes) - 1, 2)]

    # replace rewrite timecodes to the srt list
    append_counter = 0
    for line in srt_content:
        if "-->" in line:
            modified_srt.append(corrected_srt_timescodes[append_counter].strip())
            append_counter += 1
        else:
            modified_srt.append(line.strip())

    with open(srt_file, "w", encoding='utf-8') as f:
            for line in modified_srt:
                f.write(f"{line}\n")


