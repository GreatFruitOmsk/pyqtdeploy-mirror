# To create the fron version of this, run:
#
#   pyqtdeploy --freeze-c __bootstrap__.py -o frozen_bootstrap.h


import sys
import mfsimport

sys.path = [':/application', ':/stdlib']
sys.path_hooks = [mfsimport.mfsimporter]
