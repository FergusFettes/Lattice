import array

from src.Pfuncs import *
from src.Cfuncs import *
from src.PHifuncs import *

if __name__ =="__main__":
    screendim1 = [38,149]
    screendim2 = [45,192]
    screendim3 = [57,268]
    dim = array.array('i', screendim1)
    dim_v = memoryview(dim)
    arr_v = init_array(dim_v)
    clear_array(arr_v)
    h_st = 0; h_p = -1; h_w = 1; v_st = 0; v_p = -1; v_w = 2;
    while True:
        basic_update(100, 1/8, 1, array.array('i', [1,1,1,1]), h_st, h_p, h_w, v_st, v_p, v_w, prepair_rule([[2,3,3,3]], 1), dim_v, arr_v)
        basic_print(array.array('i', [1,1,1,1]), h_st, h_p, h_w, v_st, v_p, v_w, dim_v, arr_v)
        time.sleep(0.1)
        h_st += h_w; v_st += v_w
