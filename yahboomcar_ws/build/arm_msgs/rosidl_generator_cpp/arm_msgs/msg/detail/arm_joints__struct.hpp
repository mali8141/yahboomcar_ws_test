// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from arm_msgs:msg/ArmJoints.idl
// generated code does not contain a copyright notice

#ifndef ARM_MSGS__MSG__DETAIL__ARM_JOINTS__STRUCT_HPP_
#define ARM_MSGS__MSG__DETAIL__ARM_JOINTS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__arm_msgs__msg__ArmJoints __attribute__((deprecated))
#else
# define DEPRECATED__arm_msgs__msg__ArmJoints __declspec(deprecated)
#endif

namespace arm_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ArmJoints_
{
  using Type = ArmJoints_<ContainerAllocator>;

  explicit ArmJoints_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->joint1 = 0;
      this->joint2 = 0;
      this->joint3 = 0;
      this->joint4 = 0;
      this->joint5 = 0;
      this->joint6 = 0;
      this->time = 0;
    }
  }

  explicit ArmJoints_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->joint1 = 0;
      this->joint2 = 0;
      this->joint3 = 0;
      this->joint4 = 0;
      this->joint5 = 0;
      this->joint6 = 0;
      this->time = 0;
    }
  }

  // field types and members
  using _joint1_type =
    int16_t;
  _joint1_type joint1;
  using _joint2_type =
    int16_t;
  _joint2_type joint2;
  using _joint3_type =
    int16_t;
  _joint3_type joint3;
  using _joint4_type =
    int16_t;
  _joint4_type joint4;
  using _joint5_type =
    int16_t;
  _joint5_type joint5;
  using _joint6_type =
    int16_t;
  _joint6_type joint6;
  using _time_type =
    int16_t;
  _time_type time;

  // setters for named parameter idiom
  Type & set__joint1(
    const int16_t & _arg)
  {
    this->joint1 = _arg;
    return *this;
  }
  Type & set__joint2(
    const int16_t & _arg)
  {
    this->joint2 = _arg;
    return *this;
  }
  Type & set__joint3(
    const int16_t & _arg)
  {
    this->joint3 = _arg;
    return *this;
  }
  Type & set__joint4(
    const int16_t & _arg)
  {
    this->joint4 = _arg;
    return *this;
  }
  Type & set__joint5(
    const int16_t & _arg)
  {
    this->joint5 = _arg;
    return *this;
  }
  Type & set__joint6(
    const int16_t & _arg)
  {
    this->joint6 = _arg;
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
    arm_msgs::msg::ArmJoints_<ContainerAllocator> *;
  using ConstRawPtr =
    const arm_msgs::msg::ArmJoints_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      arm_msgs::msg::ArmJoints_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      arm_msgs::msg::ArmJoints_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__arm_msgs__msg__ArmJoints
    std::shared_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__arm_msgs__msg__ArmJoints
    std::shared_ptr<arm_msgs::msg::ArmJoints_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ArmJoints_ & other) const
  {
    if (this->joint1 != other.joint1) {
      return false;
    }
    if (this->joint2 != other.joint2) {
      return false;
    }
    if (this->joint3 != other.joint3) {
      return false;
    }
    if (this->joint4 != other.joint4) {
      return false;
    }
    if (this->joint5 != other.joint5) {
      return false;
    }
    if (this->joint6 != other.joint6) {
      return false;
    }
    if (this->time != other.time) {
      return false;
    }
    return true;
  }
  bool operator!=(const ArmJoints_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ArmJoints_

// alias to use template instance with default allocator
using ArmJoints =
  arm_msgs::msg::ArmJoints_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace arm_msgs

#endif  // ARM_MSGS__MSG__DETAIL__ARM_JOINTS__STRUCT_HPP_
