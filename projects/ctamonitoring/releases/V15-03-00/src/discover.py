#!/usr/bin/env python
# who       when      what
# --------  --------  ----------------------------------------------
# Igor Oya  2012-03-19  created
#

#----------------------------------------------------------------------------
'''
This is a Python script that locates all the components and on those
All the properties, and provides the required information by the archive
The idea is to use it to help the develop a storage/DB schema for the MST
Prototype and later maybe CTA
'''
#--ACS Imports-----------------------------------------------------------------
from Acspy.Clients.SimpleClient import PySimpleClient
from Acspy.Common import CDBAccess #these are necessare for python components reading
from Acspy.Util import XmlObjectifier#as before

#--Python Imports--------------------------------------------------------------
import time
import collections

'''    
Create the client
'''
myClient = PySimpleClient()

#----------------------------------------------------------------------------
'''    
Check the available components in the CDB (both active and not) 
'''
availableComponents = myClient.availableComponents()
nComps = len(availableComponents)
print 'we have '+str(nComps)+' components'
count = 0
print 'Listing components know by the manager and their state' 
while (count <  nComps):
   print availableComponents[count]
   count = count + 1

print ''
print 'Listing all the components, just the name' 
count = 0
while (count <  nComps):
   print myClient.findComponents()[count]
   count = count + 1
print ''


#----------------------------------------------------------------------------
'''    
Check the available components in the CDB (only those already been activated) 
'''
activatedComponents = myClient.availableComponents("*","*",True)
#For gettin all component just turn the True above to False
nAvComps = len(activatedComponents)
print 'Listing only activated components' 
count = 0
while (count <  nAvComps):
   print activatedComponents[count]
   count = count + 1

print ''
print 'Listing activated components, just the name' 
count = 0
while (count <  nAvComps):
   print myClient.findComponents("*","*",True)[count]
   count = count + 1
print ''

#define the map (dictionary to store the components)
componentsMap = {}


#----------------------------------------------------------------------------
'''
Here I will loop over all the active components and 
'''
countComp = 0
count = 0
while (countComp <  nAvComps):
   print ''
   print 'Inspecting component:'
   componentId =  myClient.findComponents("*","*",True)[countComp]

   try:
      myComp = myClient.getComponent(myClient.findComponents("*","*",True)[countComp])
   except Exception: 
      print 'Could not get a reference to the component: '+str(myClient.findComponents("*","*",False)[countComp])
      print ''
      countComp = countComp + 1 
      continue

   compInfo = collections.namedtuple('componentInfo', ['compReference','monitors'], verbose=False)
   compInfo.compReference = myComp

   monitorList = []
   monitorList.append("alaone")
   monitorList.append("alatwo")
   monitorList.append("alathree")
   monitorList.append("alafour")
            
   compInfo.monitors = monitorList
            
   componentsMap[componentId] = compInfo

    

#This is not helping, but I keep just in case
#methods = myComp.__methods__
#nMethods = len(methods)
#print 'Listing the available methods' 
#count = 0
#while (count <  nMethods):
#   print methods[count]
#   count = count + 1

