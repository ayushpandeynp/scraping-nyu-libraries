from PyPDF2 import PdfReader, PdfWriter
from typing import List

def split_pages(filename: str, sep: int = 15) -> List[str]:
    outputs = []
    with open(filename, "rb") as f:
        reader = PdfReader(f)
        total_pages = len(reader.pages)

        processed = 0
        page_arr = []

        while processed < total_pages:
            rem = total_pages - processed
            until = processed + (rem if rem < sep else sep)
            page_arr.append(reader.pages[processed:until])

            processed += rem if rem < sep else sep

        for x, item in enumerate(page_arr):
            writer = PdfWriter()

            for i in item:
                writer.add_page(i)

            writer.write(f"output{x}.pdf")
            outputs.append(f"output{x}.pdf")

    return outputs
