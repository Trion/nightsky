"""
basic gui
"""

from PyQt5.QtWidgets import QPushButton, QListWidget, QGraphicsView,\
    QListWidgetItem, QGraphicsScene, QFileDialog, QAction, QMenu, QMenuBar,\
    QLabel, QProgressBar
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from os.path import expanduser, dirname, basename
from model import Clip
from StarRenderer import StarRenderer
from Communicator import Communicator
import time


class GUI:
    """
    GUI class
    """

    def __init__(self, app):
        """
        constructor

        @param guiFilePath path to the ui file
        @param app the QApplication object
        """

        self.app = app
        self.clip = Clip()
        self.clip.addFrame()  # Add initial frame
        self.changed = False  # Indicates whether the file has been changed

        self.ui = loadUi('resources/gui.ui')
        self.__initRightSidebar()
        self.__initTopBar()

        # Left canvas
        sceneView = self.ui.findChild(QGraphicsView, 'starCanvas')
        scene = QGraphicsScene(sceneView)
        sceneView.setScene(scene)

        # Overwrite the mouse press event
        def sceneMousePressEvent(event):
            """
            Catches the mouse press event of the scene.

            @param event the event object, that belongs to the mouse press
                event
            """
            star = scene.itemAt(event.scenePos(), sceneView.transform())

            if star is not None:
                self.clip.toggleStar(star.starId)
                self.starRenderer.update()

        scene.mousePressEvent = sceneMousePressEvent

        starPositions = [(643, 35), (523, 50), (333, 20), (265, 58),
                         (202, 28), (120, 25),
                         (634, 92), (468, 80), (411, 49), (269, 80), (108, 78),
                         (80, 55),
                         (707, 145), (580, 155), (411, 152), (274, 100),
                         (130, 87), (22, 97),
                         (658, 227), (479, 172), (441, 160), (335, 213),
                         (232, 152), (67, 168),
                         (718, 262), (520, 202), (468, 250), (332, 258),
                         (194, 214), (105, 228)]
        self.starRenderer = StarRenderer(scene, starPositions, self.clip)
        self.ui.show()

        self.updateFrameList()
        self.frameList.setCurrentRow(0)

        # Setup animation ability
        self.animationThread = AnimationThread(self)
        self.animationThread.finished.connect(self.animationStopped)

        # Upload to arduino

        # Device search
        self.searchDevicesDialog = loadUi('resources/searchDevicesDialog.ui')
        self.searchDevicesDialog.setWindowFlags(Qt.WindowTitleHint)
        self.searchDevicesThread = SearchDevicesThread()
        self.searchDevicesThread.completed.connect(self.searchDevicesDialog.close)

        self.notFoundDialog = loadUi('resources/notFoundDialog.ui')  # Dialog if no device is found

        # Choose device
        self.choosePortDialog = loadUi('resources/choosePort.ui')

        # Transmission state
        self.transmissionStateDialog = \
            loadUi('resources/transmissionStateDialog.ui')
        self.transmissionThread = TransmissionThread()
        self.transmissionThread.finished.connect(self.transmissionStateDialog.close)
        self.transmissionThread.startTransmissionProcess.connect(self.startTransmission)
        self.transmissionThread.setText.connect(self.setTransmissionStateText)
        self.transmissionThread.addProgress.connect(self.addTransmissionProgress)
        self.transmissionThread.setProgressLimits.connect(self.setTransmissionProgressLimits)
        self.transmissionThread.aborted.connect(self.disableTransmissionAbortionButton)
        self.transmissionThread.completed.connect(self.disableTransmissionAbortionButton)
        abortButton = self.transmissionStateDialog.findChild(QPushButton,
                                                             'abortButton')
        abortButton.clicked.connect(self.transmissionThread.abort)

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

        newActionButton = self.ui.findChild(QAction, 'actionNew')
        newActionButton.triggered.connect(self.actionNew)

        toggleAllStarsActionButton = self.ui.findChild(
            QAction, 'actionToggle_all_stars')
        toggleAllStarsActionButton.triggered.connect(self.actionToggleAllStars)

        allStarsOnActionButton = self.ui.findChild(QAction,
                                                   'actionAll_stars_on')
        allStarsOnActionButton.triggered.connect(self.actionAllStarsOn)

        allStarsOffActionButton = self.ui.findChild(QAction,
                                                    'actionAll_stars_off')
        allStarsOffActionButton.triggered.connect(self.actionAllStarsOff)

        self.runClipActionButton = self.ui.findChild(QAction, 'actionRun_clip')
        self.runClipActionButton.triggered.connect(self.actionRunClip)

        self.stopClipActionButton = self.ui.findChild(QAction,
                                                      'actionStop_clip')
        self.stopClipActionButton.triggered.connect(self.actionStopClip)

        uploadActionButton = self.ui.findChild(QAction, 'actionUpload')
        uploadActionButton.triggered.connect(self.actionUpload)

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
            self.starRenderer.setClip(self.clip)
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

    def actionNew(self, event):
        """
        Creates a new clip.
        """
        self.clip = Clip()
        self.clip.addFrame()
        self.starRenderer.setClip(self.clip)
        self.updateFrameList()

    def actionToggleAllStars(self, event):
        """
        Toggles all stars.
        """
        for i in range(30):
            self.clip.toggleStar(i)
        self.starRenderer.update()

    def actionAllStarsOn(self, event):
        """
        Toggles all stars.
        """
        for i in range(30):
            self.clip.setStarState(i, True)
        self.starRenderer.update()

    def actionAllStarsOff(self, event):
        """
        Toggles all stars.
        """
        for i in range(30):
            self.clip.setStarState(i, False)
        self.starRenderer.update()

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
        self.starRenderer.update()

    def frameListChangeRow(self, row):
        """
        Event handler for changing active row.

        @param row the new current row
        """

        try:
            self.clip.setActiveFrame(row)
            self.starRenderer.update()
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
        # Add obligatory frame
        if self.clip.size == 0:
            self.clip.addFrame()

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

    # ========

    # === Animation ===
    def actionRunClip(self):
        """
        Plays the animation.
        """
        # Disable unnecessary widgets, to avoid problems in the animation
        for child in self.ui.children():
            child.setEnabled(False)
        self.ui.findChild(QMenuBar, 'menubar').setEnabled(True)
        self.ui.findChild(QMenu, 'menuRun').setEnabled(True)
        self.stopClipActionButton.setEnabled(True)

        self.animationThread.start()

    def actionStopClip(self):
        """
        Stops the animation.
        """
        self.animationThread.stop()

    def animationStopped(self):
        """
        Frees all gui elements when the animation is stopped
        """
        for child in self.ui.children():
            child.setEnabled(True)
        self.stopClipActionButton.setEnabled(False)

        self.animationThread = AnimationThread(self)
        self.animationThread.finished.connect(self.animationStopped)

    # ========

    # === Upload ===
    def actionUpload(self):
        """
        Executes the upload.
        """
        self.searchDevicesThread.start()
        self.searchDevicesDialog.exec()
        ports = self.searchDevicesThread.getPorts()

        if len(ports) == 0:
            # No Device found
            self.notFoundDialog.exec()
        else:
            portsList = self.choosePortDialog.findChild(QListWidget,
                                                        'portsList')
            portsList.clear()
            for port in ports:
                item = QListWidgetItem(port)
                portsList.addItem(item)
                portsList.setCurrentRow(0)

            if self.choosePortDialog.exec() == 1:
                # ok-button pressed
                self.transmissionThread.port = portsList.currentItem().text()
                self.transmissionThread.clip = self.clip
                self.transmissionStateDialog.show()
                self.transmissionThread.start()

    def startTransmission(self):
        """
        Starts the transmission for the gui.
        """
        bar = self.transmissionStateDialog.findChild(QProgressBar, 'progressBar')
        bar.setValue(0)
        bar.setMinimum(0)
        # Set temporary max size (+ 3 because of compression, start and end)
        bar.setMaximum(self.clip.size + 3)
        abortButton = self.transmissionStateDialog.findChild(QPushButton, 'abortButton')
        abortButton.setEnabled(True)

    def setTransmissionProgressLimits(self, min, max):
        """
        Sets the min and max of the transmission progressbar.

        @param min minimum for bar
        @param max maximum for bar
        """
        bar = self.transmissionStateDialog.findChild(QProgressBar, 'progressBar')
        bar.setMinimum(min)
        bar.setMaximum(max)

    def setTransmissionStateText(self, msg):
        """
        Sets the text of the transmission state dialog

        @param msg the text that should be shown
        """
        label = self.transmissionStateDialog.findChild(QLabel, 'stateLabel')
        label.setText(msg)

    def addTransmissionProgress(self):
        """
        Adds progress to the progressbar.
        """
        bar = self.transmissionStateDialog.findChild(QProgressBar, 'progressBar')
        bar.setValue(bar.value() + 1)

    def disableTransmissionAbortionButton(self):
        """
        Disables the abort button in the transmission state dialog.
        """
        abortButton = self.transmissionStateDialog.findChild(QPushButton, 'abortButton')
        abortButton.setEnabled(False)


