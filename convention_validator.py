import re

def validate_brackets_count(text:str) -> bool:
    con1 = False
    con2 = False
    con3 = False
    con4 = False
    opening_round_brackets = re.findall(r'\(', text)
    closing_round_brackets = re.findall(r'\)', text)
    opening_square_brackets = re.findall(r'\[', text)
    closing_square_brackets = re.findall(r'\]', text)
    openeing_curly_brackets = re.findall(r'\{', text)
    closing_curly_brackets = re.findall(r'\}', text)

    opening_round_brackets_count = len(opening_round_brackets)
    closing_round_brackets_count = len(closing_round_brackets)
    opening_square_brackets_count = len(opening_square_brackets)
    closing_square_brackets_count = len(closing_square_brackets)
    openeing_curly_brackets_count = len(openeing_curly_brackets)
    closing_curly_brackets_count = len(closing_curly_brackets)

    round_brackets_count = opening_round_brackets_count + closing_round_brackets_count
    square_brackets_count = opening_square_brackets_count + closing_square_brackets_count
    curly_brackets_count = openeing_curly_brackets_count + closing_curly_brackets_count

    if not square_brackets_count+curly_brackets_count >= round_brackets_count:
        print("<-- Make sure to use round brackets only for Quran and Hadith quotations -->\n")
    else: con1 = True

    if opening_round_brackets_count != closing_round_brackets_count:
        print("<-- Opening and closing round brackets count doesn't match -->\n")
    else: con2 = True

    if opening_square_brackets_count != closing_square_brackets_count:
        print("<-- Opening and closing square brackets count doesn't match -->\n") 
    else: con3 = True

    if openeing_curly_brackets_count != closing_curly_brackets_count:
        print("<-- Opening and closing curly brackets count doesn't match -->\n")
    else: con4 = True

    if con1 and con2 and con3 and con4:
        return True
    else: return False

def validate_dot_space_after_round_bracket(text:str) -> bool:
    bracket_dot_space = re.findall(r'\).{0,2}', text) 
    count = 0
    for expression in bracket_dot_space:
        if not "). " in expression:
            if ")}" in expression:
                pass
            else:
                count += 1
    if count == 0:
        # print("<-- dot-space after round bracket convention is valid -->\n")
        return True
    else: 
        print(f"<-- dot-space after round bracket convention is NOT valid at {count} locations -->\n")
        return False

# in case user used something else other than round brackets () before [Quran x:y]
def validate_before_square_brackets(text:str) -> bool:
    before_square_brackets = re.findall(r'..\s*(?=\[\s*\w*\s*\w+:\d+\])', text)
    count = 0 # for not using round brackets
    count2 = 0 # for missing space after the dot
    count3 = 0 # for using too many spaces after the dot
    for expression in before_square_brackets:
        match = re.match(r'\)\.\s*', expression)
        if not match:
            count += 1
        else:
            if len(match.group().strip("\n")) < 3:
                count2 += 1
            elif len(match.group().strip("\n")) > 3:
                count3 += 1
    if count == 0 and count2 == 0 and count3 == 0:
        # print("<-- Ayaht in round brackets convetion is MOST LIKELY valid -->\n")
        return True
    else:
        if count != 0: 
            print(f"<-- You might have not used round brackets for Ayaht at {count} locations -->\n")
        if count2 != 0:
            print(f"<-- Missing space after ').' at {count2} locations -->\n")
        if count3 != 0:
            print(f"<-- Too many spaces after the ').' at {count3} locations -->\n")
        return False

# in case user used something else other than round brackets () before {Authentic/Good acc. to Zaid}
def validate_before_curly_brackets(text:str) -> bool:
    before_curly_brackets = re.findall(r'..\s*(?=\{.*\})(?!\{\(Blessed Tree\)\})', text)
    count = 0 # for not using round brackets
    count2 = 0 # for missing space after the dot
    count3 = 0 # for using too many spaces after the dot
    for expression in before_curly_brackets:
        match = re.match(r'\)\.\s*', expression)
        if not match:
            count += 1
        else:
            if len(match.group().strip("\n")) < 3:
                count2 += 1
            elif len(match.group().strip("\n")) > 3:
                count3 += 1
    if count == 0 and count2 == 0 and count3 == 0:
        # print("<-- Hadith in round brackets convetion is MOST LIKELY valid -->\n")
        return True
    else:
        if count != 0: 
            print(f"<-- You might have not used round brackets for Hadith at {count} locations -->\n")
        if count2 != 0:
            print(f"<-- Missing space after ').' at {count2} locations -->\n")
        if count3 != 0:
            print(f"<-- Too many spaces after the ').' at {count3} locations -->\n")
        return False

def find_missing_round_brackets(text:str) -> bool:
    stack = []
    opening_brackets = []
    closing_brackets = []
    for i, char in enumerate(text):
        if char == '(':
            if stack: # Stack is not empty
                opening_brackets.append(stack[0]) # opening bracket without closing bracket
                stack.pop()
                stack.append(i)
            else: # Stack is empty
                stack.append(i)
        elif char == ')':
            if stack: # Stack is not empty 
                stack.pop()
            else: # Stack is empty
                closing_brackets.append(i) # closing bracket without opening bracket
        elif i == len(text)-1: # reached end of text
            if stack: # Stack is not empty
                opening_brackets.append(stack[0])

    for index in opening_brackets:
        if len(text[index:]) >= 50: # check if there are enough characters to pring
            print("******************")
            print("Opening round bracket without closing in the following location: -->:\n"+text[index:index+49]+"\n")
            print("******************")
        else: # if there is not enough charachters print to the end of the characters
            print("******************")
            print("Opening round bracket without closing in the following location: -->:\n"+text[index:]+"\n")
            print("******************")
    for index in closing_brackets:
        if len(text[:index]) >= 50:
            print("******************")
            print("Closing round bracket without opening in the following location: -->\n"+text[index-49:index+1]+"\n")
            print("******************")
        else:
            print("******************")
            print("Closing round bracket without opening in the following location: -->:\n"+text[:index+1]+"\n")
            print("******************")
    
    if opening_brackets and closing_brackets:
        return False
    else: return True