#print ''
#This is not helping neither
#nProps = myComp.get_all_characteristics().get_number_of_properties()
#print 'Number of Props is: '+str(nProps)


   '''
   Those components without characteristics were thowing exceptions here, this jumps them
   But there is a possible problem with the Python implementation: the find_characteristic and
   similar functions are actually not implemented, they are void. Therefore, for those I created
   the if (nChars == 0): check
   '''
   try:
      chars =  myComp.find_characteristic("*")
   except Exception: 
      print 'This component does not have characteristics'
      countComp = countComp + 1 
      continue 

  
   nChars = len(chars)
   print 'Number of Chars = '+str(nChars)

   #For Python components
   if (nChars == 0):
      print 'Number of chars is 0. Warning: It could be a python component'
      
      print 'lolololo'
      print myComp._get_name()
      print 'lolololo'
      
      cdb = CDBAccess.cdb()
      componentCDBXML = cdb.get_DAO('alma/%s' % (componentId))
      componentCDB = XmlObjectifier.XmlObject(componentCDBXML)
      
      #print dir((componentCDB.getElementsByTagName("*")[1]))
      #nodeString = (componentCDB.getElementsByTagName("*")[1]).nodeName
      
      elementList = (componentCDB.getElementsByTagName("*"))
      
      for element in elementList:
          nodeString = element.nodeName
          print 'evaluating the node: ' +nodeString
          nodeMethod = myPropStr= 'myComp.'+'_get_'+nodeString+'()' 
      
          try:
              myPro = eval(nodeMethod)
          except Exception: 
              print 'Not a property'
      
    
          try:
              (myPro.get_sync()[0])
              print 'could set get_sync, is IS a property'
          except Exception: 
              print 'could not set get_sync, IS NOT is not a property'
          else: 
              propNode = str('alma/%s/%s' % (componentId,nodeString))
              propertyCDBXML = cdb.get_DAO(propNode)
              propertyCDB = XmlObjectifier.XmlObject(propertyCDBXML)
              #Gets the CDB entries
              print propertyCDB.firstChild.getAttribute('units')
              print propertyCDB.firstChild.getAttribute('default_timer_trig')
              print propertyCDB.firstChild.getAttribute('description')
              print propertyCDB.firstChild.getAttribute('default_value')
              print propertyCDB.firstChild.getAttribute('archive_min_int')
              print propertyCDB.firstChild.getAttribute('archive_max_int')

              


              
            #  print dir(propertyCDB)
      
      
       
      
      #check if I can make a get_sync
      
      
      
      #print dir(componentCDB)
      #controlhost = componentCDB.apexSignal.getAttribute('controlhost')
      
     
     #controlhost = componentCDB.apexSignal.getAttribute('controlhost')
      
      print "#"
      print "#"
      print "#"
      
      #print dir(myComp._get_myRWProp())
      #This does not work with python components
      #print myComp._get_myRWProp().get_characteristic_by_name("archive_mechanism").value()

   print ''
   print 'Listing the available characteristics and values' 
   count = 0
   while (count <  nChars):
      print ''
      print 'Characteristic number '+str(count)
      print 'Name of Char: '+str(chars[count])
      print 'contains: '+str(myComp.get_characteristic_by_name(str(chars[count])).value())
      print 'type: '+str(myComp.get_characteristic_by_name(str(chars[count])).typecode())
      print 'Checking the value of the characteritics'
      myCharList = myComp.get_characteristic_by_name(str(chars[count])).value().split(',')
      print 'The entry has '+str(len(myCharList))+' characteristics'
      if (len(myCharList) > 5):
         print 'Probably is a property, trying the information of the archive'
         myPropStr= 'myComp.'+'_get_'+chars[count]+'()'
         try:
            myPro = eval(myPropStr)
         except Exception: 
            print 'It was not possible to get the property, jumping to next one'
            count = count + 1
            continue 
         #There is a funny behavior with the patter properties in Java implementation: is crashes with get_sync! I try here without proceeding 
         try:
            (myPro.get_sync()[0])
         except Exception: 
            print 'It was not possible to call get_sync in the propery, this is typically happening with pattern properties OR when the property exists in the CDB but it is not implemented in the component'
            count = count + 1
            continue
            #Here I want to jump to the statment. Maybe I have to use a "for"? 
            #pass
   
   
#         print '********************'
#         print '********************'
#         print myPro._get_characteristic_component_name()
#         print myPro._get_name()
#         print '********************'
#         print '********************'
   
         
         #dictionary of ACS properties and promitives
         
