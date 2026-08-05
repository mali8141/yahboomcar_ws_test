import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/pawan/yahboomcar_ws/install/M3Pro_MoveIt_demo'
