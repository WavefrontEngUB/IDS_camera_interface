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

Now, check your python version with `python`. Also, check the bitness (32 or 64).`

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

blablabla

## IDS cameras LabView interface

blablabla

## Interfície per a càmeres IDS

El script `interface.py` conté un wrapper de la API de IDS per a controlar les
seves pròpies càmeres. D'aquesta forma, en facilitem la posada a punt i l'ús
amb funcions de conveniència, que preparen la càmera automàticament per a la presa de
dades. L'ús d'aquesta interfície és ben senzill, tal i com surt al script `test_camera.py`

```python
from interface import IDSCamera
```




**************************************************************************

# Disclaimer

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
 02111-1307  USA

  All comments concerning this program package may be sent to the
  e-mail address 'dmaluenda@ub.edu'

*************************************************************************
