from up import *


class pureHandler(pureUps):

    def process(self, job, array):
        if not array.shape == tuple(job['dim']):
            array = super().resize_array(job['dim'])
        if job['clear']:
            array = super().resize_array(array.shape)
        if job['wolfpole'] >= 0:
            array = super().clear_wavefront(job['wolfpos'], job['wolfscale'],
                                    job['wolfpole'], array)
        for i in range(job['noisesteps']):
            array = super().noise_process(job['threshold'], array)
        array = super().set_boundary(job['ub'], job['rb'],
                             job['db'], job['lb'], array)
        if job['isingupdates'] > 0:
            array = super().ising_process(job['isingupdates'],
                                  job['beta'], array)
        if not job['conwayrules'] == []:
            array = super().conway_process(job['conwayrules'], array)
        return array
