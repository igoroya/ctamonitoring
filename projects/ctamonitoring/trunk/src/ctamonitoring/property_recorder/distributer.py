#--CORBA STUBS-----------------------------------------------------------------
import actl__POA
import actl
import ACS, ACS__POA
#--ACS Imports-----------------------------------------------------------------
from Acspy.Servants.CharacteristicComponent import CharacteristicComponent
from Acspy.Servants.ContainerServices  import ContainerServices
from Acspy.Servants.ComponentLifecycle import ComponentLifecycle
from CORBA import TRUE, FALSE
import ACSErrTypeCommonImpl
from Acspy.Nc.Consumer          import Consumer
#from Acspy.Common import TimeHelper
#--Other Imports-----------------------------------------------------------------
import collections
import threading
import time
import ast
#------------------------------------------------------------------------------
class PropertyRecorderDistributer(actl__POA.PropertyRecorderDistributer,
           CharacteristicComponent,
           ContainerServices,
           ComponentLifecycle):
    """
    Implementation of the PropertyRecorderDistributer interface 
    
    Designed for setups with many components, spans dynamic PropertyRecorder (see PropertyRecorder.py) components
    on demand when PropertyRecordes become full according to the maximum number of component or properties per recorder
    (other criteria might be possible) 

    It only requires that the corresponding containers are available when the dynamic PropertyRecorders are activated 

    Monitors and data storage is done in the different PropertyRecorders. Default rates and maximum component and properties 
    per PropertyRecorder is setup from here as well
    
    Bookeeping of components is performed, and feedback from lost(deac tivated or crashed) components is obtained via a 'pull'
    from each property recorder at a certain rate 
    
    @author: igoroya
    @organization: HU BErlin
    @copyright: cta-observatory.org
    @version: $Id$
    @change: $LastChangedDate$, $LastChangedBy$    
    """
        
    #------------------------------------------------------------------------------
    def __init__(self,isStandAlone=True):
        '''
        Superclass constructors are called here, and several variables are initialized
        
        TODO: migrate the constants to the CDB and read them from there
        '''
        CharacteristicComponent.__init__(self)
        ContainerServices.__init__(self)
        
        #Default values in case not CDB entry exists or it is faulty
        self.__defaultMonitorRate = 600000000 # units in in 100 of ns, OMG time
        self.__compsCheckingPeriod = 60 #do every 60 seconds
        self.__recordersCheckingPeriod = 60 #do every 60 seconds
        self.__maxCompsPerRecorder = 100 #TODO: Find values after testing
        self.__maxPropsPerRecorder = 2000 #TODO: Find values
        self.__recorderBaseName = 'propertyRecorderInst'
        self.__containerBaseName= 'recorderContainerInst'
        
        self.__recorderNum = 0#Number (identifier) of the actual recorder component and container
        self.__recorderActiveInst = None# actual recorder instance
        
        return
    #------------------------------------------------------------------------------  
    def initialize(self):
        """
        Lifecycle method
        """
        
        self.getLogger().logInfo("called...")

                
        
            #Get access to the CDB
        try: 
            cdb = CDBAccess.cdb()
            componentCDBXML = cdb.get_DAO('alma/%s' % (self.getName()))
            componentCDB = XmlObjectifier.XmlObject(componentCDBXML)
        except Exception:
            self.getLogger().logInfo("No CDB information found, using the default values in code implementation: ")
       
        
        try: 
            val = componentCDB.firstChild.getAttribute("default_monitor_rate").decode()
            self.__defaultMonitorRate = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for default_monitor_rate could be retrieved")

        try: 
            val = componentCDB.firstChild.getAttribute("max_comps_per_recorder").decode()
            self.__maxCompsPerRecorder = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for max_comps_per_recorder could be retrieved")

        try: 
            val = componentCDB.firstChild.getAttribute("max_props_per_recorder").decode()
            self.__maxPropsPerRecorder = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for max_props_per_recorder could be retrieved")


        try: 
            val = componentCDB.firstChild.getAttribute("checking_period_distributer").decode()
            self.__recordersCheckingPeriod = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for checking_period_distributer could be retrieved")

        try: 
            val = componentCDB.firstChild.getAttribute("comps_checking_period").decode()
            self.__compsCheckingPeriod = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for checking_period_distributer could be retrieved")


        try: 
            val = componentCDB.firstChild.getAttribute("recorder_base_name").decode()
            self.__recorderBaseName = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for recorder_base_name could be retrieved")

        try: 
            val = componentCDB.firstChild.getAttribute("container_base_name").decode()
            self.__containerBaseName = val 
        except Exception:
            self.getLogger().logInfo("No CDB information for container_base_name could be retrieved")

        self.getLogger().logInfo("====================================================")
        self.getLogger().logInfo("Configuration parameters")
        self.getLogger().logInfo("defaultMonitorRate =" + str(self.__defaultMonitorRate)) 
        self.getLogger().logInfo("maxCompsPerRecorder =" + str(self.__maxCompsPerRecorder))
        self.getLogger().logInfo("maxPropsPerRecorde =" + str(self.__maxPropsPerRecorder)) 
        self.getLogger().logInfo("recordersCheckingPeriod =" + str(self.__recordersCheckingPeriod)) 
        self.getLogger().logInfo("compsCheckingPeriod =" + str(self.__compsCheckingPeriod)) 
        self.getLogger().logInfo("recorderBaseName =" + str(self.__recorderBaseName)) 
        self.getLogger().logInfo("containerBaseName =" + str(self.__containerBaseName)) 
        self.getLogger().logInfo("====================================================")
        
        #get threading lock to make some methods synchronized
        self.__lock = threading.RLock();
        
        #dictionary to store the components with acquired references
        self.__componentsMap = {}
        
        #dictionary to store the components with acquired references
        self.__recordersMap = {}
        
        #is the component recording the properties?
        self.__isRecording = False
               
