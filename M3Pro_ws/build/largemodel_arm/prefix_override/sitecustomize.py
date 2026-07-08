import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/pawan/yahboomcar_ws_test/M3Pro_ws/install/largemodel_arm'
