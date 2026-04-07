import numpy as np

class UserModel:

    def __init__(self, max_users, noise_scale=5.0):

        self.max_users = max_users
        self.noise_scale = noise_scale

    def users(self, hour):

        base = self.max_users * (
            0.25 +
            0.75*np.sin(2*np.pi*(hour-8)/24)**2
        )

        noise = np.random.normal(0, self.noise_scale)

        users = base + noise

        return max(users, 0)