# The NC is not used any more so next lines will be removed in future versions
#        #Create a Consumer for the NC
#        self.getLogger().logInfo('Creating a NC consumer')
#        self.__NCconsumer = Consumer(actl.CHANNELNAME_PROPERTYRECORDER)
#
#        #Subscribe to temperatureDataBlockEvent events (see PropertyRecorder.idl) and register
#        #this handler to process those events
#        self.__NCconsumer.addSubscription(actl.PropertyRecorderEvent, self.__recorderEventDataHandler)
#
#        #Let the Notification Service know we are ready to start processing events.
#        self.__NCconsumer.consumerReady()

        
        #Initialize the first recorder
        recorderName = self.__recorderBaseName +str(self.__recorderNum)
        containerName = self.__containerBaseName +str(self.__recorderNum)
        
        self.getLogger().logInfo("starting dynamic component: "+recorderName+"  at the container: "+containerName)
        recorder = self.getDynamicComponent(recorderName, "IDL:cta/actl/PropertyRecorder:1.0", "PropertyRecorderImpl.PropertyRecorder", containerName)
        
        try: 
            recorder.setMonitorDefaultRate( self.__defaultMonitoRate) 
        except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
            self.getLogger().warning("could not set the default monitor rate for PropertyRecorder" + recorderName)
       
        try: 
            recorder.setMaxComponents(self.__maxCompsPerRecorder)
        except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
            self.getLogger().warning("could not set the MaxComponents for PropertyRecorder" + recorderName)
        
        try: 
            recorder.setMaxProperties(self.__maxPropsPerRecorder)
        except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
            self.getLogger().warning("could not set the MaxProperties for PropertyRecorder" + recorderName)
 
        self.__recorderActiveInst = recorder
       
        #bookkeep the recorder 
        recorderInfo = collections.namedtuple('recorderInfo', ['recorderReference','components'], verbose=False) #components is a list of components on that recorder 
        recorderInfo.recorderReference=recorder
        self.__recordersMap[recorderName] = recorderInfo
        
        #starts a thread to check the state of the different the orders (as we do not have ComponentListeners in Python)
        #threading.Timer(1, self. __recordersCheckingTask).start()
        
        return
    #------------------------------------------------------------------------------
    def cleanUp(self):
        """
        Lifecycle method
        """
        self.getLogger().logInfo("called...")

      #  self.__NCconsumer.disconnect()
        
        self.stopRecording()
        
        self.__releaseAllCompReferences()     
       
        return
    #------------------------------------------------------------------------------
    def startRecording(self):
    #def message(self, string msg):
        """
        CORBA Method, starts looking for properties and issues so the 
        PropertyRecorders to create monitors and store data
        """
        if(self.__isRecording):
            self.getLogger().logInfo("Already recording ")
            return
        
        self.__isRecording = True

         #starts a thread to check the state of the different the orders (as we do not have ComponentListeners in Python)
        threading.Timer(1, self. __recordersCheckingTask).start()

        for recorderName, recorderInfo in self.__recordersMap.items() :
            self.getLogger().logInfo("Start recording in: "+recorderName)
            recorderInfo.recorderReference.startRecording()

        #start thread in 1 sec.
        threading.Timer(1, self.__scanForCompsTask).start()

        self.getLogger().logInfo("Starting recording: ")
        return
    #------------------------------------------------------------------------------
    def stopRecording(self):
        """
        CORBA Method. Stops looking for new components and issues the order 
        to the PropertyRecorders to stop recording
        """
        self.getLogger().logInfo("Stopping recording")

        self.__isRecording = False
                
  
        length = len(self.__recordersMap)
        self.getLogger().logInfo("Will stop recording in: "+str(length)+" recorder(s)")#TODO: Remove
  
        
        #loop in recorders and stop recording
        for recorderName, recorderInfo in self.__recordersMap.items() :
            self.getLogger().logInfo("Stopping recording in: "+recorderName)
            recorderInfo.recorderReference.stopRecording()
  
        #Alternative strategy is not removing them but stopping monitors in propertyRecorders
        self.__releaseAllCompReferences()
        
        return
    #------------------------------------------------------------------------------
    def flush(self):
        """
        CORBA method impl., individual PropertyRecorders will report data to storage and empty buffers
        """
        #TODO: This should not be a limitation
