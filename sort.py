import glob
import re

def get_files():
    """function to get all txt and srt files at current directory"""
    files = []
    for file in glob.glob("*.srt"):
        files.append(file)
    return files

def sort(files:str):
    """
    get all lines of each file and sort them by time.
    """
    # main loop, working with all files
    for file in files:
        # open orginal file 
        with open(file, 'r+', encoding="utf-8") as outfile:
            # open new file for the new changes
            name, srt = file.rsplit(".", 1)
            name = name.split("\\")
            name = name[-1]
            new_file_name = name + "_s." + srt
            with open(new_file_name, "w+", encoding="utf-8") as edited_file:
                # some needed variables 
                paragraph_number = 0
                blocks = {}
                is_last_line_time_stamp = False 
                last_time_stamp = None
                # checking all lines in current file
                for line in outfile:
                    # if line is not empty
                    if line:
                        # reqular expression to get lines with time stamp
                        time_stamp_pattern = r"\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d"
                        matched_time_stamp = re.match(time_stamp_pattern, line)
                        # if line is a time stamp linne
                        if matched_time_stamp:
                            last_time_stamp = matched_time_stamp.string
                            # added paragraph number to new file
                            paragraph_number += 1
                            # creat a list for each paragtaph
                            blocks[last_time_stamp] = []
                            # blocks[last_time_stamp].append(line)
                            is_last_line_time_stamp = True

                        elif last_time_stamp != None and is_last_line_time_stamp == True and line != "\n" and line[0].isdigit()==False:
                            blocks[last_time_stamp].append(line)

                        else:
                            is_last_line_time_stamp = False 

                # sort lines by paragraph number
                dictionary_items = blocks.items()
                sorted_pargraphs_number = 0
                for key, value in sorted(dictionary_items):
                    sorted_pargraphs_number += 1
                    edited_file.write(str(sorted_pargraphs_number) + "\n")
                    edited_file.write(str(key))
                    for line in value:
                        # write text line in the new file 
                        edited_file.write(str(line))
                    edited_file.write("\n")