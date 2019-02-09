import cProfile
import numpy as np
import array
import Cfuncs as cf

dim_list = [1000,1000]
beta = 1/8
updates = 100
threshold = 0.8
rules = np.array([[2,3,3,3],[2,3,3,3]], np.intc)
vert = array.array('i', [1,1,1,0,1])
hori = array.array('i', [1,1,1,0,1])
bounds = array.array('i', [1,1,1,1])

head_position, print_position, analysis_position, buffer_length, buffer_status,\
    dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(dim_list)


cProfile.run("""
cf.basic_update(updates, beta, threshold,
                cf.prepair_rule(rules, head_position),
                dim_h, arr_h,
                )
 """)
