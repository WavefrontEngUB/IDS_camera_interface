import numpy as np

from interface import IDSCamera
import pygame

pygame.init()

def main():
    # Obrim la llibreria
    camera = IDSCamera()
    # Busquem dispositius disponibles
    cams = camera.get_devices()
    for idx, device in enumerate(cams):
        print(idx, device.ModelName())
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
    camera.set_exposure_time(10*1) # 10 us minimum
    print(f"Exposure: {camera.get_exposure_time():.4g} us")
    # Seleccionem la imatge de sortida
    mode = "Mono12p"
    camera.set_pixel_format(mode)
    # En mirem la resolució
    width, height = camera.get_resolution()
    print(f"Resoltion: {width}x{height}")
    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    camera.start_acquisition()
    # Capturem imatges
    display = pygame.display.set_mode((768, 512))
    disp_array = pygame.surfarray.pixels3d(display)
    running = True
    # camera.set_gain(1)
    print(f" ->  {camera.get_gain()}")
    # image = np.zeros((height, width), dtype=np.uint16)
    while running:
        image = camera.capture()

        disp_array[:, :, 0] = image[:512, :768].T
        disp_array[:, :, 1] = image[:512, :768].T
        disp_array[:, :, 2] = image[:512, :768].T

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()

if __name__ == "__main__":
    main()
