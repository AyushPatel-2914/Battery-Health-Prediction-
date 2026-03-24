import numpy as np

class TrafficModel:

    def __init__(self, peak):

        self.peak = peak

    def value(self, hour):

        base = self.peak * (
            0.3
            + 0.7 * np.sin(2*np.pi*(hour-8)/24)**2
        )

        burst = np.random.poisson(3)

        return base + burst