from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent, width=2, height=2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#F0F0F0')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
