import numpy as np

from interface import IDSinterface
from analyze_picture import analyze_picture
import pygame

pygame.init()

def main():

    # Open the library
    cams_interface = IDSinterface()

    # Looking for available devices and choosing one via prompt
    cams = cams_interface.get_devices()
    if len(cams) > 1:
        print(f"\nFound {len(cams)} devices:")
        for idx, device in enumerate(cams):
            print(f" > {idx} : {device.ModelName()}")
        camID = int(input("\nChoose camera by id: "))
    else:
        print(f"\nJust found one IDS camera: {cams[0].ModelName()} model. Using it...")
        camID = 0

    # Main mode selection  (color and bit-depth)
    DESIRED_BIT_DEPTH = 12  # 8, 10, 12, 16 (12 is usually the maximum here)
    DESIRED_COLOR_MODE = "RGB"  # "RGB" or "Mono" (color or grayscale)

    # Setting the color and bit-depth mode and initializing the camera
    cams_interface.set_pixel_format(bit_rate=DESIRED_BIT_DEPTH,
                                    colorness=DESIRED_COLOR_MODE, idx=camID)
    cams_interface.select_and_start_device(camID)

    # Setting secondary parameters (fps, exposure, gain, etc.)
    #  - fps
    cams_interface.set_fps(1000, camID)
    print(f"Capturing at {cams_interface.get_fps(camID):.4g} fps")
    #  - exposure, un us (microseconds)
    cams_interface.set_exposure_time(1000*50, camID)  # 10 us minimum
    print(f"Exposure: {cams_interface.get_exposure_time(camID):.4g} us")
    #  - gain
    cams_interface.set_gain(1, camID)
    print(f"gain ->  {cams_interface.get_gain(camID)}")
    #  - Checking native resolution
    width, height = cams_interface.get_resolution(camID)
    print(f"Resoltion: {width}x{height}")

    # Setting pygame to render images
    binning = 3  # pygame work pixel by pixel, we reduce the resolution to fit a reasonable window
    display = pygame.display.set_mode((width//binning, height//binning))
    disp_array = pygame.surfarray.pixels3d(display)  # 3d array for RGB images

    running = True  # video loop
    while running:

        # Capturing the current image that camera gets
        rawimage = cams_interface.capture(camID)

        # Converting the image to a 8-bit RGB image just for display
        image8 = ((rawimage.astype(np.float64) / 2 ** DESIRED_BIT_DEPTH) * 2 ** 8).astype(np.uint8)
        if image8.ndim == 3 and image8.shape[2] == 3:
            disp_array[:, :, 0] = image8[::binning, ::binning, 0].T
            disp_array[:, :, 1] = image8[::binning, ::binning, 1].T
            disp_array[:, :, 2] = image8[::binning, ::binning, 2].T
        else:
            disp_array[:, :, 0] = image8[::binning, ::binning].T
            disp_array[:, :, 1] = image8[::binning, ::binning].T
            disp_array[:, :, 2] = image8[::binning, ::binning].T

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()

    # Analyzing the last rawimage to check the bit-depth and its histograms
    analyze_picture(rawimage)


if __name__ == "__main__":
    main()
