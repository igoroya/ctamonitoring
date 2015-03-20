from ctamonitoring.property_recorder import recorder
from ctamonitoring.property_recorder.recorder import STORAGE_TYPE

import threading
from aetypes import Boolean
from __builtin__ import str


class standalone(recorder.recorder):

    """
    For using the standalone version of the PropertyRecorder.
    See recorder.py for details.

    @author: igoroya
    @organization: HU Berlin
    @copyright: cta-observatory.org
    @version: $Id$
    @change: $LastChangedDate$, $LastChangedBy$
    """
    #-------------------------------------------------------------------------

    def __init__(self):
        # TODO: the storage stuff should be removed
        recorder.recorder.__init__(self)
        self._checkThread = self._createComponentFindThread()
        self._checkThread.start()
        
        "List of ACS components to use as include, or exclude list"
        self.__predefinedComponents = []
        '''If include mode, only the components considered in the scanning. 
        If false, all the components deployed are considered except those in the list,
        which will be excluded'''
        

    #-------------------------------------------------------------------------
    def _scanForComps(self):
        """
        Scans the system, locate containers,
        their components and their properties.
        """

        self.getLogger().logInfo("called...")

        if (self._isFull):
            self.getLogger().logInfo("property recorder is full, returning")
            return

        # try:
        activatedComponents = self.availableComponents("*", "*", True)

        nAvComps = len(activatedComponents)
        self.getLogger().logInfo('found ' + str(nAvComps) + ' components')

        # Check the availableComponent, only those which are already activated
        countComp = 0
        while (countComp < nAvComps):
            componentId = self.findComponents("*", "*", True)[countComp]
            self.getLogger().logInfo(
                "inspecting component: " + str(componentId))
            self.getLogger().logInfo("self name: " + str(self.getName()))

            if not self.addComponent(componentId):
                countComp = countComp + 1  # continue with the loop then
                continue

        self.getLogger().logInfo("done...")
        

    def _createComponentFindThread(self):
        return standalone.ComponentFindThread(self)

    #-------------------------------------------------------------------------
    class ComponentFindThread(recorder.recorder.ComponentCheckThread):

        """
        Inner class defining a thread to the check components
        Overriding recorder.recorder.ComponentCheckThread to scan
        for new components as well.
        """

        def __init__(self, recorderInstance):
            recorder.recorder.ComponentCheckThread.__init__(
                self, recorderInstance)

        def _run(self):
            # First check if we lost any property
            self._recorderInstance._checkLostComponents()
            # now look for new properties
            self._recorderInstance._scanForComps()


