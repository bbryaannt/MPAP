from enums import Classification
from enums import FrameStatus


def main():

    print(Classification.GOOD)

    print(Classification.LOW_POWER)

    print(FrameStatus.VALID)

    print(FrameStatus.NO_COMPONENT_FOUND)


if __name__ == "__main__":
    main()