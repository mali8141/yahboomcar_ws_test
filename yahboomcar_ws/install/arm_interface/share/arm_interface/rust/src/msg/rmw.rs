#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__ArmJoint() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__ArmJoint__init(msg: *mut ArmJoint) -> bool;
    fn arm_interface__msg__ArmJoint__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>, size: usize) -> bool;
    fn arm_interface__msg__ArmJoint__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>);
    fn arm_interface__msg__ArmJoint__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ArmJoint>, out_seq: *mut rosidl_runtime_rs::Sequence<ArmJoint>) -> bool;
}

// Corresponds to arm_interface__msg__ArmJoint
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ArmJoint {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub run_time: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub angle: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joints: rosidl_runtime_rs::Sequence<f32>,

}



impl Default for ArmJoint {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__ArmJoint__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__ArmJoint__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ArmJoint {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ArmJoint__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ArmJoint__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ArmJoint__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ArmJoint {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ArmJoint where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/ArmJoint";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__ArmJoint() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__AprilTagInfo() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__AprilTagInfo__init(msg: *mut AprilTagInfo) -> bool;
    fn arm_interface__msg__AprilTagInfo__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AprilTagInfo>, size: usize) -> bool;
    fn arm_interface__msg__AprilTagInfo__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AprilTagInfo>);
    fn arm_interface__msg__AprilTagInfo__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AprilTagInfo>, out_seq: *mut rosidl_runtime_rs::Sequence<AprilTagInfo>) -> bool;
}

// Corresponds to arm_interface__msg__AprilTagInfo
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AprilTagInfo {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: i16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f32,

}



impl Default for AprilTagInfo {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__AprilTagInfo__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__AprilTagInfo__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AprilTagInfo {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__AprilTagInfo__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__AprilTagInfo__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__AprilTagInfo__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AprilTagInfo {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AprilTagInfo where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/AprilTagInfo";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__AprilTagInfo() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__CenterXY() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__CenterXY__init(msg: *mut CenterXY) -> bool;
    fn arm_interface__msg__CenterXY__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<CenterXY>, size: usize) -> bool;
    fn arm_interface__msg__CenterXY__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<CenterXY>);
    fn arm_interface__msg__CenterXY__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<CenterXY>, out_seq: *mut rosidl_runtime_rs::Sequence<CenterXY>) -> bool;
}

// Corresponds to arm_interface__msg__CenterXY
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CenterXY {

    // This member is not documented.
    #[allow(missing_docs)]
    pub center_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_y: f32,

}



impl Default for CenterXY {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__CenterXY__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__CenterXY__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for CenterXY {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CenterXY__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CenterXY__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CenterXY__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for CenterXY {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for CenterXY where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/CenterXY";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__CenterXY() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__ShapeInfo() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__ShapeInfo__init(msg: *mut ShapeInfo) -> bool;
    fn arm_interface__msg__ShapeInfo__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ShapeInfo>, size: usize) -> bool;
    fn arm_interface__msg__ShapeInfo__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ShapeInfo>);
    fn arm_interface__msg__ShapeInfo__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ShapeInfo>, out_seq: *mut rosidl_runtime_rs::Sequence<ShapeInfo>) -> bool;
}

// Corresponds to arm_interface__msg__ShapeInfo
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ShapeInfo {

    // This member is not documented.
    #[allow(missing_docs)]
    pub value: rosidl_runtime_rs::Sequence<f32>,

}



impl Default for ShapeInfo {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__ShapeInfo__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__ShapeInfo__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ShapeInfo {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ShapeInfo__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ShapeInfo__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__ShapeInfo__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ShapeInfo {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ShapeInfo where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/ShapeInfo";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__ShapeInfo() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__Yolov5Detect() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__Yolov5Detect__init(msg: *mut Yolov5Detect) -> bool;
    fn arm_interface__msg__Yolov5Detect__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Yolov5Detect>, size: usize) -> bool;
    fn arm_interface__msg__Yolov5Detect__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Yolov5Detect>);
    fn arm_interface__msg__Yolov5Detect__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Yolov5Detect>, out_seq: *mut rosidl_runtime_rs::Sequence<Yolov5Detect>) -> bool;
}

// Corresponds to arm_interface__msg__Yolov5Detect
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Yolov5Detect {

    // This member is not documented.
    #[allow(missing_docs)]
    pub result: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub centerx: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub centery: f32,

}



impl Default for Yolov5Detect {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__Yolov5Detect__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__Yolov5Detect__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Yolov5Detect {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Yolov5Detect__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Yolov5Detect__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Yolov5Detect__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Yolov5Detect {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Yolov5Detect where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/Yolov5Detect";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__Yolov5Detect() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__Position() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__Position__init(msg: *mut Position) -> bool;
    fn arm_interface__msg__Position__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Position>, size: usize) -> bool;
    fn arm_interface__msg__Position__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Position>);
    fn arm_interface__msg__Position__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Position>, out_seq: *mut rosidl_runtime_rs::Sequence<Position>) -> bool;
}

// Corresponds to arm_interface__msg__Position
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Position {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f32,

}



impl Default for Position {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__Position__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__Position__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Position {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Position__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Position__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__Position__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Position {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Position where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/Position";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__Position() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__CurJoints() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__CurJoints__init(msg: *mut CurJoints) -> bool;
    fn arm_interface__msg__CurJoints__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<CurJoints>, size: usize) -> bool;
    fn arm_interface__msg__CurJoints__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<CurJoints>);
    fn arm_interface__msg__CurJoints__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<CurJoints>, out_seq: *mut rosidl_runtime_rs::Sequence<CurJoints>) -> bool;
}

// Corresponds to arm_interface__msg__CurJoints
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct CurJoints {

    // This member is not documented.
    #[allow(missing_docs)]
    pub joints: rosidl_runtime_rs::Sequence<i16>,

}



impl Default for CurJoints {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__CurJoints__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__CurJoints__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for CurJoints {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CurJoints__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CurJoints__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__CurJoints__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for CurJoints {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for CurJoints where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/CurJoints";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__CurJoints() }
  }
}


#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__TargetXYRoll() -> *const std::ffi::c_void;
}

#[link(name = "arm_interface__rosidl_generator_c")]
extern "C" {
    fn arm_interface__msg__TargetXYRoll__init(msg: *mut TargetXYRoll) -> bool;
    fn arm_interface__msg__TargetXYRoll__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TargetXYRoll>, size: usize) -> bool;
    fn arm_interface__msg__TargetXYRoll__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TargetXYRoll>);
    fn arm_interface__msg__TargetXYRoll__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TargetXYRoll>, out_seq: *mut rosidl_runtime_rs::Sequence<TargetXYRoll>) -> bool;
}

// Corresponds to arm_interface__msg__TargetXYRoll
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TargetXYRoll {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub roll: f32,

}



impl Default for TargetXYRoll {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arm_interface__msg__TargetXYRoll__init(&mut msg as *mut _) {
        panic!("Call to arm_interface__msg__TargetXYRoll__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TargetXYRoll {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__TargetXYRoll__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__TargetXYRoll__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arm_interface__msg__TargetXYRoll__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TargetXYRoll {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TargetXYRoll where Self: Sized {
  const TYPE_NAME: &'static str = "arm_interface/msg/TargetXYRoll";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arm_interface__msg__TargetXYRoll() }
  }
}


