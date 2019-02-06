import array

from src.Pfuncs import *
from src.Cfuncs import *
from src.PHifuncs import *

if __name__ =="__main__":
    screendim1 = [38,149]
    screendim2 = [45,192]
    screendim3 = [57,268]
    head_pos, buf_siz, print_pos, analysis_pos, dim_v, arr_v, buf_v =\
        init(screendim2, [[2,3,3,3]])
    h_st = 0; h_p = -1; h_w = 1; v_st = 0; v_p = -1; v_w = 2;
    while True:
        head_pos += 1
        basic_update(100, 1/8, 0.99, array.array('i', [0,0,0,0]), h_st, h_p, h_w,\
                     v_st, v_p, v_w, prepair_rule([[2,5,4,6],[3,4,3,6]], head_pos),\
                     dim_v, arr_v)
        basic_print(array.array('i', [0,0,0,0]), h_st, h_p, h_w,\
                    v_st, v_p, v_w, dim_v, arr_v)
        time.sleep(0.1)
        h_st += h_w; v_st += v_w
