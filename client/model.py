"""
Models to represent the clip
"""

import json
from array import array


class Clip:
    """
    Represents a clip
    """

    class FrameIdOutOfBoundException(Exception):
        """
        Exception for frame ids, which are out of bound.
        """

        def __init__(self, frameId):
            """
            constructor

            @param frameId id you tried to access
            """
            super().__init__(self,
                             'Frame {0:d} is out of bound.'.format(frameId))

    class NoFilePathException(Exception):
        """
        Exception for missing file path
        """

        def __init__(self):
            """
            constructor
            """
            super().__init__(self, 'Missing file path.')

    def __init__(self, filePath=None):
        """
        constructor

        @param filePath name of file, where a clip could be saved
        """
        self.filePath = filePath
        self.curFrame = -1
        self.frames = []
        if filePath is not None:
            self.load(filePath)

    @property
    def size(self):
        """
        returns the number of frames within the clip

        @return the amount of frames
        """
        return len(self.frames)

    @property
    def activeFrame(self):
        """
        returns the Id of the currently active frame
        """
        return self.curFrame

    # ==== Frame management ====
    def setActiveFrame(self, frameId):
        """
        change the currently active frame

        @param frameId id of the next active frame
        @raise FrameIdOutOfBoundException frameId is out of bound
        """

        if frameId < 0 or frameId >= len(self.frames):
            raise self.__class__.FrameIdOutOfBoundException(frameId)

        self.curFrame = frameId

    def nextFrame(self):
        """
        sets the current frame to the next frame

        @raise FrameIdOutOfBoundException end of clip
        """
        self.setActiveFrame(self.curFrame+1)

    def prevFrame(self):
        """
        sets the current frame to the previous frame

        @raise FrameIdOutOfBoundException end of clip
        """
        self.setActiveFrame(self.curFrame-1)

    def moveFrame(self, newPos):
        """
        Moves the current frame to the new position.
        If the new position is out of bound, the frame will be put to the end
        respectively to the beginning of the frame list.

        @param newPos index of the new position
        """

        # Move the frame
        frame = self.frames[self.curFrame]
        del self.frames[self.curFrame]
        self.frames.insert(newPos, frame)

        # Set current frame to the new position
        if newPos < 0:
            self.curFrame = 0
        elif newPos > len(self.frames) - 1:
            self.curFrame = len(self.frames) - 1
        else:
            self.curFrame = newPos

    def moveFrameUp(self):
        """
        Moves the currently active frame up.
        If the active frame is the first one, nothing happens.
        """
        self.moveFrame(self.curFrame-1)

    def moveFrameDown(self):
        """
        Moves the currently active frame down.
        If the active frame is the last one, nothing happens.
        """
        self.moveFrame(self.curFrame+1)

    def addFrame(self):
        """
        adds a new frame
        """
        setup = [False for i in range(30)]
        self.frames.append(Frame(setup))

    def insertFrame(self, pos):
        """
        Inserts a new frame at the desired position.

        @param pos position of the new frame as index
        """
        setup = [False for i in range(30)]
        self.frames.insert(pos, Frame(setup))

    def copyFrame(self):
        """
        Copies the current frame and add the copy directly after the current
        frame.
        Has no effect if the clip is empty.
        """

        if self.size != 0:
            frame = self.frames[self.curFrame].copy()
            self.frames.insert(self.curFrame+1, frame)

    def removeFrame(self, frameId):
        """
        Removes the desired frame.

        @param frameId the id of the frame, that should be removed
        """

        if frameId < 0 or frameId >= self.size:
            raise self.__class__.FrameIdOutOfBoundException

        if frameId <= self.curFrame:
            self.curFrame -= 1

        # Correct active frame if clip is not empty
        if self.curFrame == -1 and self.size != 0:
            self.curFrame = 0

        del self.frames[frameId]

    def setStar(self, starId, state):
        """
        sets the state of the star with starId in the current frame

        @param starId id of the star
        @param state True for star is on and False for star is off
        @raise StarOutOfBoundException starId doesn't exist
        """
        self.frames[self.curFrame].setStar(starId, state)

    def toggleStar(self, starId):
        """
        toggles  a star

        @param starId id of the star
        @raise StarOutOfBoundException starId doesn't exist
        """
        state = self.frames[self.curFrame].getStarState(starId)
        self.setStar(starId, not state)

    # === Export/Import ===
    def save(self, filePath=None):
        """
        saves the clip into a json file

        @param filePath optional new filePath; if none is given, the
        current filePath is used
        """

        # Check file path
        if filePath is None and self.filePath is None:
            raise self.__class__.NoFilePathException()

        if filePath is not None:
            self.filePath = filePath

        # Generate data dump for serialization
        frameDump = []
        for frame in self.frames:
            starDump = []
            for star in frame.stars:
                starDump.append(star.isOn)

            frameDump.append(starDump)

        # Dump data into file
        fp = open(self.filePath, 'w')
        json.dump({'currentFrame': self.curFrame, 'frames': frameDump}, fp)
        fp.close()

    def load(self, filePath):
        """
        loads clip from file

        @param filePath path to file
        """
        self.filePath = filePath

        # Load json
        fp = open(self.filePath, 'r')
        dump = json.load(fp)
        fp.close()

        # Put into Clip object
        self.curFrame = dump['currentFrame']

        for frameSetup in dump['frames']:
            self.frames.append(Frame(frameSetup))

    def export(self):
        """
        exports the clip to a compressed animation for running on the arduino

        @return a list of compressed frames as bytes of the length 5
        """

        # List of bytes, which represents the frames
        exportedFrames = []
        # Setup of the previous frame
        curFrameSetup = -1
        # Duration of the current frame
        curFrameDuration = 1

        for frame in self.frames:
            setup = frame.export()
            if curFrameSetup == setup:
                curFrameDuration += 1
            else:
                packedFrame = setup + (curFrameDuration << 30)
                # Convert to bytes
                byteArr = array('B')  # Create array with unsigned chars
                for i in range(5):
                    byteArr.append((packedFrame >> (i * 8)) & 0b11111111)
                exportedFrames.append(bytes(byteArr))
                curFrameDuration = 1

        return exportedFrames


class Frame:
    """
    Represents a frame (single image) within a clip (animation).
    """

    class StarOutOfBoundException(Exception):
        """
        Exception for stars that doesn't exist.
        """

        def __init__(self, starId):
            """
            constructor

            @param starId id you tried to access
            """
            super().__init__(self, 'Star {0:d} is out of bound'.format(starId))

    def __init__(self, setup=[]):
        """
        constructor

        @param setup list of stars which are on or off (setup[1] = true means
        star with Id 1 is on)
        """

        self.stars = [Star(state) for state in setup]

    def getStarState(self, starId):
        """
        Returns the state of the desired star.

        @param starId id of the star
        @return True if star is on and False if star is off
        @raise StarOutOfBoundException starId doesn't exist
        """

        if starId < 0 or starId >= len(self.stars):
            raise self.__class__.StarOutOfBoundException()

        return self.stars[starId].isOn

    def export(self):
        """
        Exports the star setup of the frame as integer (1 at position x means,
        that star x is on).

        @return the setup as integer
        """

        i = 0
        setup = 0
        # Generate number
        for star in self.stars:
            if (star.isOn):
                setup += 1 << (len(self.stars) - 1 - i)
            i += 1

        return setup

    def copy(self):
        """
        Returns a hard copy of this frame.
        """
        setup = [star.isOn for star in self.stars]
        return Frame(setup)


class Star:
    """
    Represents a star.
    """

    def __init__(self, isOn=False):
        """
        constructor
        """
        self.isOn = isOn
