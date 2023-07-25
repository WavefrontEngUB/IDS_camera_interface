from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension


class IDSCamera(object):
    """IDS Camera interface, keeping all memory and low level bus management opaque
    to the user, for ease of use."""

    def __init__(self):
        ids_peak.Library.Initialize()

        self.__acquisition_ready = False
        self.__pixel_format = None
        self.__resolution = None

        self.__create_device_manager()

        self.__datastreams = []
        self.__nodemap_remote_devices = []
        self.__devices = []

    def __create_device_manager(self):

        self.__device_manager = ids_peak.DeviceManager.Instance()

        self.__device_manager.Update()

        # Si no hem trobat cap càmera, tallem pel dret!
        if self.__device_manager.Devices().empty():
            self.__destroy()
            raise ids_peak.NotFoundException("No devices found!")

    def __setup_data_stream(self, idx=0, print_formats=False):
        device = self.__devices[idx]
        datastreams = device.DataStreams()

        if datastreams.empty():
            self.__destroy()
            raise ids_peak.NotAvailableException("Devie has no DataStream!")

        datastream = datastreams[0].OpenDataStream()
        nodemap_remote_device = device.RemoteDevice().NodeMaps()[0]
        # Preparem captures d'imatge contínues
        try:
            nodemap_remote_device.FindNode("UserSetSelector").SetCurrentEntry("Default")
            nodemap_remote_device.FindNode("UserSetLoad").Execute()
            nodemap_remote_device.FindNode("UserSetLoad").WaitUntilDone()
        except ids_peak.Exception:
            # Userset is not available
            pass

        if print_formats:
            currPxForm = nodemap_remote_device.FindNode(
                "PixelFormat").CurrentEntry().StringValue()
            pxForms = {x.StringValue(): x.Value() for x in
                       nodemap_remote_device.FindNode("PixelFormat").Entries()}

            print(f"Device: {device.ModelName()}  S/N-{device.SerialNumber()} ")
            for k, v in pxForms.items():
                try:
                    nodemap_remote_device.FindNode("PixelFormat").SetCurrentEntry(v)
                    print(f"    {k}: Success  < ---------------------------")
                except:
                    print(f"    {k}: Failed")
            # Return to original pixel format
            nodemap_remote_device.FindNode("PixelFormat").SetCurrentEntry(currPxForm)

        if self.__pixel_format:
            if self.__pixel_format == ids_peak_ipl.PixelFormatName_Mono12:
                try:
                    nodemap_remote_device.FindNode("PixelFormat").SetCurrentEntry(
                        ids_peak_ipl.PixelFormatName_Mono12g24IDS)
                except:
                    raise RuntimeError(f"Pixel format not supported by this device.\n\n"
                                       f"Run IDSCamera.__setup_data_stream(idx={idx}, "
                                       f"print_formats=True) to see available formats.")
        else:
            raise RuntimeError("Set pixel format before select_device() method")

        self.__datastreams.append(datastream)
        self.__nodemap_remote_devices.append(nodemap_remote_device)
        payload_size = nodemap_remote_device.FindNode("PayloadSize").Value()

        buffer_count_max = datastream.NumBuffersAnnouncedMinRequired()
        print(len(self.__nodemap_remote_devices))
        # Allocate and announce image buffers and queue them
        for i in range(buffer_count_max):
            buffer = datastream.AllocAndAnnounceBuffer(payload_size)
            datastream.QueueBuffer(buffer)

    def __setup_nodemap(self):
        self.__nodemap_remote_device = self.__device.RemoteDevice().NodeMaps()[0]

    def __stop_acquisition(self):
        if not self.__devices:
            return
        # Otherwise try to stop acquisition
        try:
            for i, device in enumerate(self.__devices):
                remote_nodemap = device.RemoteDevice().NodeMaps()[0]
                remote_nodemap.FindNode("AcquisitionStop").Execute()

                # Stop and flush datastream
                self.__datastreams[i].KillWait()
                self.__datastreams[i].StopAcquisition(ids_peak.AcquisitionStopMode_Default)
                self.__datastreams[i].Flush(ids_peak.DataStreamFlushMode_DiscardAll)


                # Unlock parameters after acquisition stop
                if self.__nodemap_remote_devices[i] is not None:
                    try:
                        self.__nodemap_remote_devices[i].FindNode("TLParamsLocked").SetValue(0)
                    except Exception as e:
                        raise e

        except Exception as e:
            raise e

        self.__acquisition_running = False

    def get_devices(self):
        return self.__device_manager.Devices()

    def select_device(self, device_idx):
        try:
            device = self.__device_manager.Devices()[device_idx]
        except:
            self.__destroy()
            raise KeyError(f"Device {device_idx} not found")

        # Intenta obrir la càmera
        if not device.IsOpenable():
            self.__destroy()
            raise ids_peak.NotAvailableException(f"Device {device_idx} could not be opened")

        self.__devices.append(device.OpenDevice(ids_peak.DeviceAccessType_Control))

        # Con
        idx = len(self.__devices) - 1
        self.__setup_data_stream(idx=idx)

    def set_gain(self, gain: float, idx=0):
        """Intenta configurar les imatges per segon que la càmera capturarà, fins el màxim establert
        per la pròpia càmera."""
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        try:
            target_gain = max(gain, 1)  # must be greater than or equal 1
            nodemap_remote_device.FindNode("Gain").SetValue(target_gain)
        except ids_peak.Exception as e:
            raise e

    def get_gain(self, idx=0):
        """Retorna els fps actuals amb els què treballa la càmera."""
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        try:
            current_gain = nodemap_remote_device.FindNode("Gain").Value()
        except ids_peak.Exception as e:
            raise e
        return current_gain

    def set_fps(self, fps: float, idx=0):
        """Intenta configurar les imatges per segon que la càmera capturarà, fins el màxim establert
        per la pròpia càmera."""
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
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
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        try:
            current_fps = nodemap_remote_device.FindNode("AcquisitionFrameRate").Value()
        except ids_peak.Exception as e:
            raise e
        return current_fps

    def set_exposure_time(self, etime: float, idx=0):
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
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
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        try:
            current_etime = nodemap_remote_device.FindNode("ExposureTime").Value()
        except ids_peak.Exception as e:
            raise e
        return current_etime

    def get_resolution(self, idx=0):
        if not self.__devices:
            raise NameError("Device not selected")
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        try:
            width = nodemap_remote_device.FindNode("Width").Value()
            height = nodemap_remote_device.FindNode("Height").Value()
        except ids_peak.Exception as e:
            raise e
        return width, height

    def stop_acquisition(self, idx=0):
        """Comença la captura contínua d'imatges amb els paràmetres seleccionats."""
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        device = self.__devices[idx]
        datastream = self.__datastreams[idx]
        try:
            nodemap_remote_device.FindNode("TLParamsLocked").SetValue(0)

            datastream.StopAcquisition()
            nodemap_remote_device.FindNode("AcquisitionStop").Execute()
            nodemap_remote_device.FindNode("AcquisitionStop").WaitUntilDone()
        except Exception as e:
            raise e

        # self.__acquisition_ready = True


    def start_acquisition(self, idx=0):
        """Comença la captura contínua d'imatges amb els paràmetres seleccionats."""
        nodemap_remote_device = self.__nodemap_remote_devices[idx]
        device = self.__devices[idx]
        datastream = self.__datastreams[idx]
        try:
            nodemap_remote_device.FindNode("TLParamsLocked").SetValue(1)

            datastream.StartAcquisition()
            nodemap_remote_device.FindNode("AcquisitionStart").Execute()
            nodemap_remote_device.FindNode("AcquisitionStart").WaitUntilDone()
        except Exception as e:
            raise e

        self.__acquisition_ready = True

    def set_pixel_format(self, kind, idx=0):
        """Selecciona el format en què es guardaran les imatges."""
        if kind == "BGRa8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGRa8
        elif kind == "BGRa10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGRa10
        elif kind == "BGRa12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGRa12
        elif kind == "Mono8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_Mono8
        elif kind == "Mono10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_Mono10
        elif kind == "Mono12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_Mono12
        elif kind == "BayerRG8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerRG8
        elif kind == "BayerRG10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerRG10
        elif kind == "BayerRG12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerRG12
        elif kind == "BayerGR8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGR8
        elif kind == "BayerGR10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGR10
        elif kind == "BayerGR12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGR12
        elif kind == "BayerBG8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerBG8
        elif kind == "BayerBG10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerBG10
        elif kind == "BayerBG12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerBG12
        elif kind == "BayerGB8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGB8
        elif kind == "BayerGB10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGB10
        elif kind == "BayerGB12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BayerGB12
        elif kind == "BGR8":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGR8
        elif kind == "BGR10":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGR10
        elif kind == "BGR12":
            self.__pixel_format = ids_peak_ipl.PixelFormatName_BGR12



    def capture(self, idx=0, binning=1, force8bit=False):
        if not self.__acquisition_ready:
            raise RuntimeError("Acquisition not ready")

        datastream = self.__datastreams[idx]
        # Recuperem el buffer directament de la càmera
        buff = datastream.WaitForFinishedBuffer(500)

        # Recuperem la imatge i fem debayering si cal
        ipl_image = ids_peak_ipl_extension.BufferToImage(buff)
        if not self.__pixel_format:
            raise RuntimeError("Pixel format not selected")
        converted_image = ipl_image.ConvertTo(self.__pixel_format)

        # Indiquem que el búffer es pot tornar a utilitzar
        datastream.QueueBuffer(buff)

        # Retornem la imatge en format numpy amb les dimensions correctes
        inner_pixel_format = converted_image.PixelFormat()
        if inner_pixel_format.NumChannels() == 1:
            if inner_pixel_format.NumSignificantBitsPerChannel() <= 8 or force8bit:
                converter = converted_image.get_numpy_2D
            else:
                converter = converted_image.get_numpy_2D_16
        else:  # check this, not tested
            converter = converted_image.get_numpy_3D
        image_array = converter().copy()

        return image_array

    def __destroy(self):
        try:
            self.__stop_acquisition()
        except Exception as e:
            pass
        
        ids_peak.Library.Close()

    def __del__(self):
        self.__destroy()

