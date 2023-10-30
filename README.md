# IDS camera interface

## Drivers installation

Go to [IDS cameras](https://es.ids-imaging.com/downloads.html) website and browse to
`uEye industrial cameras` => `Interface:USB3` , `Family:XLE Rev.1.1` , `Model:U3-3680XLE-C-HQ Rev.1.1` or so, 
=> `Show`.

On software section, choose your operative system and download the `IDS peak 2.5.1` suite.
It contains de drivers and the API. You must be registered in the website, but it is free and easy.

Once downloaded, install the suite and reboot the computer.

## Install the IDS-cameras API

We must install the python wheels via pip. Locate the wheels files.
They should be somewhere like `C:\Program Files\IDS\ids_peak\generic_sdk`.
There should be at least three directories: `afl`, `api`, `ipl`.

Open a terminal and move to this directory

``` bash
cd C:\Program Files\IDS\ids_peak\generic_sdk
```

Now, check your python version with `python`. Also, check the bitness (32 or 64).

*Note: If you want to use this API in the LabView environ, then you have to install it in the system python (not in a conda python).*

The first wheel to install is `api`. In the terminal, type
    
``` bash
pip install api/binding/python/wheel/x86_64/ids_peak-1.5.0.0-cpXX-cpXX-win_amd64.whl
```
Notice that cpXX have to be replaced with your python version (e.g. cp37 for python 3.7).

Then, install the `afl` and the `ipl` wheel with a similar command.

You can check that the installation was successful by typing `pip list` and looking for the `ids-peak` package 
or by checking that `import ids_peak` do not give any error in a python console.

## Install and test this IDS-cameras python interface

Clone this repository where you want

``` bash
cd $HOME  # or werever you want
git clone https://github.com/WavefrontEngUB/IDS_camera_interface.git
cd IDS_camera_interface
```

the code `test_camera.py` is a simple example of how to use the API. You can run it with

``` bash
python test_camera.py
```

If everything is ok, you should see a window with the camera image and 
the camera parameters printed in the terminal.

## IDS cameras python interface

Easy example for just one camera

     from interface import IDSinterface
    
     my_interface = IDSinterface()
     my_interface.set_pixel_format(bit_rate=12, colorness="RGB")  # RGB12 (optional)
     my_interface.select_and_start_device()  # Select the first device found and start acquisition
     my_interface.set_fps(1000)  # Set the fps to 1000 (optional)
     my_interface.set_exposure_time(1000*50)  # Set the exposure time to 50 ms (optional)
     my_interface.set_gain()  # Set the gain to 1 (optional)
     image = my_interface.capture()  # Capture an image as a numpy array
     my_interface.stop()  # Stop the acquisition
     del my_interface  # Close the interface and release the camera
    
If more than one camera is wired, every method has an optional argument 
`idx` to select the camera to manage.

      my_interface = IDSinterface()
      # Exploring available devices
      all_devices = my_interface.get_devices()
      print(f"\nFound {len(all_devices)} devices:")
      for idx, device in enumerate(all_devices):
          print(f" > {idx} : {device.ModelName()}")

      # Output:
      $ Found 2 devices:
      $  > 0 : U3-368xXLE-M
      $  > 1 : U3-368xXLE-C

      my_interface.select_and_start_device(idx=0)  # Select the first device found and start acquisition
      my_interface.select_and_start_device(idx=1)  # Select the second device found and start acquisition
      my_interface.set_pixel_format(bit_rate=8, idx=0)  # Seting 8 bit pixel format for the first camera
      my_interface.set_exposure(1000*50, idx=1)  # Set the exposure time to 50 ms to the second camera
      image0 = my_interface.capture(idx=0)  # Capture an image from the first camera
      image1 = my_interface.capture(idx=1)  # Capture an image from the second camera


## IDS cameras LabView interface

blablabla

## Requeriments

numpy
matplotlib
imageio


**************************************************************************

# Disclaimer

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; check the License.txt for more details.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

*************************************************************************
