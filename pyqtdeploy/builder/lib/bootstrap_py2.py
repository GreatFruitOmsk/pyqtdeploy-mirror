import sys
import pyqtdeploy

sys.path = [':/', ':/stdlib', ':/site-packages']
sys.path_hooks = [pyqtdeploy.qrcimporter]
