import matplotlib.ticker as ticker
import matplotlib.dates as mdates

from base.canvas import MplCanvas
from base.formatting import float_strcommaspace


class PaymentHistoryGraph:
    def __init__(self):
        self.canvas = MplCanvas(self, width=3, height=3, dpi=100)
        self.ax = self.canvas.axes

    def update_plot(self, dates: list, amounts: list):
        self.canvas.axes.cla()
        self.ax.plot(dates, amounts, marker='o', markersize=3, linestyle='-')  # Plot the data
        self.canvas.fig.autofmt_xdate()

        yticks: list = []
        amounts_reversed: list = amounts[::-1]
        min_distance: float = float(max(amounts)) * 0.05
        for index, y in enumerate(amounts_reversed):
            if index == 0:
                yticks.append(y)
            else:
                if y - amounts_reversed[index - 1] > min_distance:
                    yticks.append(y)
        yticks.reverse()

        xticks: list = []
        dates_reversed: list = dates[::-1]
        min_distance = (max(dates) - min(dates)) * 0.07
        for index, x in enumerate(dates_reversed):
            if index == 0 or index == len(dates_reversed) - 1:
                xticks.append(x)
            else:
                if dates_reversed[index - 1] - x > min_distance:
                    if index == len(dates_reversed) - 2 and x - dates_reversed[index + 1] < min_distance:
                        continue
                    xticks.append(x)
        xticks.reverse()

        self.ax.set_xticks(xticks)
        self.ax.set_yticks(yticks)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
        self.ax.tick_params(axis='x', labelsize=8, rotation=45)
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(float_strcommaspace))
        self.ax.tick_params(axis='y', labelsize=8, rotation=0)
        self.ax.set_facecolor('#F0F0F0')
        self.ax.grid(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        for index, x_pos in enumerate(dates):
            self.ax.vlines(x=x_pos, ymin=0, ymax=amounts[index], color='gray', linestyle='--', linewidth=0.5)
        for index, y_pos in enumerate(amounts):
            self.ax.hlines(y=y_pos, xmin=dates[0], xmax=dates[index], color='gray', linestyle='--', linewidth=0.5)

        for i, (x, y) in enumerate(zip(dates, amounts)):
            label = f"{(1-y/max(amounts))*100:.1f}%"
            self.ax.annotate(label,
                            (x, y),
                            textcoords="offset points",
                            xytext=(15, 10),
                            ha='center',
                            fontsize=9)
        self.ax.fill_between(dates, amounts, color="lightblue", alpha=0.5)

        self.canvas.fig.tight_layout()
        self.canvas.draw()