#         proTypeDict = {}
#         proTypeDict.update("IDL:alma/ACS/ROboolean:1.0","boolean")
#         proTypeDict.update("IDL:alma/ACS/RWboolean:1.0","boolean")
#         proTypeDict.update("IDL:alma/ACS/RObooleanSeq:1.0","booleanSeq")
#         proTypeDict.update("IDL:alma/ACS/RWbooleanSeq:1.0","booleanSeq")
#         
#         proTypeDict.update("IDL:alma/ACS/ROdouble:1.0","double")
#         proTypeDict.update("IDL:alma/ACS/RWdouble:1.0","double")
#         proTypeDict.update("IDL:alma/ACS/ROdoubleSeq:1.0","doubleSeq")
#         proTypeDict.update("IDL:alma/ACS/RWdoubleSeq:1.0","doubleSeq")
#         
#         proTypeDict.update("IDL:alma/ACS/ROlong:1.0","long")
#         proTypeDict.update("IDL:alma/ACS/RWlong:1.0","long")
#         proTypeDict.update("IDL:alma/ACS/ROlongSeq:1.0","longSeq")
#         proTypeDict.update("IDL:alma/ACS/RWlongSeq:1.0","longSeq")
#         
#         proTypeDict.update("IDL:alma/ACS/ROuLong:1.0","longLong")
#         proTypeDict.update("IDL:alma/ACS/RWuLong:1.0","longLong")
#         proTypeDict.update("IDL:alma/ACS/ROuLongSeq:1.0","longLongSeq")
#         proTypeDict.update("IDL:alma/ACS/RWuLongSeq:1.0","longLongSeq")
#         
#         proTypeDict.update("IDL:alma/ACS/ROlongLong:1.0","longLong")
#         proTypeDict.update("IDL:alma/ACS/RWlongLong:1.0","longLong")
#         proTypeDict.update("IDL:alma/ACS/ROlongLongSeq:1.0","longLongSeq")
#         proTypeDict.update("IDL:alma/ACS/RWlongLongSeq:1.0","longLongSeq")
#         
#         
#         proTypeDict.update("IDL:alma/ACS/ROfloat:1.0","float")
#         proTypeDict.update("IDL:alma/ACS/RWfloat:1.0","float")
#         proTypeDict.update("IDL:alma/ACS/ROfloatSeq:1.0","floatSeq")
#         proTypeDict.update("IDL:alma/ACS/RWfloatSeq:1.0","floatSeq")
#         
#         
         
         propertyType = myPro._NP_RepositoryId
   
         print '-------------------------'
         print ' '
         print propertyType
         print ' '
         print '-------------------------'    
   
   
         if myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROdouble:1.0":
                print 'IS A RODOUBLE!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWdouble:1.0":
                print 'IS A RWDOUBLE!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROdoubleSeq:1.0":
                print 'IS A RODOUBLE_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWdoubleSeq:1.0":
                print 'IS A RWDOUBLES_EQ!'
         
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROfloat:1.0":
                print 'IS A ROFLOAT!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWfloat:1.0":
                print 'IS A RWFLOAT!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROfloatSeq:1.0":
                print 'IS A ROFLOAT_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWfloatSeq:1.0":
                print 'IS A RWFLOAT_SEQ!'
        
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROlong:1.0":
                print 'IS A ROLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWlong:1.0":
                print 'IS A RWLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROlongSeq:1.0":
                print 'IS A ROLONG_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWlongSeq:1.0":
                print 'IS A RWLONG_SEQ!'
             
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROuLong:1.0":
                print 'IS A ROULONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWuLong:1.0":
                print 'IS A RWULONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROuLongSeq:1.0":
                print 'IS A ROULONG_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWuLongSeq:1.0":
                print 'IS A RWULONG_SEQ!'
         
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROlongLong:1.0":
                print 'IS A ROLONGLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWlongLong:1.0":
                print 'IS A RWLONGLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROlogLongSeq:1.0":
                print 'IS A ROLONGLONG_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWlongLongSeq:1.0":
                print 'IS A RWLONGLONG_SEQ!'
         
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROuLongLong:1.0":
                print 'IS A ROULONGLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWuLongLong:1.0":
                print 'IS A RWULONGLONG!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROuLogLongSeq:1.0":
                print 'IS A ROULONGLONG_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWuLongLongSeq:1.0":
                print 'IS A RWULONGLONG_SEQ!'
         
         
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROboolean:1.0":
                print 'IS A ROBOOLEAN!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWboolean:1.0":
                print 'IS A RWBOOLEAN!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RObooleanSeq:1.0":
                print 'IS A ROBOOLEAN_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWbooleanSeq:1.0":
                print 'IS A RWBOOLEAN_EQ!'
         
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROpattern:1.0":
                print 'IS A ROPATTERN!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWpattern:1.0":
                print 'IS A RWPATTERN!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROpatternSeq:1.0":
                print 'IS A ROPATTERN_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWpatternSeq:1.0":
                print 'IS A RWPATTERN_EQ!'
             
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROstring:1.0":
                print 'IS A ROSTRING!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWstring:1.0":
                print 'IS A RWSTRING!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROstringSeq:1.0":
                print 'IS A ROSTRING_SEQ!'
         elif myPro._NP_RepositoryId ==  "IDL:alma/ACS/RWstringSeq:1.0":
                print 'IS A RWSTRING_EQ!'
         
         else:
                print 'It is something else probably an enum!'
             
