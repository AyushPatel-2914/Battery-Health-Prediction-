"""Load sharing model for redistributing users across towers."""

import numpy as np

class LoadSharingModel:

    def __init__(self, decay=250):
        """Initialize the load sharing model.

        The decay parameter is reserved for future distance-based
        redistribution, but the current implementation uses SOC.
        """
        self.decay = decay

    def distribute(self, base_users, positions, batteries):
        """Redistribute users proportionally to tower battery capacity."""
        base_users = np.array(base_users)

        # Use remaining SOC as a proxy for tower capacity
        socs = np.array([b.soc for b in batteries])

        # Avoid divide-by-zero by adding a tiny constant
        capacity = socs / (np.sum(socs) + 1e-6)

        total_users = np.sum(base_users)
        effective_users = capacity * total_users

        return effective_users