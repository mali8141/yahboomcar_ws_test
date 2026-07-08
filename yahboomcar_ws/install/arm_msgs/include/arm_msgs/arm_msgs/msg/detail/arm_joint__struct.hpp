// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from arm_msgs:msg/ArmJoint.idl
// generated code does not contain a copyright notice

#ifndef ARM_MSGS__MSG__DETAIL__ARM_JOINT__STRUCT_HPP_
#define ARM_MSGS__MSG__DETAIL__ARM_JOINT__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__arm_msgs__msg__ArmJoint __attribute__((deprecated))
#else
# define DEPRECATED__arm_msgs__msg__ArmJoint __declspec(deprecated)
#endif

namespace arm_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ArmJoint_
{
  using Type = ArmJoint_<ContainerAllocator>;

  explicit ArmJoint_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->id = 0;
      this->joint = 0;
      this->time = 0;
    }
  }

  explicit ArmJoint_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->id = 0;
      this->joint = 0;
      this->time = 0;
    }
  }

  // field types and members
  using _id_type =
    uint8_t;
  _id_type id;
  using _joint_type =
    int16_t;
  _joint_type joint;
  using _time_type =
    int16_t;
  _time_type time;

  // setters for named parameter idiom
  Type & set__id(
    const uint8_t & _arg)
  {
    this->id = _arg;
    return *this;
  }
  Type & set__joint(
    const int16_t & _arg)
  {
    this->joint = _arg;
    return *this;
  }
  Type & set__time(
    const int16_t & _arg)
  {
    this->time = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    arm_msgs::msg::ArmJoint_<ContainerAllocator> *;
  using ConstRawPtr =
    const arm_msgs::msg::ArmJoint_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      arm_msgs::msg::ArmJoint_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      arm_msgs::msg::ArmJoint_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__arm_msgs__msg__ArmJoint
    std::shared_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__arm_msgs__msg__ArmJoint
    std::shared_ptr<arm_msgs::msg::ArmJoint_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ArmJoint_ & other) const
  {
    if (this->id != other.id) {
      return false;
    }
    if (this->joint != other.joint) {
      return false;
    }
    if (this->time != other.time) {
      return false;
    }
    return true;
  }
  bool operator!=(const ArmJoint_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ArmJoint_

// alias to use template instance with default allocator
using ArmJoint =
  arm_msgs::msg::ArmJoint_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace arm_msgs

#endif  // ARM_MSGS__MSG__DETAIL__ARM_JOINT__STRUCT_HPP_
