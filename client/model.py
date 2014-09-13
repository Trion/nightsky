"""
models to represent the clip
"""

import json
from array import array

class Clip:
    """
    Represents a clip
    """

    class FrameIdOutOfBoundException(Exception):
        """
        Exception for frame ids, which are out of bound
        """

        def __init__(self, frameId):
            """
            constructor

            @param frameId id you tried to access
            """

            super().__init__(self, 'Frame {0:d} is out of bound'.format(frameId))

    class NoFilePathException(Exception):
        """
        Exception for missing file path
        """

        def __init__(self):
            """
            constructor
            """

            super().__init__(self, 'Missing file path')

    def __init__(self, filePath=None):
        """
        constructor

        @param filePath name of file, where a clip could be saved
        """

        self.filePath = filePath
        self.curFrame = 0
        self.frames = []
        if filePath != None:
            self.load(filePath)

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

    def save(self, filePath=None):
        """
        saves the clip into a json file

        @param filePath optional new filePath; if none is given, the current filePath is used
        """

        # Check file path
        if filePath == None and self.filePath == None:
            raise self.__class__.StarOutOfBoundException()

        if filePath != None:
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
                byteArr = array('B') # Create array with unsigned chars
                for i in range(5):
                    byteArr.append((packedFrame >> (i * 8)) & 0b11111111)
                exportedFrames.append(bytes(byteArr))
                curFrameDuration = 1

        return exportedFrames


class Frame:
    """
    Represents a frame (single image) within a clip (animation)
    """

    class StarOutOfBoundException(Exception):
        """
        Exception for stars that doesn't exist
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

        @param setup list of stars which are on or off (setup[1] = true means star with Id 1 is on)
        """

        self.stars = []
        for state in setup:
            self.stars.append(Star(state))

    def getStarState(self, starId):
        """
        returns the state of the desired star

        @param starId id of the star
        @return True if star is on and False if star is off
        @raise StarOutOfBoundException starId doesn't exist
        """

        if starId < 0 or starId >= len(self.stars):
            raise self.__class__.StarOutOfBoundException()

        return self.stars[starId].isOn

    def export(self):
        """
        exports the star setup of the frame as integer (1 at position x means, that star x is on)

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


class Star:
    """
    Represents a star
    """

    def __init__(self, isOn=False):
        """
        constructor
        """
        self.isOn = isOn