#        if self.__isRecording:
#            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
#            ex.addData("ErrorDesc", "The component is recording, data cannot be reported")
#            raise ex
        
        for recorderName, recorderInfo in self.__recordersMap.items() :
            self.getLogger().logInfo("Reporting data stored in "+recorderName)
            recorderInfo.recorderReference.flush()
    #------------------------------------------------------------------------------
    def isRecording(self):
        '''
        CORBA Method
        
        Returns True if recording, False otherwise
        '''
        self.getLogger().logInfo("isRecording() called")
  
        self.__isRecording
        #return 1#this can be done better, for sure
        if(self.__isRecording):
            return TRUE
        else:
            return FALSE
    #------------------------------------------------------------------------------
    def setMonitorDefaultRate(self,rate):
        """
        CORBA method implementation to set the default monitor rate for the new properties to be created in each 
        individual property recorder.
        
        The default rate will be only applied for those properties without a value in 'default_timer_trig' char. 
        Only can be called if it is not recording, in order to avoid having a mixture of properties with different 
        default monitor rates. 
        
        Keyword arguments:
        rate     -- integer in seconds
        """
        if self.__isRecording:
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData("ErrorDesc", "The component is recording and teh default value cannot be changed")
            raise ex
        
        self.__defaultMonitorRate = rate*10000000 #convert to OMG time, that is 100 ns
        #set that in childs
    #------------------------------------------------------------------------------
    def getMonitorDefaultRate(self):
        """
        CORBA method implementation to get the value of the default monitor rate for the new properties to be created
        
        Returns: rate in seconds
        """
        
        return self.__defaultMonitorRate/10000000 #convert to OMG time, that is 100 ns
    #------------------------------------------------------------------------------
    def setMaxComponentsPerRecorder(self,maxComp):
        """
        CORBA method implementation to set the maximum number of components for each new PropertyRecorder.
        
        Keyword arguments:
        maxComp    --  Maximum number of components accepted in each PropertyRecorder 
        """ 
        self.__maxCompsPerRecorder = maxComp
    #------------------------------------------------------------------------------
    
    def setMaxPropertiesPerRecorder(self,maxProp):
        """
        CORBA method implementation to set the maximum number of properties for each new PropertyRecorder.
        
        Keyword arguments:
        maxComp    --  Maximum number of properties accepted in each PropertyRecorder 
        """ 
        self.__maxPropsPerRecorder = maxProp
    #------------------------------------------------------------------------------
    def __scanForComps(self):
        """
        Private method to scan the system, locate containers, 
        their components. It will distribute components to the corresponding PropertyRecorders  
        """
        #make it a sync method
        self.__lock.acquire()        

        componenList = []

        
        self.getLogger().logInfo("__scanForComps() called")
        
        activatedComponents = self.availableComponents("*","*",True)
        
        nAvComps = len(activatedComponents)
        self.getLogger().logInfo('found '+str(nAvComps)+' components')
        
        #Check the availableComponent, only those which are already activated
        countComp = 0
        while (countComp <  nAvComps):
            componentId = self.findComponents("*","*",True)[countComp]
            self.getLogger().logInfo('Dealing with component:' + str(componentId))
            
            #self.getLogger().logInfo('Self name:' + str(self.getName()))
        
            #check if the component is already stored, if it is the case, check that it is still available and if not, remove. 
            
            if self.__componentsMap.has_key(componentId):
                self.getLogger().logInfo("The component is already registered")
                #check if is still reachable
                compEntry = self.__componentsMap.get(componentId)
                self.getLogger().logInfo("The component "+ componentId +" is already registered")
                
                #States should not be checked here but by childls, who give feedback to Distributer if something happended
                
                countComp = countComp + 1 
                continue
            #Skipping the self component to avoid getting a self-reference
            if componentId == self.getName():
               self.getLogger().logInfo("Skipping myself")
               countComp = countComp + 1 
               continue
            
            #Should skip chile components as well
            if self.__recordersMap.has_key(componentId): 
               self.getLogger().logInfo("Skipping PropertyRecorders")
               countComp = countComp + 1 
               continue
                       
               
                
            recorderInfo = collections.namedtuple('recorderInfo', ['recorderReference','components'], verbose=False) #components is a list of components on that recorder 

            recorder = self.__recorderActiveInst
            recorderName = self.__recorderBaseName +str(self.__recorderNum)
            
            #Check if the writer is full, if so create a new one
            if self.__recorderActiveInst.isFull():
                self.__recorderNum = self.__recorderNum + 1
                self.getLogger().logInfo("Startin a new PropertyRecoder. Instance number: " +  elf.__recorderNum)
                
                recorderName = self.__recorderBaseName +str(self.__recorderNum)
                containerName = self.__containerBaseName +str(self.__recorderNum)
        
                recorder = self.getDynamicComponent(recorderName, "IDL:cta/actl/PropertyRecorder:1.0", "PropertyRecorderImpl.PropertyRecorder", containerName)
                
                #Book-keep the new recorder
                recorderInfo.recorderReference=recorder
                self.__recordersMap[recorderName] =  recorderInfo
                componenList = []
                self.__recorderActiveInst = recorder
            
                try: 
                    recorder.setMonitorDefaultRate( self.__defaultMonitorRate) 
                except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
                    self.getLogger().warning("could not set the default monitor rate for PropertyRecorder" + recorderName)
               
                try: 
                    recorder.setMaxComponents(self.__maxCompsPerRecorder)
                except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
                    self.getLogger().warning("could not set the MaxComponents for PropertyRecorder" + recorderName)
                
                try: 
                    recorder.setMaxProperties(self.__maxPropsPerRecorder)
                except ACSErrTypeCommonImpl.CouldntPerformActionExImpl, ex: #TODO: check that this is correct
                    self.getLogger().warning("could not set the MaxProperties for PropertyRecorder" + recorderName)
                
                recorder.startRecording()
            
            try:
              
                #TODO: uncomment the following
                self.getLogger().logInfo("Inserting component: "+str(componentId))
                self.__recorderActiveInst.addOneComponent(componentId)
                
               
            except Exception: 
                self.getLogger().logInfo("Could not insert to the component: "+str(componentId))

                #TODO: Maybe check that the child is alive?
                
                countComp = countComp + 1 
                continue
           
            componenList.append(componentId)
            recorderInfo.recorderReference=recorder    
            recorderInfo.components = componenList
            self.__recordersMap[recorderName] = recorderInfo
            

           
            #store the component data into the dict  comp name :: compoennt curl
            compInfo = collections.namedtuple('componentId', 'storedInRecorder', verbose=False)
            
            compInfo.componentId = componentId
            compInfo.storedInRecorder = recorderName
    
            #TODO: This seems redundant, think how to inprove (maybe a list?)
            self.__componentsMap[componentId] = compInfo
                
            countComp = countComp + 1
    

        self.__lock.release()
        
        self.getLogger().logInfo("__scanForComps() done")
    #------------------------------------------------------------------------------
    def __checkRecordersState(self):
        """
        Checks is we lost any of the recorder in the way, and remove them 
        from the bookkeeping so they could be added again if they come alive again
        """ 
        self.__lock.acquire()       
        
        length = len(self.__recordersMap)
        totalLostComponents = 0
        
        for recorderName, recorderInfo  in self.__recordersMap.items() :
            self.getLogger().logInfo('checking propertyRecorder instance: '+recorderName) 
        
            state = None
                
            try:
                state = recorderInfo.recorderReference._get_componentState()
            except Exception: 
                self.getLogger().logInfo('The reference of the property recorder component '+ compName +'  is not valid any more, removing it') 
                if recorderInfo.components != None: 
                    for componentId in recorderInfo.components:
                        self.__componentsMap.pop(componentId)
                self.__recordersMap.pop(recorderName)
              #  self.releaseComponent(compName)
                continue
                    
            if (str(state) != "COMPSTATE_OPERATIONAL"):
                self.getLogger().logInfo('The reference of the property recorder component '+ compName +'  is not valid any more, removing it') 
                if recorderInfo.components != None: 
                    for componentId in recorderInfo.components:
                        self.__componentsMap.pop(componentId)
                self.__recordersMap.pop(recorderName)
                continue

            #Now check if there are lost components in the recorders that are still alive 
            lostComponents = recorderInfo.recorderReference.getLostComponent()
        
            totalLostComponents = totalLostComponents + len(lostComponents)

            if len(lostComponents)>0:
               for comp in lostComponents:
                   try: 
                       recorderInfo.components.remove(comp)
                       self.getLogger().logInfo(comp+" removed from recorderInfo")
                   except Exception:
                       self.getLogger().logInfo("The component is not any more in the recorderInfo")
                   try: 
                        self.__componentsMap.pop(comp)
                   except Exception:
                       self.getLogger().logInfo("The component is not any more in the __componentsMap")
            
            
        #print number of removed comps
        length = length - len(self.__recordersMap)
            
        if length > 0:
            self.getLogger().logInfo(str(length)+" propertyRecorders(s) removed from the records")
        else:
            self.getLogger().logInfo("No propertyRecorders removed from the records")
        
        if totalLostComponents > 0:
            self.getLogger().logInfo(str(totalLostComponents)+" components(s) removed from the records")
        
        self.__lock.release()            
    #------------------------------------------------------------------------------
    def __releaseAllCompReferences(self):
        self.getLogger().logInfo("called...")
  
        self.__componentsMap.clear()
    #------------------------------------------------------------------------------    
    def __emptyBuffers(self): 
        """TODO: Needed?"""
        self.__componentsMap.clear()
        self.__recordersMap.clear()
        #Execute in child the corresponding methods
    #------------------------------------------------------------------------------        
    def __recordersCheckingTask(self):
        """Scheduled timer process for checking the recorders state. If not recording it dies"""
        if self.__isRecording != True:
            self.getLogger().logInfo("___recordersCheckingTask dies.") 
            return
        
        self.__checkRecordersState()
        #call myself after self.__checkingPeriod seconds to get a periodic behavior
        threading.Timer(self.__recordersCheckingPeriod , self.__recordersCheckingTask).start()
    #------------------------------------------------------------------------------
    def __scanForCompsTask(self):
        """
        Scheduled timer process for checking for new properties. If not recording it dies
        
        NOTE: In the actual implementation it is not singleton, should this be a problem if several times activated?
        I think that not because startRecording() can only be called while not recording and it is the place where the 
        timer is activated.
        """
        if self.__isRecording != True: #If I should not keep recording, let the thread die
            self.getLogger().logInfo("__scanForCompsTask dies.")
            return
        
        
        #First check if we lost any property
        self.__scanForComps()
        
        #now look for new properties (TODO: can be unified with previous point)
                
        
        #call myself after self.__checkingPeriod seconds to get a periodic behavior
        threading.Timer(self.__compsCheckingPeriod, self.__scanForCompsTask).start()

