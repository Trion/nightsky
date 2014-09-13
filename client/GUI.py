"""
basic gui
"""

from PyQt5.QtWidgets import QApplication, QPushButton, QListWidget, QGraphicsView, QListWidgetItem, QGraphicsScene, QFileDialog, QAction
#from PyQt5.QtGui import QBrush, QColor
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
        self.changed = False # Indicates whether the file has been changed

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

        self.addFrameButton = self.ui.findChild(QPushButton, 'addButton')
        self.delFrameButton = self.ui.findChild(QPushButton, 'deleteButton')
        self.nextFrameButton = self.ui.findChild(QPushButton, 'nextButton')
        self.prevFrameButton = self.ui.findChild(QPushButton, 'prevButton')
        self.moveUpButton = self.ui.findChild(QPushButton, 'moveUpButton')
        self.moveDownButton = self.ui.findChild(QPushButton, 'moveDownButton')
        self.frameList = self.ui.findChild(QListWidget, 'frameList')

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

    def actionOpenNsc(self, event):
        """
        opens a nightsky clip file

        @param event QEvent object of the event
        """

        startDir = expanduser('~')
        if self.clip.filePath:
            startDir = dirname(self.clip.filePath)

        filePath = QFileDialog.getOpenFileName(self.ui, self.ui.tr('Open Nightsky Clip'), startDir, self.ui.tr('Nightsky Clip Files (*.nsc)'))[0];

        # Load file
        try:
            self.clip = Clip(filePath)
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

        filePath = QFileDialog.getSaveFileName(self.ui, self.ui.tr('Save Nightsky Clip'), startFilePath, self.ui.tr('Nightsky Clip Files (*.nsc)'))[0];

        fileName = basename(filePath)
        if (fileName != ''):
            # Check if suffix is given and add it if necessary
            if fileName.split('.')[-1] != 'nsc':
                filePath += '.nsc'

            if isfile(filePath):
                # TODO ask if you wanna save, because the file already exist
                pass

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
