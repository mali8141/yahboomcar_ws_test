#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to arm_interface__srv__ArmKinemarics_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ArmKinemarics_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub tar_x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub tar_y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub tar_z: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub roll: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pitch: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint1: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint2: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint3: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint4: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint5: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cur_joint6: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub kin_name: std::string::String,

}



impl Default for ArmKinemarics_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ArmKinemarics_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ArmKinemarics_Request {
  type RmwMsg = super::srv::rmw::ArmKinemarics_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        tar_x: msg.tar_x,
        tar_y: msg.tar_y,
        tar_z: msg.tar_z,
        roll: msg.roll,
        pitch: msg.pitch,
        yaw: msg.yaw,
        cur_joint1: msg.cur_joint1,
        cur_joint2: msg.cur_joint2,
        cur_joint3: msg.cur_joint3,
        cur_joint4: msg.cur_joint4,
        cur_joint5: msg.cur_joint5,
        cur_joint6: msg.cur_joint6,
        kin_name: msg.kin_name.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      tar_x: msg.tar_x,
      tar_y: msg.tar_y,
      tar_z: msg.tar_z,
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
      cur_joint1: msg.cur_joint1,
      cur_joint2: msg.cur_joint2,
      cur_joint3: msg.cur_joint3,
      cur_joint4: msg.cur_joint4,
      cur_joint5: msg.cur_joint5,
      cur_joint6: msg.cur_joint6,
        kin_name: msg.kin_name.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      tar_x: msg.tar_x,
      tar_y: msg.tar_y,
      tar_z: msg.tar_z,
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
      cur_joint1: msg.cur_joint1,
      cur_joint2: msg.cur_joint2,
      cur_joint3: msg.cur_joint3,
      cur_joint4: msg.cur_joint4,
      cur_joint5: msg.cur_joint5,
      cur_joint6: msg.cur_joint6,
      kin_name: msg.kin_name.to_string(),
    }
  }
}


// Corresponds to arm_interface__srv__ArmKinemarics_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ArmKinemarics_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub joint1: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint2: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint3: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint4: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint5: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joint6: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub roll: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pitch: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: f64,

}



impl Default for ArmKinemarics_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ArmKinemarics_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ArmKinemarics_Response {
  type RmwMsg = super::srv::rmw::ArmKinemarics_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        joint1: msg.joint1,
        joint2: msg.joint2,
        joint3: msg.joint3,
        joint4: msg.joint4,
        joint5: msg.joint5,
        joint6: msg.joint6,
        x: msg.x,
        y: msg.y,
        z: msg.z,
        roll: msg.roll,
        pitch: msg.pitch,
        yaw: msg.yaw,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      joint1: msg.joint1,
      joint2: msg.joint2,
      joint3: msg.joint3,
      joint4: msg.joint4,
      joint5: msg.joint5,
      joint6: msg.joint6,
      x: msg.x,
      y: msg.y,
      z: msg.z,
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      joint1: msg.joint1,
      joint2: msg.joint2,
      joint3: msg.joint3,
      joint4: msg.joint4,
      joint5: msg.joint5,
      joint6: msg.joint6,
      x: msg.x,
      y: msg.y,
      z: msg.z,
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
    }
  }
}






#[link(name = "arm_interface__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__arm_interface__srv__ArmKinemarics() -> *const std::ffi::c_void;
}

// Corresponds to arm_interface__srv__ArmKinemarics
#[allow(missing_docs, non_camel_case_types)]
pub struct ArmKinemarics;

impl rosidl_runtime_rs::Service for ArmKinemarics {
    type Request = ArmKinemarics_Request;
    type Response = ArmKinemarics_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__arm_interface__srv__ArmKinemarics() }
    }
}


