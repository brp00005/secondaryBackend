#!/usr/bin/env python3
"""PyQt6 GUI front-end for the crawler (wraps existing CLI functions).

This GUI intentionally calls existing functions and the `run.py` script
so the CLI remains authoritative; the GUI is a convenience wrapper.
"""
import sys
import os
import io
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QFileDialog,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

import run as runmod
from crawler import DuckDuckGoJobBoardCrawler


class WorkerThread(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # capture stdout/stderr from called functions
        old_out, old_err = sys.stdout, sys.stderr
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            try:
                self.fn(*self.args, **self.kwargs)
            except Exception as e:
                self.log.emit(f"ERROR: {e}\n")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            out = buf_out.getvalue()
            err = buf_err.getvalue()
            if out:
                self.log.emit(out)
            if err:
                self.log.emit(err)
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DuckDuckGo Jobboard Crawler — GUI")
        self._build_ui()

    def _build_ui(self):
        w = QWidget()
        layout = QVBoxLayout()

        # Controls: engine, rate, proxies file, playwright proxy mode, stats file
        ctrl_layout = QHBoxLayout()
        self.engine_cb = QComboBox()
        # default to playwright for more robust scraping
        self.engine_cb.addItems(["playwright", "brave", "duckduckgo"])
        ctrl_layout.addWidget(QLabel("Engine:"))
        ctrl_layout.addWidget(self.engine_cb)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.1)
        self.rate_spin.setValue(1.0)
        self.rate_spin.setSingleStep(0.1)
        ctrl_layout.addWidget(QLabel("Rate (s):"))
        ctrl_layout.addWidget(self.rate_spin)

        layout.addLayout(ctrl_layout)

        p_layout = QHBoxLayout()
        self.proxies_le = QLineEdit()
        self.proxies_le.setPlaceholderText("e.g. proxies.txt (leave blank to skip)")
        p_layout.addWidget(QLabel("Proxies file:"))
        p_layout.addWidget(self.proxies_le)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_proxies)
        p_layout.addWidget(browse_btn)
        layout.addLayout(p_layout)

        p2_layout = QHBoxLayout()
        self.playwright_mode = QComboBox()
        self.playwright_mode.addItems(["none", "single", "rotate"])
        p2_layout.addWidget(QLabel("Playwright proxy mode:"))
        p2_layout.addWidget(self.playwright_mode)

        self.proxy_stats_le = QLineEdit("proxy_stats.json")
        p2_layout.addWidget(QLabel("Proxy stats file:"))
        p2_layout.addWidget(self.proxy_stats_le)
        browse2 = QPushButton("Browse")
        browse2.clicked.connect(self.browse_proxy_stats)
        p2_layout.addWidget(browse2)
        layout.addLayout(p2_layout)

        tune_layout = QHBoxLayout()
        self.max_retries = QSpinBox()
        self.max_retries.setValue(3)
        tune_layout.addWidget(QLabel("Max retries:"))
        tune_layout.addWidget(self.max_retries)
        self.backoff = QDoubleSpinBox()
        self.backoff.setValue(1.0)
        tune_layout.addWidget(QLabel("Backoff:"))
        tune_layout.addWidget(self.backoff)
        self.jitter = QDoubleSpinBox()
        self.jitter.setValue(0.2)
        tune_layout.addWidget(QLabel("Jitter:"))
        tune_layout.addWidget(self.jitter)
        layout.addLayout(tune_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.fetch_btn = QPushButton("Fetch US counties")
        self.fetch_btn.clicked.connect(self.fetch_counties)
        btn_layout.addWidget(self.fetch_btn)

        self.augment_btn = QPushButton("Augment counties (find chambers)")
        self.augment_btn.clicked.connect(self.augment_counties)
        btn_layout.addWidget(self.augment_btn)

        self.run_chambers_btn = QPushButton("Run chambers (full CLI)")
        self.run_chambers_btn.clicked.connect(self.run_chambers)
        btn_layout.addWidget(self.run_chambers_btn)

        self.proxy_dash_btn = QPushButton("Proxy Dashboard")
        self.proxy_dash_btn.clicked.connect(self.open_proxy_dashboard)
        btn_layout.addWidget(self.proxy_dash_btn)

        layout.addLayout(btn_layout)

        # log output
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        w.setLayout(layout)
        self.setCentralWidget(w)

    def browse_proxies(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select proxies file", os.getcwd())
        if p:
            self.proxies_le.setText(p)

    def browse_proxy_stats(self):
        p, _ = QFileDialog.getSaveFileName(self, "Proxy stats file", os.getcwd())
        if p:
            self.proxy_stats_le.setText(p)

    def _append(self, text: str):
        self.log.append(text)

    def fetch_counties(self):
        self._append("Starting county fetch...")
        wiki = "https://en.wikipedia.org/wiki/List_of_United_States_counties_and_county_equivalents"
        t = WorkerThread(runmod.fetch_and_save_counties, wiki, "us_counties.xlsx")
        t.log.connect(self._append)
        t.finished.connect(lambda: self._append("County fetch finished"))
        t.start()

    def _build_crawler_from_ui(self):
        proxies = None
        pfile = self.proxies_le.text().strip()
        if pfile:
            try:
                lines = Path(pfile).read_text().splitlines()
                proxies = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
            except Exception as e:
                self._append(f"Could not read proxies file: {e}")

        c = DuckDuckGoJobBoardCrawler(
            rate_limit=float(self.rate_spin.value()),
            engine=self.engine_cb.currentText(),
            max_retries=int(self.max_retries.value()),
            backoff_factor=float(self.backoff.value()),
            jitter=float(self.jitter.value()),
            proxies=proxies,
            proxy_ban_seconds=300,
            playwright_proxy_mode=self.playwright_mode.currentText(),
            proxy_stats_file=self.proxy_stats_le.text().strip() or None,
        )
        return c

    def augment_counties(self):
        self._append("Starting county->chamber augmentation (this may take a long time)...")
        crawler = self._build_crawler_from_ui()
        t = WorkerThread(runmod.augment_counties_with_chambers, crawler, "us_counties.xlsx")
        t.log.connect(self._append)
        t.finished.connect(lambda: self._append("Augmentation finished"))
        t.start()

    def run_chambers(self):
        self._append("Launching full chambers run (subprocess)...")
        # construct command
        cmd = [sys.executable, str(Path(__file__).parent / "run.py"), "--chambers", "--engine", self.engine_cb.currentText(), "--rate", str(self.rate_spin.value())]
        if self.proxies_le.text().strip():
            cmd.extend(["--proxies", self.proxies_le.text().strip()])
        # add tuning flags
        cmd.extend(["--max-retries", str(self.max_retries.value()), "--backoff-factor", str(self.backoff.value()), "--jitter", str(self.jitter.value())])

        def proc_func():
            import subprocess
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                # printing will be captured by WorkerThread and emitted
                print(line.rstrip())
            p.wait()
            print(f"Process exited: {p.returncode}")

        t = WorkerThread(proc_func)
        t.log.connect(self._append)
        t.finished.connect(lambda: self._append("Subprocess finished"))
        t.start()

    def open_proxy_dashboard(self):
        stats = self.proxy_stats_le.text().strip() or "proxy_stats.json"
        self._append(f"Proxy dashboard output (from {stats}):")
        # run the script and capture output
        def run_dash():
            import subprocess
            dash = Path(__file__).parent / "scripts" / "proxy_dashboard.py"
            if not dash.exists():
                self._append("Proxy dashboard script missing")
                return
            p = subprocess.Popen([sys.executable, str(dash), "--stats", stats], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                self._append(line.rstrip())
            p.wait()
            self._append(f"Proxy dashboard exited: {p.returncode}")

        threading.Thread(target=run_dash, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