class AnimationThread(QThread):
    """
    Thread class to run the animation
    """

    TIME_STEP_DURATION = 100  # Duration of a time step in ms

    def __init__(self, gui):
        """
        constructor

        @param gui instance of the GUI class
        """
        super().__init__()
        self.stopped = False
        self.gui = gui

    def run(self):
        """
        Runs the thread.
        """

        clip = self.gui.clip
        while not self.stopped:
            if clip.activeFrame == clip.size - 1:
                clip.setActiveFrame(0)
            else:
                clip.nextFrame()
            self.gui.frameList.setCurrentRow(self.gui.clip.activeFrame)
            self.gui.starRenderer.update()
            self.msleep(self.__class__.TIME_STEP_DURATION)

        self.stopped = False  # Set not stopped to enabled restart

    def stop(self):
        """
        Stops the animation thread.
        """
        if self.isRunning():
            self.stopped = True


class SearchDevicesThread(QThread):
    """
    Thread for search dialog
    """

    completed = pyqtSignal()

    def __init__(self):
        """
        constructor
        """
        super().__init__()
        self.ports = None

    def run(self):
        """
        Run method
        """
        self.ports = Communicator.getPorts()
        self.completed.emit()

    def getPorts(self):
        """
        Closes the dialog.
        """
        return self.ports


