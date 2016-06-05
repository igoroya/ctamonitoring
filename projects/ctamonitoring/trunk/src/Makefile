#*******************************************************************************

# ALMA - Atacama Large Millimiter Array
#
# "@(#) $Id: Makefile,v 1.20 2009/03/11 17:08:51 hsommer Exp $" 
#
# Makefile of ........
#
#

#
# MODULE CODE DESCRIPTION:
# ------------------------
# As a general rule:  public file are "cleaned" and "installed"  
#                     local (_L) are not "installed".

#
# Flag to switch on debugging information
# ----------------------------
#
DEBUG=on

#
# Error definition files for exceptions
# and completions
# ----------------------------
#
#TODO: Create my own errors, for now I use those from the acs Course example
#ACSERRDEF = ACSErrTypeACSCourse

#
# Java sources
# ----------------------------
#


#
# Configuration database schema Files
# ------------------------------------
CDB_SCHEMAS = PropertyRecorder
#
# IDL FILES
#----------------------------
IDL_FILES =  PropertyRecorder
USER_IDL = 

#
# Python sources
#----------------------------
#PY_SCRIPTS = mountSimple mountCallback acscourseMountSupplier acscourseMountConsumer

PY_PACKAGES = ctamonitoring

#
#>>>>> END OF standard rules

#
# CHOSE PLATFORM
# --------------
# Default is UNIX, for VxVorks application next line MUST BE UNCOMMENTED
#MAKE_VXWORKS = on   

#
# INCLUDE STANDARDS
# -----------------

#
# list of all possible C-sources (used to create automatic dependencies)
# ------------------------------
CSOURCENAMES = \
	$(foreach exe, $(EXECUTABLES) $(EXECUTABLES_L), $($(exe)_OBJECTS)) \
	$(foreach lib, $(LIBRARIES) $(LIBRARIES_L), $($(lib)_OBJECTS))


MAKEDIRTMP := $(shell searchFile include/acsMakefile)
ifneq ($(MAKEDIRTMP),\#error\#)
   MAKEDIR := $(MAKEDIRTMP)/include
   include $(MAKEDIR)/acsMakefile
endif


#
# TARGETS
# -------
all:	do_all
	@echo " . . . 'all' done" 

clean : clean_all 
	$(RM) *~ ../include/*~ ../idl/*~ ../*~ ../../*~ ../doc/html/* core
	$(RM) tmp.txt 
	@echo " . . . clean done"

clean_dist : clean clean_dist_all 
	@echo " . . . clean_dist done"

man   : do_man 
	@echo " . . . man page(s) done"

install : install_all
	@echo " . . . installation done"

#___oOo___
