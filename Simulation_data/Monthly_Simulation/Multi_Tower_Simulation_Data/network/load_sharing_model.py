import numpy as np

class LoadSharingModel:

    def __init__(self, decay=250):

        self.decay = decay
    def distribute(self, base_users, positions, batteries):

            base_users = np.array(base_users)

            # 🔥 capacity based on SOC
            socs = np.array([b.soc for b in batteries])

            # normalize (avoid divide by zero)
            capacity = socs / (np.sum(socs) + 1e-6)

            # total users in system
            total_users = np.sum(base_users)

            # redistribute based on capacity
            effective_users = capacity * total_users

            return effective_users