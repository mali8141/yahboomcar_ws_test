# generated from rosidl_generator_py/resource/_idl.py.em
# with input from arm_msgs:msg/ArmJoints.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_ArmJoints(type):
    """Metaclass of message 'ArmJoints'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('arm_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'arm_msgs.msg.ArmJoints')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__arm_joints
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__arm_joints
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__arm_joints
            cls._TYPE_SUPPORT = module.type_support_msg__msg__arm_joints
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__arm_joints

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class ArmJoints(metaclass=Metaclass_ArmJoints):
    """Message class 'ArmJoints'."""

    __slots__ = [
        '_joint1',
        '_joint2',
        '_joint3',
        '_joint4',
        '_joint5',
        '_joint6',
        '_time',
    ]

    _fields_and_field_types = {
        'joint1': 'int16',
        'joint2': 'int16',
        'joint3': 'int16',
        'joint4': 'int16',
        'joint5': 'int16',
        'joint6': 'int16',
        'time': 'int16',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
        rosidl_parser.definition.BasicType('int16'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.joint1 = kwargs.get('joint1', int())
        self.joint2 = kwargs.get('joint2', int())
        self.joint3 = kwargs.get('joint3', int())
        self.joint4 = kwargs.get('joint4', int())
        self.joint5 = kwargs.get('joint5', int())
        self.joint6 = kwargs.get('joint6', int())
        self.time = kwargs.get('time', int())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.joint1 != other.joint1:
            return False
        if self.joint2 != other.joint2:
            return False
        if self.joint3 != other.joint3:
            return False
        if self.joint4 != other.joint4:
            return False
        if self.joint5 != other.joint5:
            return False
        if self.joint6 != other.joint6:
            return False
        if self.time != other.time:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def joint1(self):
        """Message field 'joint1'."""
        return self._joint1

    @joint1.setter
    def joint1(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint1' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint1' field must be an integer in [-32768, 32767]"
        self._joint1 = value

    @builtins.property
    def joint2(self):
        """Message field 'joint2'."""
        return self._joint2

    @joint2.setter
    def joint2(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint2' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint2' field must be an integer in [-32768, 32767]"
        self._joint2 = value

    @builtins.property
    def joint3(self):
        """Message field 'joint3'."""
        return self._joint3

    @joint3.setter
    def joint3(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint3' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint3' field must be an integer in [-32768, 32767]"
        self._joint3 = value

    @builtins.property
    def joint4(self):
        """Message field 'joint4'."""
        return self._joint4

    @joint4.setter
    def joint4(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint4' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint4' field must be an integer in [-32768, 32767]"
        self._joint4 = value

    @builtins.property
    def joint5(self):
        """Message field 'joint5'."""
        return self._joint5

    @joint5.setter
    def joint5(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint5' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint5' field must be an integer in [-32768, 32767]"
        self._joint5 = value

    @builtins.property
    def joint6(self):
        """Message field 'joint6'."""
        return self._joint6

    @joint6.setter
    def joint6(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'joint6' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'joint6' field must be an integer in [-32768, 32767]"
        self._joint6 = value

    @builtins.property
    def time(self):
        """Message field 'time'."""
        return self._time

    @time.setter
    def time(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'time' field must be of type 'int'"
            assert value >= -32768 and value < 32768, \
                "The 'time' field must be an integer in [-32768, 32767]"
        self._time = value
