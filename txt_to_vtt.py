# this script converts txt (translated) to vtt using the timing information from the vtt

import re
import glob

def get_files(extension:str) -> list[str]:
    """
    Retrieves a list of files with the specified extension from the current working directory.

        Parameters:
            extension (str): The file extension to search for (e.g., 'txt', 'csv', 'jpg').
                            Do not include a leading period (e.g., use 'txt' instead of '.txt').

        Returns:
            list[str]: A list of file names that have the specified extension.
                    Returns an empty list if no matching files are found.

        Example:
            >>> get_files("txt")
            ['file1.txt', 'notes.txt']

        Notes:
            - The search is case-sensitive; files with uppercase extensions (e.g., '.TXT') will
            not be matched unless specified exactly.
            - The function searches only in the current working directory.
    """
    files = []
    for file in glob.glob("*."+extension):
        files.append(file)
    return files

def run(vtt_file_path:str, txt_file_path:str, output_file_name:str) -> None:
    # Read the SRT file
    with open(vtt_file_path, 'r', encoding='utf-8') as file:
        vtt_content = file.readlines()

    # make sure the the srt lines don't have extry white spaces after each line
    vtt_content = [line.strip() for line in vtt_content]
    vtt_content = "\n".join(vtt_content)

    # Split the content into blocks based on the blank lines and remove the first block (WEBVTT line) 
    vtt_blocks = re.split(r'\n\s*\n', vtt_content.strip())[1:]
    # Remove the text from each block keeping only the timecodes
    vtt_timecodes = [block.split("\n")[0] for block in vtt_blocks if "\n" in block]

    # read the txt file
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        txt_content = file.readlines()

    txt_content = [line.strip() for line in txt_content]
    txt_content = "\n".join(txt_content)

    # Split the content into blocks based on the blank lines
    txt_lines = re.split(r'\n\s*\n', txt_content.strip())

    if len(vtt_timecodes) != len(txt_lines):
        print("Something went wrong. Number of timecoeds from VTT doesn't match the number of lines from TXT")
        return
    
    with open(output_file_name, 'w', encoding='utf-8') as file:
        file.write("WEBVTT\n")
        file.write("\n")
        for timecode, line in zip(vtt_timecodes, txt_lines):
            file.write(f"{timecode}\n")
            file.write(f"{line}\n")
            file.write("\n")

    print("Done!")



if __name__ == "__main__":

    output_file = "output.vtt"
    vtt_files = get_files("vtt")
    txt_files = get_files("txt")

    if len(vtt_files) == 1 and len(txt_files) == 1:
        vtt_file = vtt_files[0]
        txt_file = txt_files[0]

        run(vtt_file, txt_file, output_file)

    else:
        print("There exist more that one vtt/txt file in the folder")