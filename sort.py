from prep_srt import srt_to_json

def sort(srt_file_path:str, output_file=None, edit_original_file=False):
    json_data = srt_to_json(srt_file_path, save_json=False)
    entries = json_data.get('entries', [])
    sorted_entries = sorted(entries, key=lambda x: x['time_code'])
    
    block_number = 1

    # Write the contents to the SRT file
    if edit_original_file:
        fileName = srt_file_path
    else:
        if output_file is not None:
            fileName = output_file
        else:
            fileName = srt_file_path.lower().rsplit("/", 1)[-1].rsplit(".", 1)[0] + "_sorted.srt"

    with open(fileName, "w", encoding="utf-8") as f:
        for entry in sorted_entries:

            time_code = entry.get('time_code', '')
            text = entry.get('text', '')

            # Create the SRT block
            srt_block = f"{block_number}\n{time_code}\n{text}\n\n"
            f.write(srt_block)
            block_number += 1


