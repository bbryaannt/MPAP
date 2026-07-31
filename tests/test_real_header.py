"""
===============================================================================
MPAP
Melt Pool Analysis Platform

Real RPM222XR Header Test
===============================================================================
"""

from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from pipeline.decoder import RPM222XRDecoder


def main():

    # Hide the tkinter root window
    root = Tk()
    root.withdraw()

    print("Select an RPM222XR .dat file...")
    print()

    filename = askopenfilename(
        title="Select RPM222XR .dat File",
        filetypes=[("DAT Files", "*.dat")]
    )

    if not filename:
        print("No file selected.")
        return

    path = Path(filename)

    decoder = RPM222XRDecoder()

    header = decoder.peek_header(path)

    print("======================================")
    print("Header Successfully Read")
    print("======================================")
    print()

    print(header)

    print()

    print(f"Schema:               {header.schema}")
    print(f"Width:                {header.width}")
    print(f"Height:               {header.height}")
    print(f"Bit Depth:            {header.bit_depth}")
    print(f"Pixel Format:         {header.pixel_format}")
    print(f"Header Size:          {header.header_size} bytes")
    print(f"Header Length Words:  {header.header_length_words}")
    print(f"Image Shape:          {header.image_shape}")
    print(f"Pixel Count:          {header.pixel_count}")


if __name__ == "__main__":
    main()