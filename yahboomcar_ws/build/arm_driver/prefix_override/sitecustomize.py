import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/pawan/yahboomcar_ws_test/yahboomcar_ws/install/arm_driver'
