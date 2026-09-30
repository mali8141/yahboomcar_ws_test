#include "arm_kin/fk_ik_kin.h"

bool arm_getFK(const char *urdf_file, vector<double> &joints, vector<double> &currentPos) {
    (void)urdf_file;
    (void)joints;
    currentPos = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    return false;
}

bool arm_getIK(const char *urdf_file, vector<double> &targetXYZ, vector<double> &targetRPY, vector<double> &outjoints) {
    (void)urdf_file;
    (void)targetXYZ;
    (void)targetRPY;
    outjoints = {0.0, 0.0, 0.0, 0.0, 0.0};
    return false;
}
