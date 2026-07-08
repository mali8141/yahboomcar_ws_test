// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from arm_msgs:msg/ArmJoints.idl
// generated code does not contain a copyright notice

#ifndef ARM_MSGS__MSG__DETAIL__ARM_JOINTS__BUILDER_HPP_
#define ARM_MSGS__MSG__DETAIL__ARM_JOINTS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "arm_msgs/msg/detail/arm_joints__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace arm_msgs
{

namespace msg
{

namespace builder
{

class Init_ArmJoints_time
{
public:
  explicit Init_ArmJoints_time(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  ::arm_msgs::msg::ArmJoints time(::arm_msgs::msg::ArmJoints::_time_type arg)
  {
    msg_.time = std::move(arg);
    return std::move(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint6
{
public:
  explicit Init_ArmJoints_joint6(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  Init_ArmJoints_time joint6(::arm_msgs::msg::ArmJoints::_joint6_type arg)
  {
    msg_.joint6 = std::move(arg);
    return Init_ArmJoints_time(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint5
{
public:
  explicit Init_ArmJoints_joint5(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  Init_ArmJoints_joint6 joint5(::arm_msgs::msg::ArmJoints::_joint5_type arg)
  {
    msg_.joint5 = std::move(arg);
    return Init_ArmJoints_joint6(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint4
{
public:
  explicit Init_ArmJoints_joint4(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  Init_ArmJoints_joint5 joint4(::arm_msgs::msg::ArmJoints::_joint4_type arg)
  {
    msg_.joint4 = std::move(arg);
    return Init_ArmJoints_joint5(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint3
{
public:
  explicit Init_ArmJoints_joint3(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  Init_ArmJoints_joint4 joint3(::arm_msgs::msg::ArmJoints::_joint3_type arg)
  {
    msg_.joint3 = std::move(arg);
    return Init_ArmJoints_joint4(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint2
{
public:
  explicit Init_ArmJoints_joint2(::arm_msgs::msg::ArmJoints & msg)
  : msg_(msg)
  {}
  Init_ArmJoints_joint3 joint2(::arm_msgs::msg::ArmJoints::_joint2_type arg)
  {
    msg_.joint2 = std::move(arg);
    return Init_ArmJoints_joint3(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

class Init_ArmJoints_joint1
{
public:
  Init_ArmJoints_joint1()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmJoints_joint2 joint1(::arm_msgs::msg::ArmJoints::_joint1_type arg)
  {
    msg_.joint1 = std::move(arg);
    return Init_ArmJoints_joint2(msg_);
  }

private:
  ::arm_msgs::msg::ArmJoints msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::arm_msgs::msg::ArmJoints>()
{
  return arm_msgs::msg::builder::Init_ArmJoints_joint1();
}

}  // namespace arm_msgs

#endif  // ARM_MSGS__MSG__DETAIL__ARM_JOINTS__BUILDER_HPP_
