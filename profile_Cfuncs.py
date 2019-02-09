import cProfile
import src.Cfuncs as cf

dim_list = [20,20]
beta = 1/8
updates = 5
threshold = 1
rules = [[2,3,3,3],[2,3,3,3]]

head_position, buffer_length, print_position, analysis_position,\
    dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(dim_list)

cProfile.run("""
cf.basic_update(updates, beta, threshold,
                prepair_rule(rules, head_position),
                dim_h, arr_h,
                )
""")
