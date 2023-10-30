import matplotlib.pyplot as plt
import numpy as np

from interface import IDSCamera

""" Do NOT USE this. It is old and it still under update. """

def main(mode="Mono12", exposure_ms=1, fps=100):
    # Obrim la llibreria
    camera = IDSCamera()
    # Busquem dispositius disponibles
    cams = camera.get_devices()
    if len(cams) > 1:
        print(f"\nFound {len(cams)} devices:")
        for idx, device in enumerate(cams):
            print(f" > {idx} : {device.ModelName()}")
        camID = int(input("\nChoose camera by id: "))
    else:
        camID = 0

    # Seleccionem la imatge de sortida
    camera.set_pixel_format(mode)  # must be before selecting device
    camera.select_device(int(camID))

    # Seleccionem els fps
    camera.set_fps(fps)
    print(f"Capturing at {camera.get_fps():.4g} fps")

    # Seleccionem el temps d'exposició, en us
    camera.set_exposure_time(exposure_ms*1000)  # 10us minimum
    print(f"Exposure: {camera.get_exposure_time():.4g} us")
    # En mirem la resolució
    width, height = camera.get_resolution()
    print(f"Resoltion: {width}x{height}")

    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    camera.start_acquisition()
    # Capturem imatges
    # camera.set_gain(2)
    print(f"Gain:  {camera.get_gain()}")


    # Capturing 12 bit images using two methods, two words of 8 bits and one word of 16 bits
    image_array_2words = camera.capture(force8bit=True)
    image_array_1words = camera.capture(force8bit=False)

    print(f"image_array_2words.dtype: {image_array_2words.dtype}")
    print(f"image_array_1words.dtype: {image_array_1words.dtype}")

    image1 = image_array_2words[:, ::2]
    image2 = image_array_2words[:, 1::2]

    image_rec = image1 + image2.astype(np.uint16)*2**8
    print(f"image_rec.dtype: {image_rec.dtype}")

    hist0, hist_bins0 = np.histogram(image_array_2words.flatten(), bins=2**8, range=(0, 2**8))
    hist1, hist_bins1 = np.histogram(image1.flatten(), bins=256, range=(0, 2**8))
    hist2, hist_bins2 = np.histogram(image2.flatten(), bins=256, range=(0, 2**8))
    hist3, hist_bins3 = np.histogram(image_rec.flatten(), bins=2**12, range=(0, 2**12))
    hist4, hist_bins4 = np.histogram(image_array_1words.flatten(), bins=2**12, range=(0, 2 ** 12))

    plt.figure()
    plt.subplot(511)
    plt.plot(hist_bins0[:-1], hist0)
    plt.title("histogram raw 2 words", y=0.5)
    plt.subplot(512)
    plt.plot(hist_bins1[:-1], hist1)
    plt.title("histogram first word", y=0.5)
    plt.subplot(513)
    plt.plot(hist_bins2[:-1], hist2)
    plt.title("histogram second word", y=0.5)
    plt.subplot(514)
    plt.plot(hist_bins3[:-1], hist3)
    plt.title("histogram image_rec", y=0.5)
    plt.subplot(515)
    plt.plot(hist_bins4[:-1], hist4)
    plt.title("histogram single word", y=0.5)
    plt.show()

    plt.figure()
    plt.subplot(231)
    plt.imshow(image_array_2words)
    plt.colorbar()
    plt.title("raw 2 words")
    plt.subplot(232)
    plt.imshow(image1)
    plt.colorbar()
    plt.title("first word")
    plt.subplot(233)
    plt.imshow(image2)
    plt.colorbar()
    plt.title("second word")
    plt.subplot(234)
    plt.imshow(image_rec)
    plt.colorbar()
    plt.title("image_rec")
    plt.subplot(235)
    plt.imshow(image_array_1words)
    plt.colorbar()
    plt.title("single word")
    plt.show()


if __name__ == "__main__":
    main(mode="Mono12", exposure_ms=20, fps=100)
