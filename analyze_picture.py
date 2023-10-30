#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This program is used to analyze the picture taken by a IDS camera.

    Take a picture with the IDS camera, either with their-own software (cockpit),
    or with the interface in this repository, save it as a PNG file, and then
    run this program to analyze the picture.

    You can run it:
     - as script (in command line)
        $ python analyze_picture.py <picture_path>
     - by PLAY button in Spyder (then, type the picture_path in the console)
     - import it as a module (in python console or in any other script, check last step of test_camera.py)
        from analyze_picture import analyze_picture
        analyze_picture(picture_path)

    The program will show the picture, the histogram of the picture, and the
    color channels and their histograms.

    The program will also print the shape, dtype, min and max of the picture.

    Notice that the picture has 16 bits per channel and pixel (dtype=uint16).
    However, the camera only uses 12 bits per channel and pixel,
    the 4 least significant bits are always 0 and then the histogram is sparse.
    So, you can squeeze the picture to 12 bits per channel and pixel,
    just by dividing the image by 2**4=16. Check the option squeeze=True.

"""

import sys
import matplotlib.pyplot as plt
import numpy as np
import imageio.v2 as imageio

# If you don't have the freeimage plugin (FORMAT ERROR), you can download it with:
# imageio.plugins.freeimage.download()  # this should be done only once, then comment it again

def analyze_picture(picture_path, squeeze=False, bit_depth=12):

    if isinstance(picture_path, str):
        im = imageio.imread(picture_path, format='PNG-FI')  # if FORMAT ERROR -> check a couple of lines above
    else:
        """ If the picture_path is not a string, 
            it is assumed that it is already a numpy array.
        """
        im = picture_path

    print(f"raw_im.shape = {im.shape} ; raw_im.dtype = {im.dtype} ; "
          f"raw_im.min() = {im.min()} ; raw_im.max() = {im.max()}")
    if im.ndim == 2:
        im = np.repeat(im[:, :, np.newaxis], 3, axis=2)
        print('The picture is grayscale, so it has been converted to RGB.')
    elif im.shape[2] == 4:
        im = im[:, :, :3]
        print('The picture has an alpha channel, so it has been removed.')

    raw_br = int(np.round(np.log2(im.max())))  # = 16, 12, 10, 8...
    print(f"raw_br = {raw_br}")
    final_br = bit_depth if squeeze else raw_br

    if squeeze:
        """ Let's squeeze the picture to 12 bits per channel and pixel, 
            just by dividing the image by 2**4=16.
        """
        squeeze_level = int(2**16 / 2**bit_depth)  # = 16  (bit_depth=12)
        im = (im/squeeze_level).astype(np.uint16)
        hist = lambda im: np.histogram(im, bins=np.arange(2**bit_depth))[0]
    else:
        hist = lambda im: np.histogram(im, bins=np.arange(2**raw_br))[0]

    print(f"im.shape = {im.shape} ; im.dtype = {im.dtype} ; "
          f"im.min() = {im.min()} ; im.max() = {im.max()}")

    fig, ax = plt.subplots(2, 3)

    ax[0, 0].set_title('Red channel')
    r_plot = ax[0, 0].imshow(im[:, :, 0], vmin=0, vmax=2**final_br, cmap='Reds_r')
    plt.colorbar(r_plot, ax=ax[0, 0])

    ax[0, 1].set_title('Green channel')
    g_plot = ax[0, 1].imshow(im[:, :, 1], vmin=0, vmax=2**final_br, cmap='Greens_r')
    plt.colorbar(g_plot, ax=ax[0, 1])

    ax[0, 2].set_title('Blue channel')
    b_plot = ax[0, 2].imshow(im[:, :, 2], vmin=0, vmax=2**final_br, cmap='Blues_r')
    plt.colorbar(b_plot, ax=ax[0, 2])

    ax[1, 0].set_title('Original picture')
    ax[1, 0].imshow(im/2**final_br, cmap='gray')

    gs = ax[1, 2].get_gridspec()
    # remove the underlying axes
    for axi in ax[1, 1:]:
        axi.remove()
    axhist = fig.add_subplot(gs[1, 1:])
    axhist.set_title('Histograms (when not squeezed, check if it dense or sparse)')
    axhist.plot(hist(im[:, :, 0]), 'x-r', label='Red channel')
    axhist.plot(hist(im[:, :, 1]), '+-g', label='Green channel')
    axhist.plot(hist(im[:, :, 2]), '.-b', label='Blue channel')
    axhist.set_xlim([-1, 2**final_br+1])
    if final_br >= 10:
        axins = axhist.inset_axes([0.4, 0.6, 0.57, 0.37], xlim=(900, 990),
                                  ylim=(0, (hist(im[:, :, 2])[900:990]).max()*1.1))
        axins.plot(hist(im[:, :, 2]), '.b')
        axhist.indicate_inset_zoom(axins, edgecolor="black")
    axhist.legend()

    plt.show()

if __name__ == '__main__':
    """ Usage: python analyze_picture.py <path_to_picture> [--squeeze]
        
        If --squeeze is specified, the picture is squeezed to 12 bit depth.
        
        Example: python analyze_picture.py my_picture.png --squeeze
    """

    squeeze = False
    if len(sys.argv) > 1:
        picture_path = sys.argv[1]
        if '--squeeze' in sys.argv:
            squeeze = True
    else:
        picture_path = input('Please enter the path of the picture: ')

    analyze_picture(picture_path, squeeze=squeeze)
