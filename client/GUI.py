"""
basic gui
"""

from PyQt5.QtWidgets import QPushButton, QListWidget, QGraphicsView, QListWidgetItem, QGraphicsScene, QFileDialog, QAction
from PyQt5.uic import loadUi
from os.path import expanduser, dirname, basename, isfile
from model import Clip


class GUI:
    """
    GUI class
    """

    def __init__(self, guiFilePath, app):
        """
        constructor

        @param guiFilePath path to the ui file
        @param app the QApplication object
        """

        self.app = app
        self.clip = Clip()
        self.changed = False  # Indicates whether the file has been changed

        self.ui = loadUi(guiFilePath)
        self.__initRightSidebar()
        self.__initTopBar()

        # Left canvas
        self.canvas = self.ui.findChild(QGraphicsView, 'starCanvas')
        self.scene = QGraphicsScene(self.canvas)
        self.canvas.setScene(self.scene)

        self.ui.show()

    def __initRightSidebar(self):
        """
        initiates the widgets of the right sidebar
        """

        addFrameButton = self.ui.findChild(QPushButton, 'addButton')
        addFrameButton.clicked.connect(self.buttonAddFrame)

        nextFrameButton = self.ui.findChild(QPushButton, 'nextButton')
        nextFrameButton.clicked.connect(self.buttonNextFrame)

        prevFrameButton = self.ui.findChild(QPushButton, 'prevButton')
        prevFrameButton.clicked.connect(self.buttonPrevFrame)

        self.delFrameButton = self.ui.findChild(QPushButton, 'deleteButton')
        self.moveUpButton = self.ui.findChild(QPushButton, 'moveUpButton')
        self.moveDownButton = self.ui.findChild(QPushButton, 'moveDownButton')

        self.frameList = self.ui.findChild(QListWidget, 'frameList')
        self.frameList.currentRowChanged.connect(self.frameListChangeRow)

        #self.addFrameButton.clicked.connect(self.test)

    def __initTopBar(self):
        """
        initiates the top bar
        """
        openActionButton = self.ui.findChild(QAction, 'actionOpen')
        openActionButton.triggered.connect(self.actionOpenNsc)

        saveAsActionButton = self.ui.findChild(QAction, 'actionSave_as')
        saveAsActionButton.triggered.connect(self.actionSaveAsNsc)

        saveActionButton = self.ui.findChild(QAction, 'actionSave')
        saveActionButton.triggered.connect(self.actionSaveNsc)

    # === File management ===

    def actionOpenNsc(self, event):
        """
        opens a nightsky clip file

        @param event QEvent object of the event
        """

        startDir = expanduser('~')
        if self.clip.filePath:
            startDir = dirname(self.clip.filePath)

        filePath = QFileDialog.getOpenFileName(self.ui, self.ui.tr('Open Nightsky Clip'), startDir, self.ui.tr('Nightsky Clip Files (*.nsc)'))[0]

        # Load file
        try:
            self.clip = Clip(filePath)
            self.updateFrameList()
        except FileNotFoundError:
            # Skip because of abort
            pass

    def actionSaveAsNsc(self, event):
        """
        saves a nightsky clip file

        @param event QEvent object of the event
        """

        startFilePath = expanduser('~')
        if self.clip.filePath:
            startFilePath = self.clip.filePath

        filePath = QFileDialog.getSaveFileName(self.ui, self.ui.tr('Save Nightsky Clip'), startFilePath, self.ui.tr('Nightsky Clip Files (*.nsc)'))[0]

        fileName = basename(filePath)
        if (fileName != ''):
            # Check if suffix is given and add it if necessary
            if fileName.split('.')[-1] != 'nsc':
                filePath += '.nsc'

            self.clip.save(filePath)

    def actionSaveNsc(self, event):
        """
        saves a nightsky clip file, if there is already a filename

        @param event QEvent object of the event
        """

        try:
            self.clip.save()
        except Clip.NoFilePathException:
            self.actionSaveAsNsc(event)

    # ========

    # === Frame management ===

    def updateFrameList(self):
        """
        updates the frame list
        """

        self.frameList.clear()
        for i in range(len(self.clip.frames)):
            item = QListWidgetItem('Frame {0:d}'.format(i))
            self.frameList.addItem(item)

        self.frameList.setCurrentRow(self.clip.activeFrame)

    def frameListChangeRow(self, row):
        """
        event handler for changing active row

        @param row the new current row
        """

        try:
            self.clip.setActiveFrame(row)
        except Clip.FrameIdOutOfBoundException:
            # On updateFrameList row is -1
            pass

    def buttonAddFrame(self, event):
        """
        adds a new frame
        """

        if self.clip.size == 0:
            newPos = 0
        else:
            newPos = self.frameList.currentRow() + 1

        self.clip.addFrame()
        self.clip.setActiveFrame(self.clip.size - 1)
        self.clip.moveFrame(newPos)
        self.updateFrameList()

    def buttonNextFrame(self, event):
        """
        Changes the currently active frame to the next frame.
        If the end is reached, the active frame remains the last frame.
        """

        try:
            self.clip.nextFrame()
        except Clip.FrameIdOutOfBoundException:
            pass
        self.updateFrameList()

    def buttonPrevFrame(self, event):
        """
        Changes the currently active frame to the previous frame.
        If the beginning is reached, the active frame remains the first frame.
        """

        try:
            self.clip.prevFrame()
        except Clip.FrameIdOutOfBoundException:
            pass
        self.updateFrameList()
