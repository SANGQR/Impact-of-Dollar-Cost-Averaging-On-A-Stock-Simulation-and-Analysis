import sys
import os
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton,
    QGroupBox, QCheckBox, QSizePolicy, QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.simulation import random_simulation, dca_simulation, monte_carlo


class SimWorker(QThread):
    result_single = Signal(list, str)
    result_mc = Signal(list, list, str)

    def __init__(self, sim, use_mc, mc_n, sim_kwargs, label):
        super().__init__()
        self.sim = sim
        self.use_mc = use_mc
        self.mc_n = mc_n
        self.sim_kwargs = sim_kwargs
        self.label = label
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _should_stop(self):
        return self._cancelled

    def run(self):
        if self.use_mc:
            mean, histories = monte_carlo(
                sim=self.sim, n=self.mc_n,
                should_stop=self._should_stop,
                **self.sim_kwargs,
            )
            if not self._cancelled and mean:
                title = f"Monte Carlo ({len(histories)} runs) — {self.label}"
                self.result_mc.emit(mean, histories, title)
        else:
            if self.sim == "random":
                _, price_history = random_simulation(should_stop=self._should_stop, **self.sim_kwargs)
            else:
                _, price_history = dca_simulation(should_stop=self._should_stop, **self.sim_kwargs)
            if not self._cancelled and price_history:
                self.result_single.emit(price_history, self.label)


class SimCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ax.set_title("Run a simulation to see results")
        self.ax.set_xlabel("Day (Tick)")
        self.ax.set_ylabel("Price")
        self.fig.tight_layout()

    def _finish(self, ticks, title):
        self.ax.set_title(title)
        self.ax.set_xlabel("Day (Tick)")
        self.ax.set_ylabel("Price")
        self.ax.set_xlim(0, ticks)
        self.ax.set_xticks(range(0, ticks + 1, 30))
        self.fig.tight_layout()
        self.draw()

    def plot(self, price_history, title):
        self.ax.clear()
        self.ax.plot(price_history, linewidth=0.8)
        self._finish(len(price_history), title)

    def plot_monte_carlo(self, mean, histories, title):
        self.ax.clear()
        for run in histories:
            self.ax.plot(run, color="steelblue", alpha=0.1, linewidth=0.5)
        self.ax.plot(mean, color="steelblue", linewidth=1.8, label="mean")
        self.ax.legend()
        self._finish(len(mean), title)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Price Simulation")
        self.resize(1100, 600)
        self._worker = None
        self._last_result = None  # ("single", data) | ("mc", data)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(400)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_step = 0

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Left control panel
        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)
        left.setSpacing(6)
        root.addLayout(left, stretch=0)

        left.addWidget(QLabel("Simulation"))
        self.sim_combo = QComboBox()
        self.sim_combo.addItems(["Random", "DCA"])
        self.sim_combo.currentTextChanged.connect(self._on_sim_changed)
        left.addWidget(self.sim_combo)

        left.addWidget(QLabel("Initial Price"))
        self.initial_price = QDoubleSpinBox()
        self.initial_price.setRange(1, 1000000)
        self.initial_price.setValue(100)
        left.addWidget(self.initial_price)

        left.addWidget(QLabel("Days (ticks)"))
        self.ticks = QSpinBox()
        self.ticks.setRange(1, 100000)
        self.ticks.setValue(1000)
        left.addWidget(self.ticks)

        seed_row = QHBoxLayout()
        self.use_seed = QCheckBox("Seed")
        self.seed_input = QSpinBox()
        self.seed_input.setRange(0, 2**31 - 1)
        self.seed_input.setEnabled(False)
        self.use_seed.toggled.connect(self.seed_input.setEnabled)
        seed_row.addWidget(self.use_seed)
        seed_row.addWidget(self.seed_input)
        left.addLayout(seed_row)

        # Random sim params
        self.rand_group = QGroupBox("Random")
        rand_layout = QVBoxLayout(self.rand_group)
        rand_layout.addWidget(QLabel("Agents"))
        self.num_agents = QSpinBox()
        self.num_agents.setRange(1, 10000)
        self.num_agents.setValue(100)
        rand_layout.addWidget(self.num_agents)
        left.addWidget(self.rand_group)

        # DCA sim params
        self.dca_group = QGroupBox("DCA")
        dca_layout = QVBoxLayout(self.dca_group)
        dca_layout.addWidget(QLabel("DCA Agents"))
        self.num_dca = QSpinBox()
        self.num_dca.setRange(1, 10000)
        self.num_dca.setValue(10)
        dca_layout.addWidget(self.num_dca)
        dca_layout.addWidget(QLabel("Random Agents"))
        self.num_rand = QSpinBox()
        self.num_rand.setRange(1, 10000)
        self.num_rand.setValue(90)
        dca_layout.addWidget(self.num_rand)
        left.addWidget(self.dca_group)
        self.dca_group.setVisible(False)

        # Monte Carlo
        self.mc_group = QGroupBox("Monte Carlo")
        self.mc_group.setCheckable(True)
        self.mc_group.setChecked(False)
        mc_layout = QVBoxLayout(self.mc_group)
        mc_layout.addWidget(QLabel("Runs (n)"))
        self.mc_n = QSpinBox()
        self.mc_n.setRange(1, 10000)
        self.mc_n.setValue(50)
        mc_layout.addWidget(self.mc_n)
        left.addWidget(self.mc_group)

        # Run / Stop buttons
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.setToolTip("Run the simulation with the selected parameters")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.stop_btn)
        left.addLayout(btn_row)

        self.save_btn = QPushButton("Save Results")
        self.save_btn.setToolTip("Save the current chart as PNG and data as CSV")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save)
        left.addWidget(self.save_btn)

        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        left.addWidget(self.status_label)

        # Chart
        self.canvas = SimCanvas()
        root.addWidget(self.canvas, stretch=1)

    def _on_sim_changed(self, sim):
        self.rand_group.setVisible(sim == "random")
        self.dca_group.setVisible(sim == "dca")

    def _tick_anim(self):
        dots = "." * (self._anim_step % 4)
        self.status_label.setText(f"Simulating{dots}")
        self._anim_step += 1

    def _set_running(self, running):
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.status_label.setVisible(running)
        if running:
            self._anim_step = 0
            self._anim_timer.start()
        else:
            self._anim_timer.stop()
            self.status_label.setText("")

    def _run(self):
        seed = self.seed_input.value() if self.use_seed.isChecked() else None
        sim = self.sim_combo.currentText()
        ticks = self.ticks.value()
        initial_price = self.initial_price.value()
        use_mc = self.mc_group.isChecked()

        if sim == "Random":
            n = self.num_agents.value()
            sim_kwargs = dict(initial_price=initial_price, ticks=ticks, seed=seed, num_agents=n)
            label = f"Random | {n} agents | {ticks} ticks"
        else:
            n_dca = self.num_dca.value()
            n_rand = self.num_rand.value()
            sim_kwargs = dict(initial_price=initial_price, ticks=ticks, seed=seed,
                              num_dca_agents=n_dca, num_rand_agents=n_rand)
            label = f"DCA | {n_dca} DCA + {n_rand} random | {ticks} ticks"

        self._worker = SimWorker(sim, use_mc, self.mc_n.value(), sim_kwargs, label)
        self._worker.result_single.connect(self.canvas.plot)
        self._worker.result_single.connect(self._store_single)
        self._worker.result_mc.connect(self.canvas.plot_monte_carlo)
        self._worker.result_mc.connect(self._store_mc)
        self._worker.finished.connect(self._on_done)
        self._set_running(True)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.cancel()

    def _store_single(self, price_history, title):
        self._last_result = ("single", {"price_history": price_history, "title": title})
        self.save_btn.setEnabled(True)

    def _store_mc(self, mean, histories, title):
        self._last_result = ("mc", {"mean": mean, "histories": histories, "title": title})
        self.save_btn.setEnabled(True)

    def _save(self):
        if self._last_result is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "PNG Image (*.png)"
        )
        if not path:
            return

        base = os.path.splitext(path)[0]
        self.canvas.fig.savefig(base + ".png", dpi=150, bbox_inches="tight")

        kind, data = self._last_result
        if kind == "single":
            np.savetxt(
                base + ".csv",
                np.array(data["price_history"]),
                delimiter=",",
                header="price_history",
                comments="",
            )
        else:
            runs = np.array(data["histories"])        # (n_runs, ticks)
            mean = np.array(data["mean"])             # (ticks,)
            columns = np.column_stack([mean, runs.T]) # (ticks, 1 + n_runs)
            header = ",".join(["mean"] + [f"run_{i}" for i in range(len(runs))])
            np.savetxt(base + ".csv", columns, delimiter=",", header=header, comments="")

    def _on_done(self):
        self._set_running(False)
        self.status_label.setText("Simulation complete")
        self._worker = None


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