class TransmissionThread(QThread):
    """
    Thread class to run the transmission
    """

    # Signals to make the gui responsive
    startTransmissionProcess = pyqtSignal()
    setText = pyqtSignal(str)
    setProgressLimits = pyqtSignal(int, int)
    addProgress = pyqtSignal()
    aborted = pyqtSignal()
    completed = pyqtSignal()

    def __init__(self):
        """
        constructor
        """
        super().__init__()
        self.clip = None
        self.port = None
        self.abortionState = False

    def run(self):
        """
        Runs the thread.
        """
        self.abortionState = False
        self.startTransmissionProcess.emit()

        if self.abortionState:
            return

        # Clip compression
        self.setText.emit('Compress frames...')
        compressedFrames = self.clip.export()
        clipLength = len(compressedFrames)
        self.setProgressLimits.emit(0, clipLength + 3)
        self.addProgress.emit()

        if self.abortionState:
            return

        # Handshake
        self.setText.emit('Start transmission...')
        Communicator.start(self.port)
        self.addProgress.emit()

        if self.abortionState:
            self.setText.emit('Abort transmission...')
            Communicator.end()
            return

        # Transmission of frames
        i = 0
        for frame in compressedFrames:
            self.setText.emit('Transmit frame {0:d} of {1:d}...'
                          .format(i, clipLength))
            Communicator.transmitFrame(frame)
            self.addProgress.emit()
            if self.abortionState:
                self.setText.emit('Abort at frame {0:d} of {1:d}...'
                              .format(i, clipLength))
                Communicator.end()
                return
            i += 1

        self.completed.emit()

        # Handshake for end
        self.setText.emit('Complete transmission...')
        Communicator.end()
        self.addProgress.emit()

        self.setText.emit('Transmission complete...')
        time.sleep(2)

    def abort(self):
        """
        Aborts the transmission.
        """
        self.abortionState = True
        self.aborted.emit()