#As long as I cannot use the NC this is commentd
#    def __ncListenerTask(self):
#         self.getLogger().logInfo('Creating a NC consumer')
#         self.__NCconsumer = Consumer(actl.CHANNELNAME_PROPERTYRECORDER)
#
#         #Subscribe to temperatureDataBlockEvent events (see PropertyRecorder.idl) and register
#         #this handler to process those events
#         self.__NCconsumer.addSubscription(actl.PropertyRecorderEvent, self.__recorderEventDataHandler)
# 
#         #Let the Notification Service know we are ready to start processing events.
#         self.__NCconsumer.consumerReady()
#            
#
#    def __recorderEventDataHandler(self,event):
#        '''
#        This function serves only one purpose...it must do something with the extracted
#        data from the structured event.  That is, it must be capable of processing
#        filterable_data[0].any in the structured event.  We can be certain of the real
#        type of someParam because handlers are registered only for specific
#        types (i.e., the type_name field of a structured event).
#    
#        Parameters: someParam is the real CORBA type extracted from the CORBA Any at
#        filterable_data[0].  In this case, it will always be a actl.PropertyRecorderEvent.
#    
#        Returns: event handler functions return nothing.
#    
#        Raises: If any exception is thrown by this function, the Consumer class will
#        catch it and call processEvent(...) which will hopefully have been overriden.
#        '''
#        
#        self.getLogger().logInfo('propertyRecorder: ' +str(event.recorderId)+' reports that the component: '  +str(event.componentId) + 'is not active any more')
#        
#        return
#------------------------------------------------------------------------------


   



# ___oOo___