#             
#         if isinstance(myPro.get_sync()[0],int): # I get boolean here as well as long prop
#           
#            
#            if str(myPro.get_sync()[0].__class__) == "<type 'bool'>":
#                print 'type of property: bool'
#            elif str(myPro.get_sync()[0].__class__) == "<type 'int'>":
#                print 'type of property: long'
#            else: 
#                print 'type of property: '+ str(myPro.get_sync()[0].__class__) + ' but identified as "int" primitive by Python'
#         
#         elif isinstance(myPro.get_sync()[0],float):#here I get also double
#            print 'type of property: float'
#
#       
#            print "$"
#            print "$"
#            print "$"
#            print 'type of property: '+ str(myPro.get_sync()[0].__class__) + ' but identified as "float" primitive by Python'
#            print "$"
#            print "$"
#            print "$"
#            print dir(myPro)
#            print "RESOLUTION: "+str(myPro._get_resolution())
#            print myPro._NP_RepositoryId
#            
#            if myPro._NP_RepositoryId ==  "IDL:alma/ACS/ROdouble:1.0":
#                print 'IS A DOUBLE!'
#            
#            #print myPro.__module__
#            #print myPro.__class__
##            print dir(myPro.get_sync()[0])
##            print str(myPro.get_sync()[0].__class__)
##            print "$"
##            print "$"
##            print "$"
#         elif isinstance(myPro.get_sync()[0],long): #long would be a longLong or a pattern or uLongLong or uLong, we need to distinguish nbetween them  
# 
#            try: 
#                myPro._get_bitDescription()
#                print 'it has bit description, then it is a pattern'
#            except Exception: 
#                print 'it does not have bit description, then it is a longLong, uLong or an uLongLong'
#                if str(myPro.get_sync()[0].__class__) == "<type 'long'>":
#                    print 'type of property: longLong' # I assume here that we do the same for longLong, uLong or an uLongLong properties
#                else:
#                    print 'type of property: '+ str(myPro.get_sync()[0].__class__) + ' but identified as "long" primitive by Python'
#            
#         elif isinstance(myPro.get_sync()[0],bool): #never used
#            print 'type of property: bool'
#         elif isinstance(myPro.get_sync()[0],str):
#            print 'type of property: string'
#         elif isinstance(myPro.get_sync()[0],object):
#            if isinstance(myPro.get_sync()[0],list):
#                if isinstance((myPro.get_sync()[0])[0],int): #I get also booleanSeq
#                   if str(myPro.get_sync()[0][0].__class__) == "<type 'bool'>":
#                       print 'type of property: boolSeq'
#                   elif str(myPro.get_sync()[0][0].__class__) == "<type 'int'>":
#                           print 'type of property: longSeq'
#                   else: 
#                       print 'type of property: '+ str(myPro.get_sync()[0].__class__) + ' but identified as "int" primitive by Python'
#                       print 'type of property: intSeq'
#                elif isinstance((myPro.get_sync()[0])[0],float):
#           
#           
#                    
#                    print 'type of property: floatSeq'#I get also doubleseq
#                elif isinstance((myPro.get_sync()[0])[0],long):#no patternSeq that I know
#                    print 'type of property: longSeq'
#                elif isinstance((myPro.get_sync()[0])[0],bool):#never used
#                    print 'type of property: boolSeq'
#                else:
#                    print 'type "other list type"'
#            else:    
#                print 'type "object instance" (enumeration)'
#           
#                
#            
#            #Get all the states of the enum/pattern
#            #The states come as a comma separate string, we need to do some hacking to get them as a list
#            #Then I insert them into a dict so it works as a "c-type" enum, and this can be used in the monitor to obtain the string representation of 
#            # the enum, as by in the implementation the integer rep is given 
##            enumValues    = myPro.get_characteristic_by_name("statesDescription").value().split(', ')
##            enumDict = {}
##            i = 0
##            for item in enumValues:
##                enumDict[i] = enumValues[i]
##                i=i+1
##            print 'the dict:'
##            print enumDict
#            
#         else:
#            print 'Something else'
            #print type(myPro.get_sync()[0])
         print 'archive_priority:  '+ str(myPro.get_characteristic_by_name("archive_priority").value())
         print 'archive_min_int:  '+ str(myPro.get_characteristic_by_name("archive_min_int").value())
         print 'archive_max_int:  '+ str(myPro.get_characteristic_by_name("archive_max_int").value())
         print 'archive_suppress:  '+ str(myPro.get_characteristic_by_name("archive_suppress").value())
         print 'archive_mechanism:   '+ str(myPro.get_characteristic_by_name("archive_mechanism").value())
         if (myPro.get_characteristic_by_name("archive_suppress").value() != False):
            print '-------------------------------'
            print '      ARCHIVING THE PROPERY'
            print 'Actual value: '+str(myPro.get_sync()[0])+  " ||  Timestamp "+str(myPro.get_sync()[1].timeStamp)+" ||  type of completion: "+str(myPro.get_sync()[1].type)
         #more completion stuff, maybe we need in the future this
         # myPro.get_sync()[1].code
         # myPro.get_sync()[1].previousError
      print ''
      count = count + 1
      print ''
   countComp = countComp + 1




    
#check the dict    
print "Lenth of the dictionary:  " + str(len(componentsMap))           

#loop on the dict
for compName, compInfo  in componentsMap.items() :
    print 'deactivating component: '+compName 
    print dir(compInfo.compReference)
    print compInfo.compReference._get_componentState()

#            #destroy all the monitors
#            for monitor in compInfo.monitors:
#                monitor.destroy()
#          
#            #release the reference to the component
#            self.releaseComponent(compName)

#print dir(myPro)
print 'releasing components'
myClient.releaseComponent("*")
print "sleeping 3 secs to let things get stable"
time.sleep(3)
print 'Ending the discovery of properties'

# Script ends
# ___O:>___


