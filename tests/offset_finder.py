# pdf_sentence_offset_finder.py

import json
from pdfminer.high_level import extract_text

def find_sentence_offsets_in_pdf(pdf_path, sentence):
    """
    Finds all start and end offsets of a given sentence in a PDF file.

    :param pdf_path: Path to the PDF file.
    :param sentence: Sentence to search for.
    :return: List of tuples (start_offset, end_offset).
    """
    text = extract_text(pdf_path)
    offsets = []
    
    start = 0
    while True:
        idx = text.find(sentence, start)
        if idx == -1:
            break
        end_idx = idx + len(sentence)
        offsets.append((idx, end_idx))
        start = end_idx  # Move past this occurrence
    
    return offsets


if __name__ == "__main__":
    pdf_path = input("Enter path to your PDF file: ").strip()
    json_path = input("Enter path to your JSON file: ").strip()

    # Load JSON
   # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if it is a list
    if isinstance(data, list):
        first_item = data[0]  # take the first element
    else:
        first_item = data

    sentence = first_item.get("sentence")
    if not sentence:
        print("JSON does not contain 'sentence' field.")
        exit(1)


    offsets = find_sentence_offsets_in_pdf(pdf_path, sentence)
    if offsets:
        print("Sentence found at offsets (start, end):")
        for start, end in offsets:
            print(f"({start}, {end})")
    else:
        print("Sentence not found in the PDF.")
