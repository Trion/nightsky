"""
basic gui
"""

from PyQt5.QtWidgets import QPushButton, QListWidget, QGraphicsView,\
    QListWidgetItem, QGraphicsScene, QFileDialog, QAction
from PyQt5.uic import loadUi
from os.path import expanduser, dirname, basename
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
        Initiates the widgets of the right sidebar.
        """

        nextFrameButton = self.ui.findChild(QPushButton, 'nextButton')
        nextFrameButton.clicked.connect(self.buttonNextFrame)

        prevFrameButton = self.ui.findChild(QPushButton, 'prevButton')
        prevFrameButton.clicked.connect(self.buttonPrevFrame)

        addFrameButton = self.ui.findChild(QPushButton, 'addButton')
        addFrameButton.clicked.connect(self.buttonAddFrame)

        copyFrameButton = self.ui.findChild(QPushButton, 'copyButton')
        copyFrameButton.clicked.connect(self.buttonCopyFrame)

        delFrameButton = self.ui.findChild(QPushButton, 'deleteButton')
        delFrameButton.clicked.connect(self.buttonDeleteFrame)

        moveUpButton = self.ui.findChild(QPushButton, 'moveUpButton')
        moveUpButton.clicked.connect(self.buttonMoveUp)

        moveDownButton = self.ui.findChild(QPushButton, 'moveDownButton')
        moveDownButton.clicked.connect(self.buttonMoveDown)

        self.frameList = self.ui.findChild(QListWidget, 'frameList')
        self.frameList.currentRowChanged.connect(self.frameListChangeRow)
        # Setup drag and drop support
        frameListModel = self.frameList.model()
        frameListModel.rowsMoved.connect(self.frameListMoveFrame)

    def __initTopBar(self):
        """
        Initiates the top bar.
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
        Opens a nightsky clip file.

        @param event QEvent object of the event
        """

        startDir = expanduser('~')
        if self.clip.filePath:
            startDir = dirname(self.clip.filePath)

        filePath = QFileDialog.getOpenFileName(
            self.ui, self.ui.tr('Open Nightsky Clip'), startDir,
            self.ui.tr('Nightsky Clip Files (*.nsc)'))[0]

        # Load file
        try:
            self.clip = Clip(filePath)
            self.updateFrameList()
        except FileNotFoundError:
            # Skip because of abort
            pass

    def actionSaveAsNsc(self, event):
        """
        Saves a nightsky clip file.

        @param event QEvent object of the event
        """

        startFilePath = expanduser('~')
        if self.clip.filePath:
            startFilePath = self.clip.filePath

        filePath = QFileDialog.getSaveFileName(
            self.ui, self.ui.tr('Save Nightsky Clip'), startFilePath,
            self.ui.tr('Nightsky Clip Files (*.nsc)'))[0]

        fileName = basename(filePath)
        if (fileName != ''):
            # Check if suffix is given and add it if necessary
            if fileName.split('.')[-1] != 'nsc':
                filePath += '.nsc'

            self.clip.save(filePath)

    def actionSaveNsc(self, event):
        """
        Saves a nightsky clip file, if there is already a filename.

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
        Updates the frame list.
        """

        self.frameList.clear()
        for i in range(len(self.clip.frames)):
            item = QListWidgetItem('Frame {0:d}'.format(i))
            self.frameList.addItem(item)

        self.frameList.setCurrentRow(self.clip.activeFrame)

    def frameListChangeRow(self, row):
        """
        Event handler for changing active row.

        @param row the new current row
        """

        try:
            self.clip.setActiveFrame(row)
        except Clip.FrameIdOutOfBoundException:
            # On updateFrameList row is -1
            pass

    def frameListMoveFrame(self, event):
        """
        Moves a frame by a drag and drop event.
        """

        # Well, thats pretty ugly, but the easiest way for my intentions
        newPos = self.frameList.currentRow()
        self.clip.moveFrame(newPos)
        self.updateFrameList()

    def buttonAddFrame(self, event):
        """
        Adds a new frame.
        """

        if self.clip.size == 0:
            newPos = 0
        else:
            newPos = self.frameList.currentRow() + 1

        self.clip.insertFrame(newPos)
        if newPos == 0:
            self.clip.setActiveFrame(newPos)
        else:
            self.clip.setActiveFrame(newPos - 1)
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

    def buttonDeleteFrame(self, event):
        """
        Removes the currently active frame.
        """
        self.clip.removeFrame(self.clip.activeFrame)
        self.updateFrameList()

    def buttonCopyFrame(self, event):
        """
        Copies the currently active frame.
        """
        self.clip.copyFrame()
        self.updateFrameList()

    def buttonMoveUp(self):
        """
        Moves the currently active frame down.
        """
        self.clip.moveFrameUp()
        self.updateFrameList()

    def buttonMoveDown(self):
        """
        Moves the currently active frame up.
        """
        self.clip.moveFrameDown()
        self.updateFrameList()
