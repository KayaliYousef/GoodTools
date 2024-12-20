import re


from prep_srt import srt_to_json, split_in_half
import helper_functions

breakers = ["...", ".", ",", "?", ":", "!"]
char_per_line = 42


def find_breaker(text: str, breaker: str) -> list[int]:
    """
    Finds the indices of all occurrences of the specified breaker in the text.

    Parameters:
        text (str): The text to search.
        breaker (str): A breaker to search for.

    Returns:
        List[int]: A list of indices where the breaker occur in the text.
    """
    
    # Find indices of all occurrences
    return [i for i, char in enumerate(text) if char == breaker]

json = srt_to_json("english.srt", save_json=False)

entries = json.get('entries', [])

for entry in entries:
    block_number = entry.get('block_number')
    time_code = entry.get('time_code')
    time_code_start = entry.get('time_code_start')
    time_code_end = entry.get('time_code_end')
    text = entry.get('text')
    linebreak_in_text = entry.get('linebreak_in_text')
    duration_in_milliseconds = entry.get('duration_in_milliseconds')
    num_characters_without_linebreak = entry.get('num_characters_without_linebreak')

    if (linebreak_in_text and num_characters_without_linebreak > char_per_line * 2) or (not linebreak_in_text and num_characters_without_linebreak > char_per_line):
        text_without_line_break = text.replace("\n", " ")
        find_breaker(text_without_line_break, "...")