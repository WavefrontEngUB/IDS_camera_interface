# from numba import jit
import numpy as np
import os
import imageio

import interface
import matplotlib.pyplot as plt

import json


try:
    IDS_interface_Obj = interface.IDSCamera()
except interface.ids_peak.NotFoundException:
    import time
    IDS_interface_Obj = None

roi = None
ref = None

def init(is16bits=False):
    bitness = 12 if is16bits else 8
    # Obrim la llibreria
    global IDS_interface_Obj
    if IDS_interface_Obj is None:
        cam_names = ["NotFound", "aaa", "bbb", "ccc"]
        cam_serials = ["-1", "-2", "-3", "-4"]
        NUM_OF_SIM_CAMERAS = 1  # set this just to test with different cameras
        return cam_names[:NUM_OF_SIM_CAMERAS], cam_serials[:NUM_OF_SIM_CAMERAS]

    # Busquem dispositius disponibles
    devicesSerial = []
    devicesName = []
    for camID, cam in enumerate(IDS_interface_Obj.get_devices()):
        devicesSerial.append(cam.SerialNumber())
        devicesName.append(cam.ModelName())

        # Seleccionem el bit depth, el mateix per totes les camares
        IDS_interface_Obj.set_pixel_format(bitness, colorness="Mono", idx=camID)

    return devicesName, devicesSerial


def start(cam_id=0, exposure_ms=1, fps=100, gain=0):
    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    global IDS_interface_Obj

    if IDS_interface_Obj is None:
        return 1, 1, fps, exposure_ms  # Dummy values

    IDS_interface_Obj.select_device(cam_id)
    # Seleccionem els fps
    IDS_interface_Obj.set_fps(fps, cam_id)
    true_fps = IDS_interface_Obj.get_fps(cam_id)

    # Seleccionem el temps d'exposició, en us
    IDS_interface_Obj.set_exposure_time(exposure_ms*1000, cam_id)
    true_exposure = IDS_interface_Obj.get_exposure_time(cam_id)/1000  # in ms

    # Seleccionem el gain
    IDS_interface_Obj.set_gain(gain, cam_id)
    true_gain = IDS_interface_Obj.get_gain(cam_id)

    # Mirem la resolució
    width, height = IDS_interface_Obj.get_resolution(cam_id)

    # Comencem l'adquisició, que bloqueja canvis "crítics" en la càmera
    IDS_interface_Obj.start_acquisition(cam_id)

    return width, height, true_fps, true_exposure#, true_gain

def capture(cam_id=0, binning=1, use_roi=False):
    # Capturem imatges
    global IDS_interface_Obj
    global roi

    if IDS_interface_Obj is None:
        time.sleep(0.01)  # setting an effective FPS about 100
        return np.random.randint(0, 2**16, (100, 100), np.uint16)  # Dummy values

    image = IDS_interface_Obj.capture(cam_id)[::binning, ::binning]

    if roi is not None and use_roi:
        roix, roiy, roiw, roih = roi
        image = image[roiy:roiy+roih, roix:roix+roiw]

    # return myTolist(image[::-1,:])
    return image[::-1,:].astype(np.uint16)


def stop():
    global IDS_interface_Obj
    if IDS_interface_Obj is not None:
        IDS_interface_Obj.stop_acquisition()


def set_exposure(exposure_ms, cam_id=0, set_max_fps=True):
    global IDS_interface_Obj
    if IDS_interface_Obj is None:
        exposure_ms += 1e-12
        return [exposure_ms, 1.e3/exposure_ms]  # Dummy values
    IDS_interface_Obj.set_exposure_time(exposure_ms*1000, cam_id)  # gets in um
    if set_max_fps:
        IDS_interface_Obj.set_max_fps(cam_id)
    return [IDS_interface_Obj.get_exposure_time(cam_id)/1000,  # in ms
            IDS_interface_Obj.get_fps(cam_id)]


def set_fps(fps, cam_id=0):
    global IDS_interface_Obj
    if IDS_interface_Obj is None:
        fps += 1e-12
        return [fps, 1.e3/fps]  # Dummy values
    IDS_interface_Obj.set_fps(fps, cam_id)
    return [IDS_interface_Obj.get_fps(cam_id),
            IDS_interface_Obj.get_exposure_time(cam_id)/1000]


def set_gain(gain, cam_id=0):
    global IDS_interface_Obj
    if IDS_interface_Obj is None:
        return [1., 1.]  # Dummy values
    IDS_interface_Obj.set_gain(gain, cam_id)
    return [IDS_interface_Obj.get_fps(cam_id),
            IDS_interface_Obj.get_exposure_time(cam_id)/1000]


def set_roi(roix, roiy, roiw, roih):
    global roi
    roi = (roix, roiy, roiw, roih)


def set_ref(refx, refy, refw, refh):
    global ref
    ref = (refx, refy, refw, refh)


def save(image, filename, main_roi=None, ref_roi=None, bit_depth=16):
    np_fn = filename.replace(".png", ".npy")

    # main_roi implementation
    roi_xi, roi_yi, roi_xf, roi_yf = main_roi or (None, None, None, None)
    image2save = image[roi_yi:roi_yf, roi_xi:roi_xf].astype(np.float32)

    ref_xi, ref_yi, ref_xf, ref_yf = ref_roi or (None, None, None, None)
    ref_mean = image[ref_yi:ref_yf, ref_xi:ref_xf].mean() if ref_roi else 1
    ref_max = 2**14 if ref_roi else 1

    image2save /= ref_mean
    image2save16 = (image2save * ref_max).astype(np.uint16)

    # Save as PNG with imageio
    crop_fn = filename.replace(".png", "_crop.png")
    if os.path.isfile(crop_fn):
        os.remove(crop_fn)
    imageio.imwrite(crop_fn, image2save16)

    # Guardem la imatge com a numpy array
    if os.path.isfile(np_fn):
        os.remove(np_fn)
    np.save(np_fn, image2save)

    try:
        # Guardem metadades
        dir, fn = os.path.split(filename)
        meta_fn = os.path.join(dir, fn.split('_')[0] + ".json")
        if os.path.isfile(meta_fn):
            # Load the dictionary from the file
            with open(meta_fn, 'r') as meta_file:
                meta_dict = json.load(meta_file)
        else:
            meta_dict = {}

        current_dict = {"mean": float(image2save.mean()),
                        "max": float(image2save.max()),
                        "min": float(image2save.min())}
        if main_roi is not None:
            current_dict.update({'center': ((roi_xi+roi_xf)/2, (roi_yi+roi_yf)/2),
                                 'size': (roi_xf-roi_xi, roi_yf-roi_yi)})

        if ref_roi is not None:
            current_dict.update(ref_roi={'center': ((ref_xi+ref_xf)/2, (ref_yi+ref_yf)/2),
                                         'size': (ref_xf-ref_xi, ref_yf-ref_yi)})

        meta_dict.update({fn: current_dict})
        # Save the dictionary to the file
        with open(meta_fn, 'w') as meta_file:
            json.dump(meta_dict, meta_file, indent=4)
    except:
        pass

    return np_fn


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    init(is16bits=True)
    start(0)
    image = capture(0)
    plt.figure()
    plt.imshow(image)
    plt.colorbar()
    plt.show()
