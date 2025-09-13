
from collections import namedtuple

import numpy as np

Position = namedtuple("Position", "x y z w", defaults=(0, 0, 0, 1))
Color = namedtuple("Color", "r g b a", defaults=(0, 0, 0, 1))
TexCoord = namedtuple("TexCoord", "s t")
PointSize = namedtuple("PointSize", "size")


class Point(np.ndarray):
    """
    [x, y, z, w, r, g, b, a, s, t, point_size]

    Slices:
        position:      [0:4]  -> (x, y, z, w)
        color:         [4:8]  -> (r, g, b, a)
        texture_coord: [8:10] -> (s, t)
        point_size:    [10]   -> (size)

    Defaults:
        position:      (0, 0, 0, 1)
        color:         (0, 0, 0, 1)
        texture_coord: (0, 0)
        point_size:    (0,)
    """

    # Layout constants
    POSITION = slice(0, 4)
    COLOR = slice(4, 8)
    TEXTURE_COORD = slice(8, 10)
    POINT_SIZE = slice(10, 11)

    LENGTH = 11

    # Component defaults
    _DEFAULT_POSITION = np.array([0.0, 0.0, 0.0, 1.0])
    _DEFAULT_COLOR = np.array([0.0, 0.0, 0.0, 1.0])
    _DEFAULT_TEXTURE_COORD = np.array([0.0, 0.0])
    _DEFAULT_POINT_SIZE = np.array([0.0])

    def __new__(cls) -> "Point":
        """Instantiate the """
        obj = np.empty(cls.LENGTH, dtype=np.float64)
        obj[cls.POSITION] = cls._DEFAULT_POSITION
        obj[cls.COLOR] = cls._DEFAULT_COLOR
        obj[cls.TEXTURE_COORD] = cls._DEFAULT_TEXTURE_COORD
        obj[cls.POINT_SIZE] = cls._DEFAULT_POINT_SIZE

        return obj.view(cls)

    def __array_finalize__(self, obj: np.ndarray | None) -> None:
        """Required by ndarray subclassing; nothing extra to finalize."""
        if obj is None:
            return

    def __str__(self):
        return f"Point[{self.position}, {self.color}, {self.texture_coord}, {self.point_size}]"

    def divide_by_w(self) -> "Point":
        """Perform the divide by w operation"""
        w = self.position.w
        self = self / w
        self[3] = 1 / w
        return self
    
    def undo_divide_by_w(self) -> "Point":
        """
        Undo the divide by w operation, making sure NOT to touch x, y, & z, which are already
        modified to fit our viewport
        """
        position = self.position
        self: Point = self / position.w
        # Save our position data as-is
        self.position = position
        return self

    def to_device_coordinates(self, width: int, height: int) -> "Point":
        """Perform the translation to device coordinates"""
        # Normalized device coordinates will be -1 to 1 in x, y, z.
        # Perform a viewport transformation to move these normalized coordinates into device
        # coordinates by adding 1, dividing by 2, and multiplying by height (y) or width (x)
        self[0] = (self[0] + 1) * width / 2
        self[1] = (self[1] + 1) * height / 2
        return self

    @property
    def position(self) -> Position:
        return Position(*map(float, self[self.POSITION]))

    @position.setter
    def position(self, value: Position) -> None:
        self[self.POSITION] = value

    @property
    def integer_position(self) -> Position:
        """Returns the position cast to integers for printing"""
        return Position(*map(int, self[self.POSITION]))

    @property
    def color(self) -> Color:
        return Color(*map(float, self[self.COLOR]))

    @color.setter
    def color(self, value: Color) -> None:
        self[self.COLOR] = value

    @property
    def rgba_color(self) -> Color:
        """Returns the color vector * 255 as ints for printing"""
        return Color(*map(int, self[self.COLOR] * 255))
    
    @property
    def srgb_color(self) -> Color:
        """Returns the color vector translated from linear to sRGB"""
        colors = self[self.COLOR]
        # Preserve the alpha channel since we do not translate it
        alpha = colors[3]
        colors = np.where(
            colors <= 0.0031308,
            colors * 12.92,
            (colors ** (1/2.4)) * 1.055 - 0.055
        )
        colors[3] = alpha
        return Color(*map(int, colors * 255))

    @property
    def texture_coord(self) -> TexCoord:
        return TexCoord(*map(float, self[self.TEXTURE_COORD]))

    @texture_coord.setter
    def texture_coord(self, value: TexCoord) -> None:
        self[self.TEXTURE_COORD] = value

    @property
    def point_size(self) -> PointSize:
        return PointSize(*map(float, self[self.POINT_SIZE]))

    @point_size.setter
    def point_size(self, value: PointSize) -> None:
        self[self.POINT_SIZE] = value

