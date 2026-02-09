import os
import Imath
import OpenEXR
import numpy as np
from engine.resources.image.image import Image
from engine.resources.image.enums import ImageFormat, ImageColorSpace
from engine.resources.image.loaders.image_format_loader import ImageFormatLoader


class ImageLoaderEXR(ImageFormatLoader):
    def handles_path(self, path: str) -> bool:
        return os.path.splitext(path)[1].lower() == ".exr"

    def load(self, path: str) -> Image:
        if not OpenEXR.isOpenExrFile(path):
            raise ValueError(f"File is not a valid EXR: {path}")

        exr_file = OpenEXR.InputFile(path)
        header = exr_file.header()
        dw = header["dataWindow"]
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        available_channels = set(header["channels"].keys())
        pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)
        numpy_channels = []
        if {"R", "G", "B", "A"}.issubset(available_channels):
            read_channels = ["R", "G", "B", "A"]
            image_format = ImageFormat.RGBAF
            raw_bytes_list = exr_file.channels(read_channels, pixel_type)
            for raw in raw_bytes_list:
                numpy_channels.append(self._bytes_to_np(raw, width, height))

        elif {"R", "G", "B"}.issubset(available_channels):
            read_channels = ["R", "G", "B"]
            image_format = ImageFormat.RGBF
            raw_bytes_list = exr_file.channels(read_channels, pixel_type)
            for raw in raw_bytes_list:
                numpy_channels.append(self._bytes_to_np(raw, width, height))

        elif "Y" in available_channels:
            image_format = ImageFormat.RGBF
            raw_bytes_list = exr_file.channels(["Y"], pixel_type)
            y_channel = self._bytes_to_np(raw_bytes_list[0], width, height)
            numpy_channels = [y_channel, y_channel, y_channel]

        else:
            raise ValueError(
                f"Unsupported EXR Channel layout in '{path}'. "
                f"Found channels: {list(available_channels)}. "
                "Expected ['R','G','B'], ['Y'], or ['R','G','B','A']."
            )

        interleaved_data = np.dstack(numpy_channels)

        img = Image()
        img.width = width
        img.height = height
        img.format = image_format
        img.color_space = ImageColorSpace.LINEAR
        img.data = interleaved_data.tobytes()

        return img

    def _bytes_to_np(self, raw_bytes: bytes, width: int, height: int) -> np.ndarray:
        """Helper to convert raw EXR bytes to shaped float32 numpy array."""
        arr = np.frombuffer(raw_bytes, dtype=np.float32)
        return arr.reshape((height, width))
