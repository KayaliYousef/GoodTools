import re


def convert_srt_to_vtt(srt_file_path:str, output_file=None) -> None:
    """
    Convert from SRT fromat to VTT format

        Parameters:
            srt_flie_path (srt): Path to the SRT file
            output_file (str, optional): Path to save the sorted SRT file. If None, the sorted file will be named
                                        with '_sorted' appended to the original name. If a string were entered, this
                                        string will be the name of the sorted file

        Returns:
            None
    """
    # Open the SRT file
    with open(srt_file_path, "r", encoding='utf-8') as srt_file:
        # Read the contents of the file
        srt_contents = srt_file.read()

    # Replace "," with "." in time code lines to match VTT timestamp format
    pattern = r"(\d{2}:\d{2}:\d{2}),(\d{3} --> \d{2}:\d{2}:\d{2}),(\d{3}\n)"
    replace = r"\1.\2.\3"
    vtt_contents = re.sub(pattern, replace, srt_contents)

    # Remove translation block numbers
    # (?<!) negative lookbehind -- '.' matches any character --> there should be no characters before \d+\n
    vtt_contents = re.sub(r"(?<!.)\d+\n", "", vtt_contents)

    # Add the "WEBVTT" header to the VTT file
    vtt_contents = "WEBVTT\n\n" + vtt_contents

    # Write the contents to the VTT file
    if output_file is not None:
        fileName = output_file
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].split(".")
        fileName = fileName[0]+".vtt"
    with open(f"{fileName}", "w", encoding='utf-8') as vtt_file:
        vtt_file.write(vtt_contents)


def convert_vtt_to_srt(srt_file_path:str, output_file=None) -> None:
    """
    Convert from VTT fromat to SRT format

        Parameters:
            srt_flie_path (srt): Path to the SRT file
            output_file (str, optional): Path to save the sorted SRT file. If None, the sorted file will be named
                                        with '_sorted' appended to the original name. If a string were entered, this
                                        string will be the name of the sorted file

        Returns:
            None
    """
    # Open the VTT file
    with open(srt_file_path, "r", encoding='utf-8') as vtt_file:
        # Read the contents of the file
        vtt_contents = vtt_file.read()

    # Remove the "WEBVTT" header from the VTT file
    vtt_contents = re.sub(r"WEBVTT\n\n", "", vtt_contents)

    # Replace "." with "," in time code lines to match VTT timestamp format
    pattern = r"(\d{2}:\d{2}:\d{2}).(\d{3} --> \d{2}:\d{2}:\d{2}).(\d{3}\n)"
    replace = r"\1,\2,\3"
    vtt_contents = re.sub(pattern, replace, vtt_contents)

    # Add translation block numbers
    srt_contents = ""
    block_num = 1
    for block_num, block in enumerate(vtt_contents.split("\n\n"), start=1):
        if block.strip() == "": # Ignore empty lines
            continue
        srt_contents += f"{block_num}\n{block}\n\n"

    srt_contents = srt_contents.strip()

    # Write the contents to the SRT file
    if output_file is not None:
        fileName = output_file
    else:
        fileName = srt_file_path.split("/")
        fileName = fileName[-1].split(".")
        fileName = fileName[0]+".srt"
    with open(f"{fileName}", "w", encoding='utf-8') as srt_file:
        srt_file.write(srt_contents)
