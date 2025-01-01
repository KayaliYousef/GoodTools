## Python re Library
 
*Importing the re library:*

<import re

*Matching patterns:*
>matches only the start of the string with the pattern
<re.match(pattern, string, flags=0)

*Searching for patterns:*
>finds only the first match in the string
<re.search(pattern, string, flags=0)

*Finding all occurrences of a pattern:*

<re.findall(pattern, string, flags=0)

*Replacing patterns:*

<re.sub(pattern, replacement, string, count=0, flags=0)

*Splitting strings using patterns:*

<re.split(pattern, string, maxsplit=0, flags=0)

# Common pattern elements:

-   . : matches any character except a newline
-   ^ : matches the start of a string
-   $ : matches the end of a string
-   [] : matches any character within the brackets
-   [^] : matches any character not within the brackets
-   * : matches zero or more occurrences of the preceding pattern
-   + : matches one or more occurrences of the preceding pattern
-   ? : matches zero or one occurrence of the preceding pattern
-   {m} : matches exactly m occurrences of the preceding pattern
-   {m,n} : matches between m and n occurrences of the preceding pattern

# Special sequences:

-    \d : matches any digit (equivalent to [0-9])
-    \D : matches any non-digit (equivalent to [^0-9])
-    \s : matches any whitespace character
-    \S : matches any non-whitespace character
-    \w : matches any alphanumeric character (equivalent to [a-zA-Z0-9_])
-    \W : matches any non-alphanumeric character (equivalent to [^a-zA-Z0-9_])
-    \b : matches a word boundary

# Look behind and ahead

-   (?=) - positive lookahead
-   (?!) - negative lookahead
-   (?<=) - positive lookbehind
-   (?<!) - negative lookbehind

# Flags:

-    re.IGNORECASE or re.I : makes matching case-insensitive
-    re.MULTILINE or re.M : allows ^ and $ to match the start and end of lines, not just the start and end of the string
-    re.DOTALL or re.S : makes . match any character, including newlines
-    re.VERBOSE or re.X : allows you to write regular expressions that are easier to read and understand