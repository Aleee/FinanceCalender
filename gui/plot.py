from datetime import datetime, timedelta

from base.canvas import MplCanvas
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

from base.formatting import float_strcommaspace


class PaymentHistoryGraph:
    def __init__(self):
        self.canvas = MplCanvas(self, width=3, height=3, dpi=100)
        self.ax = self.canvas.axes

    def update_plot(self, dates: list, amounts: list):
        dates = dates
        amounts = amounts

        self.canvas.axes.cla()

        # original_dates = ['2025-01-02', '2025-01-08', '2025-02-03', '2025-04-04', '2025-05-08']
        # amounts = [568752.54, 394252.56, 125752.41, 96520.10, 0]
        # dates = [datetime.strptime(d, '%Y-%m-%d') for d in original_dates]

        # 2. Create the plot
        self.ax.plot(dates, amounts, marker='o', markersize=3, linestyle='-')  # Plot the data

        # Optional: Improve readability by rotating the x-axis labels
        self.canvas.fig.autofmt_xdate()

        yticks = []
        amounts_reversed = amounts[::-1]
        min_distance = float(max(amounts)) * 0.05
        for index, y in enumerate(amounts_reversed):
            if index == 0:
                yticks.append(y)
            else:
                if y - amounts_reversed[index - 1] > min_distance:
                    yticks.append(y)
        yticks.reverse()

        xticks = []
        dates_reversed = dates[::-1]
        min_distance = (max(dates) - min(dates)) * 0.05
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
            #if y != max(amounts) and y != 0:
            self.ax.annotate(label,
                            (x, y),
                            textcoords="offset points",
                            xytext=(15, 10),
                            ha='center',
                            fontsize=9)

        #self.canvas.fig.subplots_adjust(bottom=0.22, top=1, left=0.22, right=0.99)

        self.ax.fill_between(dates, amounts, color="lightblue", alpha=0.5)

        self.canvas.fig.tight_layout()
        self.canvas.draw()