def find_missing_square_brackets(text:str) -> bool:
    stack = []
    opening_brackets = []
    closing_brackets = []
    for i, char in enumerate(text):
        if char == '[':
            if stack: # Stack is not empty
                opening_brackets.append(stack[0]) # opening bracket without closing bracket
                stack.pop()
                stack.append(i)
            else: # Stack is empty
                stack.append(i)
        elif char == ']':
            if stack: # Stack is not empty 
                stack.pop()
            else: # Stack is empty
                closing_brackets.append(i) # closing bracket without opening bracket
        elif i == len(text)-1:
            if stack:
                opening_brackets.append(stack[0])

    for index in opening_brackets:
        if len(text[index:]) >= 50: # check if there are enough characters to pring
            print("******************")
            print("Opening square bracket without closing in the following location: -->:\n"+text[index:index+49]+"\n")
            print("******************")
        else: # if there is not enough charachters print to the end of the characters
            print("******************")
            print("Opening square bracket without closing in the following location: -->:\n"+text[index:]+"\n")
            print("******************")
    for index in closing_brackets:
        if len(text[:index]) >= 50:
            print("******************")
            print("Closing square bracket without opening in the following location: -->:\n"+text[index-49:index+1]+"\n")
            print("******************")
        else:
            print("******************")
            print("Closing square bracket without opening in the following location: -->:\n"+text[:index+1]+"\n")
            print("******************")

    if opening_brackets and closing_brackets:
        return False
    else: return True

def find_missing_curly_brackets(text:str) -> bool:
    stack = []
    opening_brackets = []
    closing_brackets = []
    for i, char in enumerate(text):
        if char == '{':
            if stack: # Stack is not empty
                opening_brackets.append(stack[0]) # opening bracket without closing bracket
                stack.pop()
                stack.append(i)
            else: # Stack is empty
                stack.append(i)
        elif char == '}':
            if stack: # Stack is not empty 
                stack.pop()
            else: # Stack is empty
                closing_brackets.append(i) # closing bracket without opening bracket
        elif i == len(text)-1: # reached end of text
            if stack: # Stack is not empty
                opening_brackets.append(stack[0])

    for index in opening_brackets:
        if len(text[index:]) >= 50: # check if there are enough characters to pring
            print("******************")
            print("Opening curly bracket without closing in the following location: -->:\n"+text[index:index+49]+"\n")
            print("******************")
        else: # if there is not enough charachters print to the end of the characters
            print("******************")
            print("Opening curly bracket without closing in the following location: -->:\n"+text[index:]+"\n")
            print("******************")
    for index in closing_brackets:
        if len(text[:index]) >= 50:
            print("******************")
            print("Closing curly bracket without opening in the following location: -->\n"+text[index-49:index+1]+"\n")
            print("******************")
        else:
            print("******************")
            print("Closing curly bracket without opening in the following location: -->:\n"+text[:index+1]+"\n")
            print("******************")
    
    if opening_brackets and closing_brackets:
        return False
    else: return True

def validate_inside_square_brackets(text:str) -> bool:
    count = 0
    count2 = 0
    inside_square_brackets = re.findall(r'(?<=\)\.\s)\[.*\]', text)
    inside_square_brackets2 = re.findall(r'(?<=\)\.\s\n\n)\[.*\]', text)
    pattern = r'\[\w*\s?\d+:\d+\]'
    for expression in inside_square_brackets:
        match = re.match(pattern, expression)
        if not match:
            count += 1
    for expression in inside_square_brackets2:
        match = re.match(pattern, expression)
        if not match:
            count2 += 1
    if count == 0 and count2 == 0:
        return True
    else:
        count_sum = count + count2
        print(f"<-- Not following the convention inside the square brackets at {count_sum} locations -->\n")
        return False

def clean_srt(srt_file_path:str) -> str:
    with open(srt_file_path, 'r', encoding="utf-8") as f:
        text = f.readlines()
    # remove time codes and subtitle block indexes
    cleaned_lines = [line for line in text if not (line.strip().isdigit() or '-->' in line)]
    # remove empty lines
    cleaned_lines = [line for line in cleaned_lines if line.strip()]
    return '\n'.join(cleaned_lines)

if __name__ == "__main__":
    text = clean_srt("test.srt")

    brackets_count_valid = validate_brackets_count(text)
    no_missing_round_brackets = find_missing_round_brackets(text)
    no_missing_square_brackets = find_missing_square_brackets(text)
    no_missing_curly_brackets = find_missing_curly_brackets(text)
    dot_space_after_bracket_valid = validate_dot_space_after_round_bracket(text)
    before_square_brackets_valid = validate_before_square_brackets(text)
    before_curly_brackets_valid = validate_before_curly_brackets(text)
    inside_square_brackets = validate_inside_square_brackets(text)

    def check_fo_validation():
        if brackets_count_valid and dot_space_after_bracket_valid and before_square_brackets_valid and before_curly_brackets_valid and no_missing_round_brackets and no_missing_square_brackets and no_missing_curly_brackets and inside_square_brackets:
            print("___SRT is VALID___")
            return True

        else: 
            print("___SRT is NOT Valid___")
            return False
