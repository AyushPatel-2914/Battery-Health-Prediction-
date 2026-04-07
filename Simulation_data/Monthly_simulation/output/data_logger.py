import matplotlib.pyplot as plt

def plot_results(df):

    plt.figure(figsize=(12,8))

    # USERS
    plt.subplot(3,1,1)
    plt.plot(df["datetime"], df["active_users"])
    plt.title("Active Users Pattern")
    plt.ylabel("Users")

    # POWER
    plt.subplot(3,1,2)
    plt.plot(df["datetime"], df["power_consumption_W"])
    plt.title("Tower Power Consumption")
    plt.ylabel("Power (W)")

    # BATTERY
    plt.subplot(3,1,3)
    plt.plot(df["datetime"], df["battery_soc_percent"])
    plt.title("Battery SOC")
    plt.ylabel("SOC (%)")

    plt.xlabel("Time")

    plt.tight_layout()
    plt.show()