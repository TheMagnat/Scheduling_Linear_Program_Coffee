import matplotlib.pyplot as plt
import numpy as np


def visualize(employeeHours, employeeNames):

    fig, ax = plt.subplots()

    hours = np.arange(8.5, 20.5, 0.5)
    days = np.arange(1, 7)

    ax.set_xlim(8.5, 20.5)
    ax.set_ylim(0.75, 6.5)
    ax.set_xticks(hours)
    ax.set_yticks(days)
    ax.set_xticklabels([f"{int(h)}:{int((h%1)*60):02d}" for h in hours])
    ax.set_yticklabels(['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'])

    plt.gca().invert_yaxis()

    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for i, employee in enumerate(employeeHours):
        labeled = False
        for j, hours in enumerate(employee):
            if len(hours) == 0:
                continue

            y = [j + 1 + i * 0.075] * len(hours)
            if labeled:
                ax.plot(hours, y, 'k-', linewidth=5, c=colors[i])
            else:
                ax.plot(hours, y, 'k-', linewidth=5, c=colors[i], label=employeeNames[i])
                labeled = True

    # Add legend to the plot
    plt.legend()

    ax.xaxis.grid() # horizontal lines
    
    plt.show()


if __name__ == "__main__":
    visualize(
        [[[14.0, 18.0], [8.5, 14.5], [], [8.5, 14.5], [9.0, 13.5], [18.5, 20.0]], [[8.5, 14.5], [9.0, 15.0], [8.5, 14.5], [], [17.0, 20.0], [13.0, 19.0]], [[], [18.5, 20.0], [13.5, 19.5], [9.0, 15.0], [18.0, 20.0], [9.0, 15.0]], [[], [11.5, 17.5], [18.5, 20.0], [11.5, 17.5], [12.0, 15.5], [8.5, 13.5]], [[9.0, 15.0], [14.0, 19.5], [11.5, 17.5], [17.0, 20.0], [12.0, 17.5], []], [[], [16.5, 20.0], [14.5, 20.0], [14.0, 20.0], [13.0, 19.0], [11.5, 17.0]], [[12.0, 18.0], [], [11.5, 15.0], [17.5, 20.0], [8.5, 13.5], [15.5, 20.0]]],
        ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
    )