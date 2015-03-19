from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ctamonitoring.backend.sqlal.models import * 

print 'hi man'

engine = create_engine('sqlite:///:memory:', echo=True)

engine.execute("select 1").scalar()

Session = sessionmaker (bind=engine)

session = Session()

Base = declarative_base()

comp = Component()


#Base.metadata.create_all(engine)

pType = PropertyType()
pType.type = 'DOUBLE'

prop = Property()

prop.name = 'doubleProp'
prop.property_type_id = pType.id
#relate the property with a given component 
prop.component_id = comp.id

comp.name = "AlfredoComp"

session.add(comp)
#session.add(prop)

print comp.name
print pType.type
print prop.name
print comp.properties
print prop.records


#for values of monitored data
myValue = FloatPropertyValue()
#relate with a given property
myValue.property_id = prop.id

#set values
myValue.tm = 11234
myValue.value = 2.34

print '-------------'
print myValue

#session.add(myValue)

#see what happens if I inser stuff
print myValue.id
print session.new
#session.commit()