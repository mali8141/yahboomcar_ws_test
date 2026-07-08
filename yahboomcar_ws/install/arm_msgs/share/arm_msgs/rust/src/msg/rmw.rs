#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "arm_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_msgs__msg__ArmJoint() -> *const std::ffi::c_void;
}

#[link(name = "arm_msgs__rosidl_generator_c")]
extern "C" {
    fn arm_msgs__msg__ArmJoint__init(msg: *mut ArmJoint) -> bool;
    fn arm_msgs__msg__ArmJoint__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>, size: usize) -> bool;
    fn arm_msgs__msg__ArmJoint__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>);
    fn arm_msgs__msg__ArmJoint__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ArmJoint>, out_seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>) -> bool;
}

// Corresponds to arm_msgs__msg__ArmJoint
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ArmJoint {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub time: i16,

}



impl Default for ArmJoint {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_msgs__msg__ArmJoint__init(&mut msg as *mut _) {
        panic!("Call to arm_msgs__msg__ArmJoint__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ArmJoint {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoint__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoint__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoint__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ArmJoint {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ArmJoint where Self: Sized {
  const TYPE_NAME: &'static str = "arm_msgs/msg/ArmJoint";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_msgs__msg__ArmJoint() }
  }
}


#[link(name = "arm_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_msgs__msg__ArmJoints() -> *const std::ffi::c_void;
}

#[link(name = "arm_msgs__rosidl_generator_c")]
extern "C" {
    fn arm_msgs__msg__ArmJoints__init(msg: *mut ArmJoints) -> bool;
    fn arm_msgs__msg__ArmJoints__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ArmJoints>, size: usize) -> bool;
    fn arm_msgs__msg__ArmJoints__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ArmJoints>);
    fn arm_msgs__msg__ArmJoints__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ArmJoints>, out_seq: *mut rosidl_runtime_rs::Sequence<ArmJoints>) -> bool;
}

// Corresponds to arm_msgs__msg__ArmJoints
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ArmJoints {

    // This member is not documented.
    #[allow(missing_docs)]
    pub joint1: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint2: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint3: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint4: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint5: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint6: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub time: i16,

}



impl Default for ArmJoints {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_msgs__msg__ArmJoints__init(&mut msg as *mut _) {
        panic!("Call to arm_msgs__msg__ArmJoints__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ArmJoints {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoints__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoints__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_msgs__msg__ArmJoints__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ArmJoints {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ArmJoints where Self: Sized {
  const TYPE_NAME: &'static str = "arm_msgs/msg/ArmJoints";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_msgs__msg__ArmJoints() }
  }
}


