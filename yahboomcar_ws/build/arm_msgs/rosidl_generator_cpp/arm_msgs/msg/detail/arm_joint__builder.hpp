// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from arm_msgs:msg/ArmJoint.idl
// generated code does not contain a copyright notice

#ifndef ARM_MSGS__MSG__DETAIL__ARM_JOINT__BUILDER_HPP_
#define ARM_MSGS__MSG__DETAIL__ARM_JOINT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "arm_msgs/msg/detail/arm_joint__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace arm_msgs
{

namespace msg
{

namespace builder
{

class Init_ArmJoint_time
{
public:
  explicit Init_ArmJoint_time(::arm_msgs::msg::ArmJoint & msg)
  : msg_(msg)
  {}
  ::arm_msgs::msg::ArmJoint time(::arm_msgs::msg::ArmJoint::_time_type arg)
  {
    msg_.time = std::move(arg);
    return std::move(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoint msg_;
};

class Init_ArmJoint_joint
{
public:
  explicit Init_ArmJoint_joint(::arm_msgs::msg::ArmJoint & msg)
  : msg_(msg)
  {}
  Init_ArmJoint_time joint(::arm_msgs::msg::ArmJoint::_joint_type arg)
  {
    msg_.joint = std::move(arg);
    return Init_ArmJoint_time(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoint msg_;
};

class Init_ArmJoint_id
{
public:
  Init_ArmJoint_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmJoint_joint id(::arm_msgs::msg::ArmJoint::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_ArmJoint_joint(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoint msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::arm_msgs::msg::ArmJoint>()
{
  return arm_msgs::msg::builder::Init_ArmJoint_id();
}

}  // namespace arm_msgs

#endif  // ARM_MSGS__MSG__DETAIL__ARM_JOINT__BUILDER_HPP_
