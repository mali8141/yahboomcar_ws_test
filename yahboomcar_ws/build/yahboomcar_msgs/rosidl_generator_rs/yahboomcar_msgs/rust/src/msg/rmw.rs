#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "yahboomcar_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__ImageMsg() -> *const std::ffi::c_void;
}

#[link(name = "yahboomcar_msgs__rosidl_generator_c")]
extern "C" {
    fn yahboomcar_msgs__msg__ImageMsg__init(msg: *mut ImageMsg) -> bool;
    fn yahboomcar_msgs__msg__ImageMsg__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ImageMsg>, size: usize) -> bool;
    fn yahboomcar_msgs__msg__ImageMsg__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ImageMsg>);
    fn yahboomcar_msgs__msg__ImageMsg__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ImageMsg>, out_seq: *mut rosidl_runtime_rs::Sequence<ImageMsg>) -> bool;
}

// Corresponds to yahboomcar_msgs__msg__ImageMsg
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ImageMsg {

    // This member is not documented.
    #[allow(missing_docs)]
    pub height: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub width: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub channels: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub data: rosidl_runtime_rs::Sequence<u8>,

}



impl Default for ImageMsg {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !yahboomcar_msgs__msg__ImageMsg__init(&mut msg as *mut _) {
        panic!("Call to yahboomcar_msgs__msg__ImageMsg__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ImageMsg {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__ImageMsg__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__ImageMsg__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__ImageMsg__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ImageMsg {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ImageMsg where Self: Sized {
  const TYPE_NAME: &'static str = "yahboomcar_msgs/msg/ImageMsg";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__ImageMsg() }
  }
}


#[link(name = "yahboomcar_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__PointArray() -> *const std::ffi::c_void;
}

#[link(name = "yahboomcar_msgs__rosidl_generator_c")]
extern "C" {
    fn yahboomcar_msgs__msg__PointArray__init(msg: *mut PointArray) -> bool;
    fn yahboomcar_msgs__msg__PointArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PointArray>, size: usize) -> bool;
    fn yahboomcar_msgs__msg__PointArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PointArray>);
    fn yahboomcar_msgs__msg__PointArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PointArray>, out_seq: *mut rosidl_runtime_rs::Sequence<PointArray>) -> bool;
}

// Corresponds to yahboomcar_msgs__msg__PointArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PointArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub points: rosidl_runtime_rs::Sequence<geometry_msgs::msg::rmw::Point>,

}



impl Default for PointArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !yahboomcar_msgs__msg__PointArray__init(&mut msg as *mut _) {
        panic!("Call to yahboomcar_msgs__msg__PointArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PointArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__PointArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__PointArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__PointArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PointArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PointArray where Self: Sized {
  const TYPE_NAME: &'static str = "yahboomcar_msgs/msg/PointArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__PointArray() }
  }
}


#[link(name = "yahboomcar_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__Position() -> *const std::ffi::c_void;
}

#[link(name = "yahboomcar_msgs__rosidl_generator_c")]
extern "C" {
    fn yahboomcar_msgs__msg__Position__init(msg: *mut Position) -> bool;
    fn yahboomcar_msgs__msg__Position__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Position>, size: usize) -> bool;
    fn yahboomcar_msgs__msg__Position__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Position>);
    fn yahboomcar_msgs__msg__Position__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Position>, out_seq: *mut rosidl_runtime_rs::Sequence<Position>) -> bool;
}

// Corresponds to yahboomcar_msgs__msg__Position
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Position {

    // This member is not documented.
    #[allow(missing_docs)]
    pub anglex: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub angley: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance: f32,

}



impl Default for Position {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !yahboomcar_msgs__msg__Position__init(&mut msg as *mut _) {
        panic!("Call to yahboomcar_msgs__msg__Position__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Position {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Position__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Position__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Position__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Position {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Position where Self: Sized {
  const TYPE_NAME: &'static str = "yahboomcar_msgs/msg/Position";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__Position() }
  }
}


#[link(name = "yahboomcar_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__Target() -> *const std::ffi::c_void;
}

#[link(name = "yahboomcar_msgs__rosidl_generator_c")]
extern "C" {
    fn yahboomcar_msgs__msg__Target__init(msg: *mut Target) -> bool;
    fn yahboomcar_msgs__msg__Target__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Target>, size: usize) -> bool;
    fn yahboomcar_msgs__msg__Target__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Target>);
    fn yahboomcar_msgs__msg__Target__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Target>, out_seq: *mut rosidl_runtime_rs::Sequence<Target>) -> bool;
}

// Corresponds to yahboomcar_msgs__msg__Target
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Target {

    // This member is not documented.
    #[allow(missing_docs)]
    pub frame_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::rmw::Time,


    // This member is not documented.
    #[allow(missing_docs)]
    pub scores: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ptx: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pty: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distw: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub disth: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub centerx: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub centery: f32,

}



impl Default for Target {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !yahboomcar_msgs__msg__Target__init(&mut msg as *mut _) {
        panic!("Call to yahboomcar_msgs__msg__Target__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Target {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Target__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Target__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__Target__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Target {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Target where Self: Sized {
  const TYPE_NAME: &'static str = "yahboomcar_msgs/msg/Target";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__Target() }
  }
}


#[link(name = "yahboomcar_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__TargetArray() -> *const std::ffi::c_void;
}

#[link(name = "yahboomcar_msgs__rosidl_generator_c")]
extern "C" {
    fn yahboomcar_msgs__msg__TargetArray__init(msg: *mut TargetArray) -> bool;
    fn yahboomcar_msgs__msg__TargetArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TargetArray>, size: usize) -> bool;
    fn yahboomcar_msgs__msg__TargetArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TargetArray>);
    fn yahboomcar_msgs__msg__TargetArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TargetArray>, out_seq: *mut rosidl_runtime_rs::Sequence<TargetArray>) -> bool;
}

// Corresponds to yahboomcar_msgs__msg__TargetArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TargetArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub data: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Target>,

}



impl Default for TargetArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !yahboomcar_msgs__msg__TargetArray__init(&mut msg as *mut _) {
        panic!("Call to yahboomcar_msgs__msg__TargetArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TargetArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__TargetArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__TargetArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { yahboomcar_msgs__msg__TargetArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TargetArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TargetArray where Self: Sized {
  const TYPE_NAME: &'static str = "yahboomcar_msgs/msg/TargetArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__yahboomcar_msgs__msg__TargetArray() }
  }
}


