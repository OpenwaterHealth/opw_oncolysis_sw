from oncolysis_ctrl.configurations.constants_global import *
from oncolysis_ctrl.configurations.constants_invivo import *

ID = 'INVIVO_FLANK'
NAME = 'In Vivo - Flank'
CALIB = {100: {'p_ref': 601,
               'coeff_a': 0.000635469,
               'coeff_b': 1.55504},
         150: {'p_ref': 736,
               'coeff_a': 0.00286927,
               'coeff_b': 1.64955},
         230: {'p_ref': 850,
               'coeff_a': 0.00263603,
               'coeff_b': 3.70915}}