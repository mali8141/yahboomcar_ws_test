// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from arm_msgs:msg/ArmJoint.idl
// generated code does not contain a copyright notice

#ifndef ARM_MSGS__MSG__DETAIL__ARM_JOINT__TRAITS_HPP_
#define ARM_MSGS__MSG__DETAIL__ARM_JOINT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "arm_msgs/msg/detail/arm_joint__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace arm_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const ArmJoint & msg,
  std::ostream & out)
{
  out << "{";
  // member: id
  {
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << ", ";
  }

  // member: joint
  {
    out << "joint: ";
    rosidl_generator_traits::value_to_yaml(msg.joint, out);
    out << ", ";
  }

  // member: time
  {
    out << "time: ";
    rosidl_generator_traits::value_to_yaml(msg.time, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ArmJoint & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << "\n";
  }

  // member: joint
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "joint: ";
    rosidl_generator_traits::value_to_yaml(msg.joint, out);
    out << "\n";
  }

  // member: time
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "time: ";
    rosidl_generator_traits::value_to_yaml(msg.time, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ArmJoint & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace arm_msgs

namespace rosidl_generator_traits
{

[[deprecated("use arm_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const arm_msgs::msg::ArmJoint & msg,
  std::ostream & out, size_t indentation = 0)
{
  arm_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use arm_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const arm_msgs::msg::ArmJoint & msg)
{
  return arm_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<arm_msgs::msg::ArmJoint>()
{
  return "arm_msgs::msg::ArmJoint";
}

template<>
inline const char * name<arm_msgs::msg::ArmJoint>()
{
  return "arm_msgs/msg/ArmJoint";
}

template<>
struct has_fixed_size<arm_msgs::msg::ArmJoint>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<arm_msgs::msg::ArmJoint>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<arm_msgs::msg::ArmJoint>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ARM_MSGS__MSG__DETAIL__ARM_JOINT__TRAITS_HPP_
