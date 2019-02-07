import numpy as np

class Wolf():
    #==============WOLFRAM==========================#
    # Make little wolfline and array
    def make(self, random, dim, scale, rule):
        hi = int(dim[1] / scale)
        wid = int(dim[0] / scale)
        if random:
            line = np.random.randint(0, 2, hi, int)
        else:
            line = np.zeros(hi, int)
            line[int(hi / 2)] = 1
        self.wolf = self.wolframgen(line, hi, rule)
        self.wolfarray = np.zeros([wid, hi], bool)

    # Generates the next wolfram line every time it is called
    def gen(self, line, hi, rule):
        rule = str(bin(rule))[2:]   #gets binary repr. of update rule
        while len(rule) < 8:
            rule = '0' + rule
        while True:
            nb = [
                    int(
                        str(line[(i - 1) % hi])
                        + str(line[i])
                        + str(line[(i + 1) % hi]),
                        2)
                    for i in range(hi)
                ]
            line = [int(rule[-i - 1]) for i in nb]
            yield line

    def scroll(self, start, scale, array):
        line = next(self.wolf)
        hi = len(line)
        wid = array.shape[0]
        HI = array.shape[1]
        for i in range(HI):
            for j in range(scale):
                array[(start + j) % wid, i] = line[int(i / scale) % hi]
        return array

    # Creates a wolfram array, typically slightly smaller than the image, which can then
    # be scaled onto the top
    def array(self):
        wid = self.wolfarray.shape[0]
        linegen = self.wolf
        for lin in range(wid):
            line = next(linegen)
            self.wolfarray[lin, ...] = line
        return self.wolfarray

