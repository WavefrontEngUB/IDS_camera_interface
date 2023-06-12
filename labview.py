from numba import jit
import numpy as np

from interface import IDSCamera
import matplotlib.pyplot as plt

IDS_interface_Obj = None
roi = None

def init(is16bits=False):
    mode = "Mono12" if is16bits else "Mono8"
    # Obrim la llibreria
    global IDS_interface_Obj
    IDS_interface_Obj = IDSCamera()
    # Busquem dispositius disponibles
    devicesSerial = []
    devicesName = []
    for camID, cam in enumerate(IDS_interface_Obj.get_devices()):
        devicesSerial.append(cam.SerialNumber())
        devicesName.append(cam.ModelName())


    # Seleccionem la imatge de sortida
    IDS_interface_Obj.set_pixel_format(mode)

    return devicesName, devicesSerial


def start(cam_id=0, exposure_ms=1, fps=100):
    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    global IDS_interface_Obj

    IDS_interface_Obj.select_device(cam_id)
    # Seleccionem els fps
    IDS_interface_Obj.set_fps(fps, cam_id)
    true_fps = IDS_interface_Obj.get_fps(cam_id)

    # Seleccionem el temps d'exposició, en us
    IDS_interface_Obj.set_exposure_time(exposure_ms*1000, cam_id)
    true_exposure = IDS_interface_Obj.get_exposure_time(cam_id)/1000  # in ms

    # Mirem la resolució
    width, height = IDS_interface_Obj.get_resolution(cam_id)

    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    IDS_interface_Obj.start_acquisition()

    return width, height, true_fps, true_exposure

def capture(cam_id=0, binning=1):
    # Capturem imatges
    global IDS_interface_Obj
    global roi
    image = IDS_interface_Obj.capture(cam_id)[::binning, ::binning]

    # image1 = image_array[:, ::2]
    # image2 = image_array[:, 1::2]

    # image1_aux = np.unpackbits(image1, axis=1)
    # image1_aux2 = np.zeros_like(image1_aux)
    # image1_aux2[:, :] = image1_aux[:, ::-1]
    # image1 = np.packbits(image1_aux2, axis=1)

    # image = image1 + (image2.astype(np.uint16)+1) * 2**8

    if roi is not None:
        roix, roiy, roiw, roih = roi
        image = image[roiy:roiy+roih, roix:roix+roiw]

    # return myTolist(image[::-1,:])
    return image[::-1,:].astype(np.uint16)


def stop():
    global IDS_interface_Obj
    IDS_interface_Obj.stop_acquisition()

def set_exposure(exposure_ms, cam_id=0):
    global IDS_interface_Obj
    IDS_interface_Obj.set_exposure_time(exposure_ms*1000, cam_id)  # gets in um
    return [IDS_interface_Obj.get_exposure_time(cam_id)/1000,  # in ms
            IDS_interface_Obj.get_fps(cam_id)]

def set_fps(fps, cam_id=0):
    global IDS_interface_Obj
    IDS_interface_Obj.set_fps(fps, cam_id)
    return [IDS_interface_Obj.get_fps(cam_id),
            IDS_interface_Obj.get_exposure_time(cam_id)/1000]

def set_roi(roix, roiy, roiw, roih):
    global roi
    roi = (roix, roiy, roiw, roih)


if __name__ == "__main__":
    init(True)
    start(0)
    image = capture(0)
    print(image.shape)
