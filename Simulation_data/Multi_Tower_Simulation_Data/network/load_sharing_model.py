import numpy as np

class LoadSharingModel:

    def __init__(self, decay=250):

        self.decay = decay

    def distribute(self, base_users, positions):

        n = len(base_users)

        effective = base_users.copy()

        for i in range(n):
            xi, yi = positions[i]

            for j in range(n):
                if i == j:
                    continue

                xj, yj = positions[j]

                d = np.sqrt((xi-xj)**2 + (yi-yj)**2)

                influence = np.exp(-d/self.decay)

                effective[i] += 0.25 * base_users[j] * influence

        return effective