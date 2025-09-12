
from collections import namedtuple

import numpy as np

Position = namedtuple("Position", "x y z w", defaults=(0, 0, 0, 1))
Color = namedtuple("Color", "r g b a", defaults=(0, 0, 0, 1))
TexCoord = namedtuple("TexCoord", "s t")
PointSize = namedtuple("PointSize", "size")
Element = namedtuple("Element", "index")


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

    @property
    def position(self) -> Position:
        return Position(*map(float, self[self.POSITION]))

    @position.setter
    def position(self, value: Position) -> None:
        self[self.POSITION] = value

    @property
    def color(self) -> Color:
        return Color(*map(float, self[self.COLOR]))

    @color.setter
    def color(self, value: Color) -> None:
        self[self.COLOR] = value

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

