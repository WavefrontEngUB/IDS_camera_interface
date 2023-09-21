from interface import IDSCamera
import pygame

pygame.init()

""" Do NOT USE this. It is old and it still under update. """

def main():
    # Obrim la llibreria
    camera = IDSCamera()
    # Busquem dispositius disponibles
    devs = camera.get_devices()
    for i, device in enumerate(devs):
        print(i, device.ModelName())
    # En seleccionem el primer
    camera.select_device(1)
    camera.select_device(0)
    #camera.select_device(1)
    # Seleccionem els fps
    camera.set_fps(20)
    #camera.set_fps(20, idx=1)
    print(f"Capturing at {camera.get_fps(idx=0):.4g} fps")
    # Seleccionem el temps d'exposició, en us
    camera.set_exposure_time(1/25*1e6)
    #camera.set_exposure_time(1/25*1e6, idx=1)
    print(f"Exposure: {camera.get_exposure_time():.4g} us")
    # Seleccionem la imatge de sortida
    camera.set_pixel_format("BGR8")
    # En mirem la resolució
    width0, height0 = camera.get_resolution()
    width1, height1 = camera.get_resolution(idx=1)
    width = [width0, width1]
    height = [height0, height1]

    print(f"Resoltion: {width}x{height}")
    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    camera.start_acquisition()
    camera.start_acquisition(1)
    # Capturem imatges
    display = pygame.display.set_mode((1200, 900))
    disp_array = pygame.surfarray.pixels3d(display)
    running = True
    clock = pygame.time.Clock()
    idx = 0
    while running:
        clock.tick()
        image = camera.capture(idx)
        reshapen = image.reshape((height[idx], width[idx], 3))
        disp_array[:, :, 0] = reshapen[:900, :1200, 2].T
        disp_array[:, :, 1] = reshapen[:900, :1200, 1].T
        disp_array[:, :, 2] = reshapen[:900, :1200, 0].T

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        pygame.display.flip()
        pygame.display.set_caption(f"FPS = {clock.get_fps():.4g}")
        idx = (idx + 1) % 2

if __name__ == "__main__":
    main()
