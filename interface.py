from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension
import warnings


class IDSinterface(object):
    """ IDS Camera interface, keeping all memory and low level bus management opaque
        to the user, for ease of use.

        Usage:

            from interface import IDSinterface

            my_interface = IDSinterface()
            my_interface.set_pixel_format(bit_rate=12, colorness="RGB")  # RGB12 (optional)
            my_interface.select_and_start_device()  # Select the first device found and start acquisition
            my_interface.set_fps(1000)  # Set the fps to 1000 (optional)
            my_interface.set_exposure_time(1000*50)  # Set the exposure time to 50 ms (optional)
            my_interface.set_gain()  # Set the gain to 1 (optional)
            my_interface.capture()  # Capture an image
            my_interface.stop()  # Stop the acquisition
            del my_interface  # Close the interface



    """

    def __init__(self):
        ids_peak.Library.Initialize()

        self.__create_device_manager()

        # We initialize variables as dictionaries to allow multiple devices, key=idx
        self.__devices = {}  # This is just for SELECTED devices, not all wired devices!
        self.__datastreams = {}
        self.__nodemaps = {}
        self.__acquisition_ready = {}
        self.__inner_pixel_format = {}
        self.__outer_pixel_format = {}
        self.__resolution = {}

    def __create_device_manager(self):

        self.__device_manager = ids_peak.DeviceManager.Instance()
        self.__device_manager.Update()

        # Si no hem trobat cap càmera, tallem pel dret!
        if self.__device_manager.Devices().empty():
            self.__destroy()
            raise ids_peak.NotFoundException("No devices found!")

    def __setup_data_stream(self, idx=0):
        """ Setup the data stream for the selected device.
            This is necessary before starting the acquisition.
        """
        device = self._get_device(idx)

        # Let's set the datastream
        datastreams = device.DataStreams()
        if datastreams.empty():
            raise ids_peak.NotAvailableException("Device has no DataStream!")
        datastream = datastreams[0].OpenDataStream()
        self.__datastreams[idx] = datastream

        # let's set the some properties via nodemap and store the nodemap
        nodemap = device.RemoteDevice().NodeMaps()[0]
        self.__nodemaps[idx] = nodemap
        # Preparem captures d'imatge contínues
        try:
            nodemap.FindNode("UserSetSelector").SetCurrentEntry("Default")
            nodemap.FindNode("UserSetLoad").Execute()
            nodemap.FindNode("UserSetLoad").WaitUntilDone()
        except ids_peak.Exception:
            # Userset is not available
            pass

        if not self.__inner_pixel_format.get(idx):
            print("No pixel format selected. Setting the default as 8bit and "
                  "the native color mode.")
            self.set_pixel_format(idx=idx)  # with default values
        try:
            nodemap.FindNode("PixelFormat").SetCurrentEntry(self.__inner_pixel_format.get(idx))
        except:
            self.print_available_formats(idx)
            raise RuntimeError(f"\nPixel format not supported by this device.\n\n"
                               f"Choose one valid: "
                               f"{', '.join(self.print_available_formats(do_print=False))}.")


        # Allocate and announce image buffers and queue them
        payload_size = nodemap.FindNode("PayloadSize").Value()
        buffer_count_max = datastream.NumBuffersAnnouncedMinRequired()
        for i in range(buffer_count_max):
            buffer = datastream.AllocAndAnnounceBuffer(payload_size)
            datastream.QueueBuffer(buffer)

    def select_device(self, device_idx):
        """ Public method to select a device.
            This means, to open the communications to it.

            This is the first mandatory method to start working with the camera.
        """
        try:
            device = self.__device_manager.Devices()[device_idx]
        except:
            # self.__destroy()  # we can work with other cams
            raise KeyError(f"Device {device_idx} not found.")

        # Trying to open the camera
        if not device.IsOpenable():
            # self.__destroy()  # we can work with other cams
            raise ids_peak.NotInitializedException(
                f"\n\nDevice {device_idx} could not be opened.\n"
                f"Could it be in use by another application?\n")

        self.__devices[device_idx] = device.OpenDevice(ids_peak.DeviceAccessType_Control)

        # Configure this device
        self.__setup_data_stream(idx=device_idx)

    def set_pixel_format(self, bit_rate=8, colorness=None, idx=0):
        """ bit_rate: 8, 10, 12, 14, 16 bits (IDS cameras only support 8, 10, 12 -I guess-)
            colorness: 'Mono' or 'RGB'

            bit_rate and colorness are for the user preferences.

            This method will set the optimum inner pixel format to get that preferences,
            and the outer pixel format to get the bit rate and color mode chosen by user.
        """
        available_inner_modes = {"Mono": ["Mono8", "Mono10g40IDS", "Mono12g24IDS"],
                                 "RGB": ["BayerGR8", "BayerGR10g40IDS", "BayerGR12g24IDS"]}

        available_outer_modes = {"Mono": ["Mono8", "Mono10", "Mono12"],
                                 "RGB": ["RGB8", "RGB10", "RGB12"]}

        # Check if the camera is color or monochrome
        cam_name = self.get_devices()[idx].ModelName()
        if cam_name.endswith("C"):
            cam_colorness = "RGB"
            print(f"{cam_name} is a color camera.")
        else:
            cam_colorness = "Mono"
            print(f"{cam_name} is a gray-scale camera.")

        colorness = colorness or cam_colorness

        valid_br = [8, 10, 12]
        if bit_rate not in valid_br:  # , 14, 16]:
            raise RuntimeError(f"{bit_rate} : Bit rate not supported. Choose one valid: "
                               f"{', '.join([str(x) for x in valid_br])}")
        bit_rate_idx = bit_rate // 2 - 4

        valid_cm = ['Mono', 'RGB']
        if colorness not in valid_cm:
            raise RuntimeError(f"{colorness} : Color mode not supported. Choose one valid: "
                               f"{', '.join(valid_cm)}")



        inner_mode = available_inner_modes[cam_colorness][bit_rate_idx]
        outer_mode = available_outer_modes[colorness][bit_rate_idx]

        self.__inner_pixel_format[idx] = getattr(ids_peak_ipl,
                                                 "PixelFormatName_" + inner_mode)
        self.__outer_pixel_format[idx] = getattr(ids_peak_ipl,
                                                 "PixelFormatName_" + outer_mode)

        print(f"Pixel formats set to {inner_mode} (internal) and "
              f"{outer_mode} (final image)")

    def start_acquisition(self, idx=0):
        """ Starting the acquisition of images with the selected parameters.
        """
        nodemap_remote_device = self._get_nodemap(idx=idx)
        datastream = self.__datastreams[idx]
        try:
            nodemap_remote_device.FindNode("TLParamsLocked").SetValue(1)

            datastream.StartAcquisition()
            nodemap_remote_device.FindNode("AcquisitionStart").Execute()
            nodemap_remote_device.FindNode("AcquisitionStart").WaitUntilDone()
        except Exception as e:
            raise e

        self.__acquisition_ready[idx] = True

    def stop_acquisition(self, idx=0):
        """Comença la captura contínua d'imatges amb els paràmetres seleccionats."""
        nodemap_remote_device = self._get_nodemap(idx=idx)
        datastream = self.__datastreams[idx]
        try:
            nodemap_remote_device.FindNode("TLParamsLocked").SetValue(0)

            datastream.StopAcquisition()
            nodemap_remote_device.FindNode("AcquisitionStop").Execute()
            nodemap_remote_device.FindNode("AcquisitionStop").WaitUntilDone()
        except Exception as e:
            raise e

        self.__acquisition_ready[idx] = False

    def __stop_all_acquisitiona(self):
        if not self.__devices:
            return
        # Otherwise try to stop acquisition
        try:
            for idx in self.__devices.keys():
                self.release_device(idx)

        except Exception as e:
            raise e

    def release_device(self, idx=0):
        remote_nodemap = self._get_nodemap(idx=idx)
        remote_nodemap.FindNode("AcquisitionStop").Execute()
        # Stop and flush datastream
        self.__datastreams[idx].KillWait()
        self.__datastreams[idx].StopAcquisition(ids_peak.AcquisitionStopMode_Default)
        self.__datastreams[idx].Flush(ids_peak.DataStreamFlushMode_DiscardAll)
        # Unlock parameters after acquisition stop
        if self.__nodemaps[idx] is not None:
            try:
                self.__nodemaps[idx].FindNode("TLParamsLocked").SetValue(0)
            except Exception as e:
                raise e

    def select_and_start_device(self, device_idx=0):
        """ Shortcut to select a device and start its acquisition.

            The easiest way to capture a picture with a camera is:

                my_interface = IDSInterface()
                my_interface.select_and_start_device()
                my_interface.capture()

        """
        self.select_device(device_idx)
        self.start_acquisition(device_idx)

    def get_devices(self):
        return self.__device_manager.Devices()

    def get_devices_names(self):
        return [x.ModelName() for x in self.get_devices()]

    def _get_device(self, idx=0):
        device = self.__devices.get(idx)
        if device is None:
            raise RuntimeError(f"Device not selected. "
                               f"Please, select device {idx} before.")
        return device

    def _get_nodemap(self, idx=0):
        nodemap = self.__nodemaps.get(idx)
        if nodemap is None:
            raise RuntimeError(f"Device not selected. Please, select device {idx} "
                               f"before accessing to the nodemap.")
        return nodemap

    def print_available_formats(self, idx=0, do_print=True):
        nodemap = self._get_nodemap(idx)

        # Let's check the current pixel format to return to it later
        currPxForm = nodemap.FindNode("PixelFormat").CurrentEntry().StringValue()
        pxForms = {x.StringValue(): x.Value() for x in
                   nodemap.FindNode("PixelFormat").Entries()}

        valid_formats = []
        for k, v in pxForms.items():
            try:  # trying to set every pixel format
                nodemap.FindNode("PixelFormat").SetCurrentEntry(v)
                valid_formats.append(k)
                print(
                    f"    {k}: Success  < --------------------------- {v}") if do_print else None
            except:
                print(f"    {k}: Failed") if do_print else None

        # Return to original pixel format
        nodemap.FindNode("PixelFormat").SetCurrentEntry(currPxForm)

        return valid_formats

    def set_gain(self, gain: float, idx=0):
        """ Intenta configurar el gain de la càmera. """
        nodemap_remote_device = self._get_nodemap(idx)
        try:
            target_gain = max(gain, 1)  # must be greater than or equal 1
            nodemap_remote_device.FindNode("Gain").SetValue(target_gain)
        except ids_peak.Exception as e:
            raise e

    def get_gain(self, idx=0):
        """Retorna el gain actual amb què treballa la càmera. """
        nodemap_remote_device = self._get_nodemap(idx)
        try:
            current_gain = nodemap_remote_device.FindNode("Gain").Value()
        except ids_peak.Exception as e:
            raise e
        return current_gain

    def set_fps(self, fps: float, idx=0):
        """Intenta configurar les imatges per segon que la càmera capturarà, fins el màxim establert
        per la pròpia càmera."""
        nodemap_remote_device = self._get_nodemap(idx=idx)
        curr_exp = self.get_exposure_time(idx=idx)
        if curr_exp > 1e6/fps:
            self.set_exposure_time(1e6/fps, idx=idx)
        try:
            max_fps = nodemap_remote_device.FindNode("AcquisitionFrameRate").Maximum()
            target_fps = min(max_fps, fps)
            nodemap_remote_device.FindNode("AcquisitionFrameRate").SetValue(target_fps)
        except ids_peak.Exception as e:
            raise e

    def get_fps(self, idx=0):
        """Retorna els fps actuals amb els què treballa la càmera."""
        nodemap_remote_device = self._get_nodemap(idx=idx)
        try:
            current_fps = nodemap_remote_device.FindNode("AcquisitionFrameRate").Value()
        except ids_peak.Exception as e:
            raise e
        return current_fps

    def set_max_fps(self, idx=0):
        """ Intenta configurar el fps màxim de la càmera. """
        nodemap_remote_device = self._get_nodemap(idx=idx)
        exp_time = self.get_exposure_time(idx=idx)
        try:
            max_fps = nodemap_remote_device.FindNode("AcquisitionFrameRate").Maximum()
            target_fps = min(1e6/exp_time, max_fps)
            nodemap_remote_device.FindNode("AcquisitionFrameRate").SetValue(target_fps)
        except ids_peak.Exception as e:
            raise e

    def set_exposure_time(self, etime: float, idx=0):
        nodemap_remote_device = self._get_nodemap(idx=idx)
        try:
            # Hem d'assegurar que el temps es trobi entre el mínim i màxim d'exposició actuals de la càmera
            minexp = nodemap_remote_device.FindNode("ExposureTime").Minimum()
            maxexp = nodemap_remote_device.FindNode("ExposureTime").Maximum()
            target_exposure = max(minexp, min(maxexp, etime))
            nodemap_remote_device.FindNode("ExposureTime").SetValue(target_exposure)
        except ids_peak.Exception as e:
            raise e

    def get_exposure_time(self, idx=0):
        """Retorna el temps d'exposició actual de la càmera, en microsegons."""
        nodemap_remote_device = self._get_nodemap(idx=idx)
        try:
            current_etime = nodemap_remote_device.FindNode("ExposureTime").Value()
        except ids_peak.Exception as e:
            raise e
        return current_etime

    def get_resolution(self, idx=0):
        if not self.__devices:
            raise NameError("Device not selected")
        nodemap_remote_device = self._get_nodemap(idx=idx)
        try:
            width = nodemap_remote_device.FindNode("Width").Value()
            height = nodemap_remote_device.FindNode("Height").Value()
        except ids_peak.Exception as e:
            raise e
        return width, height

    def capture(self, idx=0, binning=1, force8bit=False):
        if not self.__acquisition_ready[idx]:
            raise RuntimeError("Acquisition not ready. Start acquisition before capture.")

        datastream = self.__datastreams[idx]
        # Recuperem el buffer directament de la càmera
        buff = datastream.WaitForFinishedBuffer(500)

        # Recuperem la imatge i fem debayering si cal
        ipl_image = ids_peak_ipl_extension.BufferToImage(buff)
        if not self.__outer_pixel_format[idx]:
            raise RuntimeError("Pixel format not selected")
        converted_image = ipl_image.ConvertTo(self.__outer_pixel_format[idx])

        # Indiquem que el búffer es pot tornar a utilitzar
        datastream.QueueBuffer(buff)

        # Retornem la imatge en format numpy amb les dimensions correctes
        converted_pixel_format = converted_image.PixelFormat()
        if converted_pixel_format.NumChannels() == 1:
            if converted_pixel_format.NumSignificantBitsPerChannel() <= 8 or force8bit:
                converter = converted_image.get_numpy_2D
            else:
                converter = converted_image.get_numpy_2D_16
        else:  # check this, not tested
            if converted_pixel_format.NumSignificantBitsPerChannel() <= 8 or force8bit:
                converter = converted_image.get_numpy_3D
            else:
                converter = converted_image.get_numpy_3D_16
        image_array = converter().copy()

        return image_array

    def __destroy(self):
        try:
            self.__stop_all_acquisitions()
        except Exception as e:
            pass
        
        ids_peak.Library.Close()

    def __del__(self):
        self.__destroy()


class IDSCamera(IDSinterface):
    """ It is just for backward compatibility. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("\n >>> WARNING: IDSCamera class is deprecated. "
              "Use IDSinterface instead. <<<\n")