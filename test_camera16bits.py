import matplotlib.pyplot as plt
import numpy as np

from interface import IDSCamera


def main():
    # Obrim la llibreria
    camera = IDSCamera()
    # Busquem dispositius disponibles
    cams = camera.get_devices()
    for idx, device in enumerate(cams):
        print(idx, device.ModelName())
    if idx == 0:
        camID = 0
    else:
        camID = input("Choose camera: ")
    # En seleccionem el primer
    # for id in range(10):
    #     print(id)
    #     try:
    camera.select_device(int(camID))
        # except:

    # Seleccionem els fps
    camera.set_fps(1000)
    print(f"Capturing at {camera.get_fps():.4g} fps")
    # Seleccionem el temps d'exposició, en us
    camera.set_exposure_time(13*1000) # 10 us minimum
    print(f"Exposure: {camera.get_exposure_time():.4g} us")
    # Seleccionem la imatge de sortida
    mode = "Mono12"
    camera.set_pixel_format(mode)
    # En mirem la resolució
    width, height = camera.get_resolution()
    print(f"Resoltion: {width}x{height}")
    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    camera.start_acquisition()
    # Capturem imatges
    # camera.set_gain(1)
    print(f" ->  {camera.get_gain()}")
    # image = np.zeros((height, width), dtype=np.uint16)
    image_array = camera.capture()

    print(image_array.dtype)

    image1 = image_array[:, ::2]
    image2 = image_array[:, 1::2]

    image_rec = image1 + image2.astype(np.uint16)*2**8

    hist0, hist_bins0 = np.histogram(image_array.flatten(), bins=2**12, range=(0, 2**12))
    hist1, hist_bins1 = np.histogram(image1.flatten(), bins=256, range=(0, 2**8))
    hist2, hist_bins2 = np.histogram(image2.flatten(), bins=256, range=(0, 2**8))
    hist3, hist_bins3 = np.histogram(image_rec.flatten(), bins=2**12, range=(0, 2**12))


    plt.figure()
    plt.subplot(411)
    plt.bar(hist_bins0[:-1], hist0)
    plt.title("histogram raw")
    plt.subplot(412)
    plt.plot(hist_bins1[:-1], hist1)
    plt.title("histogram image1")
    plt.subplot(413)
    plt.plot(hist_bins2[:-1], hist2)
    plt.title("histogram image2")
    plt.subplot(414)
    plt.plot(hist_bins3[:-1], hist3)
    plt.title("histogram image_rec")

    plt.show()



    # image1_aux = np.unpackbits(image1, axis=1)
    # print(image1_aux.shape)
    # image1_aux2 = np.zeros_like(image1_aux)
    # image1_aux2[:, :] = image1_aux[:, ::-1]
    # image1 = np.packbits(image1_aux2, axis=1)
    # print(image1_aux2[0, :20])
    plt.figure()
    plt.subplot(231)
    plt.hist(image1.flatten(), bins=256)
    plt.subplot(232)
    plt.hist(image2.flatten(), bins=256)
    plt.subplot(234)
    plt.imshow(image1)
    plt.colorbar()
    plt.subplot(235)
    plt.imshow(image2)
    plt.colorbar()
    plt.subplot(236)
    plt.imshow(image1+image2*2**8)
    plt.colorbar()
    plt.subplot(233)
    plt.imshow(image1*2**8+image2)
    plt.colorbar()
    plt.show()



if __name__ == "__main__":
    main()
