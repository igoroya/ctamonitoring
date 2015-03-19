__version__ = "$Id: models.py 532 2013-08-08 23:28:32Z tschmidt $"


'''
moduledocs

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: models.py 532 2013-08-08 23:28:32Z tschmidt $
@change: $LastChangedDate: 2013-08-09 01:28:32 +0200 (Fri, 09 Aug 2013) $
@change: $LastChangedBy: tschmidt $
@requires: sqlalchemy
@requires: json
'''


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Boolean, Enum, Float, Integer, String, Text, TypeDecorator
from sqlalchemy.dialects.mysql import BIGINT as BigInteger
import json


Base = declarative_base()


class JSON(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.
    Usage::
    JSON
    """

    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class ComponentType(Base):
    __tablename__ = 'component_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(252),
                  #index=True,
                  nullable=False)
    components = relationship("Component", backref=backref('type'))

    def __repr__(self):
        return "<ComponentType('%s')>" % (self.name,)


class Component(Base):
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True)
    component_type_id = Column(Integer, ForeignKey("component_types.id"),
                               #index=True,
                               nullable=False)
    name = Column(String(252),
                  #index=True,
                  nullable=False)
    properties = relationship("Property", backref=backref('component'))

    def __repr__(self):
        return "<Component('%s')>" % (self.name,)


class PropertyType(Base):
    __tablename__ = 'property_types'

    id = Column(Integer, primary_key=True)
    type = Column(Enum('FLOAT', 'DOUBLE', 'LONG', 'LONG_LONG', 'STRING', 'BIT_FIELD', 'ENUMERATION', 'FLOAT_SEQ', 'DOUBLE_SEQ', 'LONG_SEQ', 'LONG_LONG_SEQ', 'STRING_SEQ', 'OBJECT'),
                  nullable=False)
    type_description = Column(JSON(65532))
    properties = relationship('Property', backref=backref('type'))

    def __repr__(self):
        return "<PropertyType('%s')>" % (self.type,)


class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    component_id = Column(ForeignKey('components.id'),
                          #index=True,
                          nullable=False)
    property_type_id = Column(ForeignKey('property_types.id'),
                              #index=True,
                              nullable=False)
    name = Column(String(252),
                  #index=True,
                  nullable=False)
    description = Column(String(65532))
    #format = Column(String(252))
    #units = Column(String(252))
    #resolution = Column(BigInteger(unsigned=True))
    #graph_min = Column(Float(precision=53))
    #graph_max = Column(Float(precision=53))
    #min_step = Column(Float(precision=53))
    records = relationship('RecordEntry', backref=backref('property'))
    # floatToPropertyRef = relationship('FloatPropertyValue', backref=backref('property'))
    # intToPropertyRef = relationship('IntegerPropertyValue', backref=backref('property'))
    # textToPropertyRef = relationship('TextPropertyValue', backref=backref('property'))
    # bitToPropertyRef = relationship('BitFieldPropertyValue', backref=backref('property'))
    # enumToPropertyRef = relationship('EnumPropertyValue', backref=backref('property'))
    # structuredToPropertyRef = relationship('AnyPropertyValue', backref=backref('property'))

    def __repr__(self):
        return "<Property('%s')>" % (self.name,)


class FloatPropertyValue(Base):
    __tablename__ = 'float_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(Float(precision=53), nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class IntegerPropertyValue(Base):
    __tablename__ = 'integer_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(BigInteger, nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class TextPropertyValue(Base):
    __tablename__ = 'text_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(Text(65532), nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class BitFieldPropertyValue(Base):
    __tablename__ = 'bit_field_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(BigInteger(unsigned=True), nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class EnumPropertyValue(Base):
    __tablename__ = 'enum_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class AnyPropertyValue(Base):
    __tablename__ = 'any_values'

    id = Column(BigInteger(unsigned=True), primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    tm = Column(BigInteger(unsigned=True),
                #index=True,
                nullable=False)
    value = Column(JSON(65532), nullable=False)

    def __repr__(self):
        return "<Value('%s')='%s'>" % (self.tm, self.value)


class RecordEntry(Base):
    __tablename__ = 'record_entries'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'),
                         #index=True,
                         nullable=False)
    start_tm = Column(BigInteger(unsigned=True),
                      #index=True,
                      nullable=False)
    stop_tm = Column(BigInteger(unsigned=True))
    enabled = Column(Boolean, nullable=False)

    def __repr__(self):
        return "<LogEntry('%s','%s','%s')" % (self.start_tm, self.stop_tm, self.enabled)


if __name__ == '__main__':
    print 'Hello World'
