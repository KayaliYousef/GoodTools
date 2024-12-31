from prep_srt import srt_to_json

def sort(srt_file_path:str, output_file=None, edit_original_file=False) -> None:
    """
    Function to sort srt timestamps by time

        Parameters:
            srt_file_path (str): The path to the srt file 
            output_file (str, optional): Path to save the sorted SRT file. If None, the sorted file will be named
                                        with '_sorted' appended to the original name. If a string were entered, this
                                        string will be the name of the sorted file
            edit_original_file (bool): If True the origial file will be overwritten, else the output will be saved in another file

        Returns:
            None

    """
    # Convert the srt file into json
    json_data = srt_to_json(srt_file_path, save_json=False)
    # Retrieve the list of JSON entries, where each entry represents information for an SRT block. Such as timestamp, block number and text
    entries = json_data.get('entries', [])
    # Sort the entries by timestamp
    sorted_entries = sorted(entries, key=lambda x: x['time_code'])
    
    # Write the contents to the SRT file
    if edit_original_file:
        fileName = srt_file_path
    else:
        if output_file is not None:
            fileName = output_file
        else:
            fileName = srt_file_path.lower().rsplit("/", 1)[-1].rsplit(".", 1)[0] + "_sorted.srt"

    # Open the output file
    with open(fileName, "w", encoding="utf-8") as f:
        # Iterate over the sorted entries
        for block_number, entry in enumerate(sorted_entries, start=1):
            # Get the timestamp and text from this entry
            time_code = entry.get('time_code', '')
            text = entry.get('text', '')

            # Create the SRT block
            srt_block = f"{block_number}\n{time_code}\n{text}\n\n"
            f.write(srt_block)


