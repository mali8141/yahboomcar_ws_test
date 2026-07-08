#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to arm_msgs__msg__ArmJoint

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ArmJoint::default())
  }
}

impl rosidl_runtime_rs::Message for ArmJoint {
  type RmwMsg = super::msg::rmw::ArmJoint;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        joint: msg.joint,
        time: msg.time,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      joint: msg.joint,
      time: msg.time,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      joint: msg.joint,
      time: msg.time,
    }
  }
}


// Corresponds to arm_msgs__msg__ArmJoints

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ArmJoints::default())
  }
}

impl rosidl_runtime_rs::Message for ArmJoints {
  type RmwMsg = super::msg::rmw::ArmJoints;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        joint1: msg.joint1,
        joint2: msg.joint2,
        joint3: msg.joint3,
        joint4: msg.joint4,
        joint5: msg.joint5,
        joint6: msg.joint6,
        time: msg.time,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      joint1: msg.joint1,
      joint2: msg.joint2,
      joint3: msg.joint3,
      joint4: msg.joint4,
      joint5: msg.joint5,
      joint6: msg.joint6,
      time: msg.time,
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
      time: msg.time,
    }
  }
}


