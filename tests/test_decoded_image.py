import numpy as np

from models import DecodedImage
from models import Header


def main():

    image = np.zeros(
        (380, 1280),
        dtype=np.uint16
    )

    header = Header(
        schema=0,
        width=1280,
        height=380,
        bit_depth=12,
        pixel_format=0,
        header_size=8,
        raw_bytes=b"\x00" * 8,
        header_length_words=None
    )

    decoded = DecodedImage(
        image=image,
        header=header,
    )

    print(decoded)

    print()

    print("Shape:", decoded.shape)

    print("Data Type:", decoded.dtype)

    print("Width:", decoded.width)

    print("Height:", decoded.height)

    print("Bit Depth:", decoded.bit_depth)

    print("Schema:", decoded.schema)


if __name__ == "__main__":
    main()