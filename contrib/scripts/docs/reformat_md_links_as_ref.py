import re

this_file_in_docs = "User-Manual-For-Project-Managers.md"


def reformat_links_as_refs(file_name: str) -> None:
    """
    Function takes in a mark down file, searches for inline links and changes them to reference (footnote) version.

    NB the path to "docs" is hardcoded.
    NB: Care should be taken to make sure that inline url links are formatted correctly (broken lines, spaces, parenthesis, etc.)

    function created by contributor @cordovez.
    """
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    # Read the original markdown document
    with open(f"./docs/{this_file_in_docs}", "r") as file:
        lines = file.readlines()

    # Create a list to store the footnotes
    footnotes = []

    # Create a new list to store the modified lines
    modified_lines = []

    # Iterate through each line in the document
    for line in lines:
        # Find all matches of the pattern in the line
        matches = re.findall(pattern, line)

        # Iterate through the matches in reverse order
        for match in reversed(matches):
            label = match[0]
            url = match[1]

            # Generate the footnote reference
            footnote_ref = f"[{label}][{len(footnotes) + 1}]"

            # Replace the original hyperlink with the footnote reference
            line = line.replace(f"[{label}]({url})", footnote_ref)

            # Append the footnote to the list
            footnotes.append(f'[{len(footnotes) + 1}]: {url} "{label}"')

        # Append the modified line to the new list
        modified_lines.append(line)

    # Write the modified lines to the new document
    with open(f"./docs/{this_file_in_docs}", "w") as file:
        file.writelines(modified_lines)

    # Append the footnotes to the end of the document
    with open(f"./docs/{this_file_in_docs}", "a") as file:
        file.write("\n\n")
        file.write("\n".join(footnotes))


if __name__ == "__main__":
    reformat_links_as_refs(this_file_in_docs)
