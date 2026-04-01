import numpy as np

class UserModel:

    def __init__(self, max_users):

        self.max_users = max_users

    def users(self, hour):

        base = self.max_users * (
            0.25 +
            0.75*np.sin(2*np.pi*(hour-8)/24)**2
        )

        noise = np.random.normal(0, 5)

        users = base + noise

        return max(users, 0)