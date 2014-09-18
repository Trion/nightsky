"""
Renders the stars onto the canvas
"""
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QGraphicsEllipseItem


class StarRenderer:
    """
    The star renderer
    """

    def __init__(self, scene, starPositions, clip):
        """
        constructor

        @param scene the scene the stars are put on
        @param starPositions a list/tuple of tuples with the size of 2,
            which represents the position of the stars in the format (x, y)
        @param clip the clip object
        """

        # Color of the stars in on and off mode
        self.offBrush = QBrush(QColor(100, 100, 100))
        self.onBrush = QBrush(QColor(200, 200, 200))

        self.clip = clip

        self.stars = []
        starId = 0
        for pos in starPositions:
            star = StarEllipse(starId, pos, self.offBrush)
            scene.addItem(star)
            self.stars.append(star)
            starId += 1

        self.update()

    def setClip(self, clip):
        """
        Sets the current clip.

        @param clip the new clip
        """
        self.clip = clip
        self.update()

    def update(self):
        """
        Updates the canvas.
        """

        setup = self.clip.getSetup()
        for star in self.stars:
            if setup[star.starId]:
                star.setBrush(self.onBrush)
            else:
                star.setBrush(self.offBrush)


class StarEllipse(QGraphicsEllipseItem):
    """
    A star to render.
    """

    def __init__(self, id, position, brush):
        """
        constructor

        @param id id of the star
        @param positon position of the star
        @param brush the initial brush
        """
        super().__init__(position[0], position[1], 13, 13)
        self.setBrush(brush)
        self.starId = id
