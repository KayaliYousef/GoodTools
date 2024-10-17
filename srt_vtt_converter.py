import re


def convert_srt_to_vtt(srt_file_path:str) -> None:
    # Open the SRT file
    with open(srt_file_path, "r", encoding='utf-8') as srt_file:
        # Read the contents of the file
        srt_contents = srt_file.read()

    # Replace "," with "." in time code lines to match VTT timestamp format
    pattern = r"(\d{2}:\d{2}:\d{2}),(\d{3} --> \d{2}:\d{2}:\d{2}),(\d{3}\n)"
    replace = r"\1.\2.\3"
    vtt_contents = re.sub(pattern, replace, srt_contents)

    # Remove translation block numbers
    vtt_contents = re.sub(r"(?<!.)\d+\n", "", vtt_contents)

    # Add the "WEBVTT" header to the VTT file
    vtt_contents = "WEBVTT\n\n" + vtt_contents

    # Write the contents to the VTT file
    fileName = srt_file_path.split("/")
    fileName = fileName[-1].split(".")
    fileName = fileName[0]
    with open(f"{fileName}.vtt", "w", encoding='utf-8') as vtt_file:
        vtt_file.write(vtt_contents)


def convert_vtt_to_srt(srt_file_path:str) -> None:
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
    for block in vtt_contents.split("\n\n"):
        if block.strip() == "": # Ignore empty lines
            continue
        srt_contents += f"{block_num}\n{block}\n\n"
        block_num += 1

    srt_contents = srt_contents.strip()

    # Write the contents to the SRT file
    fileName = srt_file_path.split("/")
    fileName = fileName[-1].split(".")
    fileName = fileName[0]
    with open(f"{fileName}.srt", "w", encoding='utf-8') as srt_file:
        srt_file.write(srt_contents)
