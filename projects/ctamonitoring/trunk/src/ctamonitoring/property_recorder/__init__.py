""" This package contains the implementation of the PropertyRecorder interface
and the required auxiliary code.

The PropertyRecorder is a tool that allows to scan an ACS deployment,
identify the components, their properties and create monitors on these
properties. These monitors will transfer the monitored measurements to
a backend that will take care of storing the data.
I works with the three ACS implementation language components.

The property recorder can operate in two modes: stand-alone (see standalone.py)
or in a combination of distributer (see distributer.py) and several recorders,
instantiating dynamic recorder components (see recorder.py).


@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
