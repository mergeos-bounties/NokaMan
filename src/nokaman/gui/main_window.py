"""NokaMan modern Qt desktop demo — multi-language CEFR assessment."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nokaman import __version__
from nokaman.config import OUT_DIR, SAMPLES_DIR
from nokaman.data.loader import list_rubric_files, list_sample_files, load_rubric, load_sample
from nokaman.eval.metrics import batch_evaluate, placement_test
from nokaman.eval.pipeline import evaluate_demo, evaluate_sample_file, evaluate_text
from nokaman.gui.styles import STYLESHEET
from nokaman.rubrics.registry import CEFR_BANDS, SKILLS, SUPPORTED_LANGUAGES, get_language_meta
from nokaman.train.toy_train import train_toy


def _card() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


def _primary(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        " stop:0 #14b8a6, stop:1 #0d9488); color: white; border: none;"
        " border-radius: 10px; padding: 10px 18px; font-weight: 700; }"
        "QPushButton:hover { background: #2dd4bf; color: #042f2e; }"
        "QPushButton:disabled { background: #334155; color: #94a3b8; }"
    )
    return b


def _ghost(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setCheckable(True)
    b.setStyleSheet(
        "QPushButton { text-align: left; background: transparent; border: none;"
        " border-radius: 10px; padding: 12px 14px; color: #94a3b8; font-weight: 600; }"
        "QPushButton:hover { background: #1e293b; color: #e2e8f0; }"
        "QPushButton:checked { background: #115e59; color: #f0fdfa; }"
    )
    return b


class TrainWorker(QThread):
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, epochs: int = 3) -> None:
        super().__init__()
        self.epochs = epochs

    def run(self) -> None:
        try:
            report = train_toy(epochs=self.epochs)
            self.finished_ok.emit(report)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"NokaMan · Language Ability Assessment · v{__version__}")
        self.resize(1140, 740)
        self.setMinimumSize(QSize(940, 600))
        self.setStyleSheet(STYLESHEET)
        self._worker: TrainWorker | None = None

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(210)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 18, 14, 14)
        brand = QLabel("📊 NokaMan")
        brand.setObjectName("brand")
        sl.addWidget(brand)
        sub = QLabel("CEFR assessment demo")
        sub.setObjectName("brandSub")
        sl.addWidget(sub)

        self._nav: list[QPushButton] = []
        self._keys = ["demo", "languages", "evaluate", "samples", "rubrics", "train"]
        labels = {
            "demo": "▶  Full demo",
            "languages": "🌐  Languages",
            "evaluate": "✍️  Evaluate",
            "samples": "📁  Samples",
            "rubrics": "📋  Rubrics",
            "train": "🧠  Train",
        }
        for k in self._keys:
            b = _ghost(labels[k])
            b.clicked.connect(lambda _=False, key=k: self._goto(key))
            self._nav.append(b)
            sl.addWidget(b)
        sl.addStretch(1)
        sl.addWidget(QLabel(f"v{__version__} · offline"))
        root.addWidget(side)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.pages = {
            "demo": self._page_demo(),
            "languages": self._page_languages(),
            "evaluate": self._page_evaluate(),
            "samples": self._page_samples(),
            "rubrics": self._page_rubrics(),
            "train": self._page_train(),
        }
        for w in self.pages.values():
            self.stack.addWidget(w)

        self.setStatusBar(QStatusBar())
        self._status("Ready · multi-language CEFR assessment")
        self._goto("demo")
        self.refresh_samples()
        self.refresh_languages()
        self.refresh_rubrics()

    def _status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def _goto(self, key: str) -> None:
        idx = self._keys.index(key)
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._nav):
            b.setChecked(i == idx)

    # ----- Demo -----
    def _page_demo(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)
        t = QLabel("Full multi-skill demo")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel("Run offline CEFR-style multi-skill evaluation for a language.")
        s.setObjectName("h2")
        lay.addWidget(s)

        form_card = _card()
        fl = QFormLayout(form_card)
        fl.setContentsMargins(18, 14, 18, 14)
        self.demo_lang = QComboBox()
        for code in sorted(SUPPORTED_LANGUAGES):
            meta = get_language_meta(code)
            self.demo_lang.addItem(f"{code} — {meta['name']}", code)
        self.demo_lang.setCurrentIndex(self.demo_lang.findData("en"))
        fl.addRow("Language", self.demo_lang)
        lay.addWidget(form_card)

        card = _card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 18, 18, 18)
        self.demo_progress = QProgressBar()
        self.demo_progress.setRange(0, 0)
        self.demo_progress.setVisible(False)
        cl.addWidget(self.demo_progress)
        self.demo_log = QTextEdit()
        self.demo_log.setReadOnly(True)
        self.demo_log.setMinimumHeight(280)
        self.demo_log.setPlaceholderText("Click Run demo to start…")
        cl.addWidget(self.demo_log)
        lay.addWidget(card, 1)

        row = QHBoxLayout()
        btn = _primary("Run full demo")
        btn.clicked.connect(self.run_full_demo)
        row.addWidget(btn)
        row.addStretch(1)
        lay.addLayout(row)
        return page

    def run_full_demo(self) -> None:
        self.demo_progress.setVisible(True)
        self.demo_log.clear()
        lang = self.demo_lang.currentData() or "en"
        self._append_demo(f"Starting multi-skill demo for language={lang}…")
        try:
            result = evaluate_demo(lang)
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            path = OUT_DIR / f"demo_{lang}.json"
            path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            self._append_demo(f"Language: {result.get('language_name')} ({lang})")
            self._append_demo(f"Demo text: {result.get('demo_text', '')[:160]}…")
            self._append_demo(f"Overall: {result.get('overall')} → CEFR {result.get('cefr')}")
            skills = result.get("skills") or result.get("skill_scores") or {}
            if isinstance(skills, dict) and skills:
                self._append_demo("Skill scores:")
                for sk, sc in skills.items():
                    if isinstance(sc, dict):
                        self._append_demo(f"  · {sk}: {sc}")
                    else:
                        self._append_demo(f"  · {sk}: {sc}")
            self._append_demo(json.dumps(result, indent=2, ensure_ascii=False)[:3500])
            self._append_demo(f"Saved: {path}")
            self._append_demo("Demo complete — offline multi-skill assessment works.")
            self._status(f"Demo complete · {lang} · CEFR {result.get('cefr')}")
            self.refresh_samples()
        except Exception as exc:  # noqa: BLE001
            self._append_demo(f"Error: {exc}")
            QMessageBox.warning(self, "NokaMan", str(exc))
        finally:
            self.demo_progress.setVisible(False)

    def _append_demo(self, line: str) -> None:
        self.demo_log.append(line)

    # ----- Languages -----
    def _page_languages(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Supported languages")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel("Built-in tracks + CEFR / regional frameworks")
        s.setObjectName("h2")
        lay.addWidget(s)
        self.lang_table = QTableWidget(0, 3)
        self.lang_table.setHorizontalHeaderLabels(["Code", "Name", "Frameworks"])
        self.lang_table.horizontalHeader().setStretchLastSection(True)
        self.lang_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lang_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.lang_table, 1)
        return page

    def refresh_languages(self) -> None:
        codes = sorted(SUPPORTED_LANGUAGES)
        self.lang_table.setRowCount(len(codes))
        for r, code in enumerate(codes):
            meta = get_language_meta(code)
            for c, val in enumerate(
                [code, meta["name"], ", ".join(meta["frameworks"])]
            ):
                self.lang_table.setItem(r, c, QTableWidgetItem(val))
        self.lang_table.resizeColumnsToContents()

    # ----- Evaluate -----
    def _page_evaluate(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Evaluate learner text")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel("Score free text or a bundled sample → CEFR band + features")
        s.setObjectName("h2")
        lay.addWidget(s)

        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(18, 18, 18, 18)
        self.eval_mode = QComboBox()
        self.eval_mode.addItems(["free text", "sample file", "placement (multi-answer)"])
        self.eval_lang = QComboBox()
        for code in sorted(SUPPORTED_LANGUAGES):
            self.eval_lang.addItem(code, code)
        self.eval_lang.setCurrentIndex(self.eval_lang.findData("en"))
        self.eval_skill = QComboBox()
        self.eval_skill.addItems(list(SKILLS))
        self.eval_skill.setCurrentText("writing")
        self.eval_sample = QComboBox()
        self.eval_text = QTextEdit()
        self.eval_text.setPlaceholderText(
            "Paste learner writing here…\n\n"
            "Example: I enjoy learning languages because it helps me travel."
        )
        self.eval_text.setMinimumHeight(120)
        fl.addRow("Mode", self.eval_mode)
        fl.addRow("Language", self.eval_lang)
        fl.addRow("Skill", self.eval_skill)
        fl.addRow("Sample", self.eval_sample)
        fl.addRow("Text / answers", self.eval_text)
        lay.addWidget(card)

        row = QHBoxLayout()
        btn = _primary("Run evaluation")
        btn.clicked.connect(self.run_evaluate)
        row.addWidget(btn)
        row.addStretch(1)
        lay.addLayout(row)

        self.eval_out = QTextEdit()
        self.eval_out.setReadOnly(True)
        lay.addWidget(self.eval_out, 1)
        return page

    def run_evaluate(self) -> None:
        mode = self.eval_mode.currentText()
        lang = self.eval_lang.currentData() or "en"
        skill = self.eval_skill.currentText() or "writing"
        try:
            if mode == "sample file":
                path_s = self.eval_sample.currentData()
                if not path_s:
                    QMessageBox.information(self, "NokaMan", "No sample selected.")
                    return
                result = evaluate_sample_file(Path(path_s))
            elif mode == "placement (multi-answer)":
                raw = self.eval_text.toPlainText().strip()
                answers = [a.strip() for a in raw.split("\n") if a.strip()]
                if not answers:
                    QMessageBox.information(
                        self, "NokaMan", "Enter one answer per line for placement."
                    )
                    return
                result = placement_test(lang, answers)
            else:
                text = self.eval_text.toPlainText().strip()
                if not text:
                    QMessageBox.information(self, "NokaMan", "Enter learner text.")
                    return
                result = evaluate_text(lang, text, skill=skill)
            self.eval_out.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
            cefr = result.get("cefr")
            self._status(f"Eval done · CEFR {cefr} · score={result.get('score') or result.get('overall')}")
        except Exception as exc:  # noqa: BLE001
            self.eval_out.setPlainText(f"Error: {exc}")

    # ----- Samples -----
    def _page_samples(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Bundled samples")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel(f"Directory: {SAMPLES_DIR}")
        s.setObjectName("h2")
        lay.addWidget(s)
        self.samples_table = QTableWidget(0, 5)
        self.samples_table.setHorizontalHeaderLabels(
            ["File", "Lang", "Skill", "CEFR", "Score"]
        )
        self.samples_table.horizontalHeader().setStretchLastSection(True)
        self.samples_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.samples_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.samples_table, 1)

        row = QHBoxLayout()
        btn_r = _primary("Refresh + score")
        btn_r.clicked.connect(self.refresh_samples)
        btn_b = _ghost("Batch report")
        btn_b.setCheckable(False)
        btn_b.clicked.connect(self.run_batch)
        row.addWidget(btn_r)
        row.addWidget(btn_b)
        row.addStretch(1)
        lay.addLayout(row)

        self.batch_out = QTextEdit()
        self.batch_out.setReadOnly(True)
        self.batch_out.setMaximumHeight(140)
        self.batch_out.setPlaceholderText("Batch metrics appear here…")
        lay.addWidget(self.batch_out)
        return page

    def refresh_samples(self) -> None:
        files = list_sample_files()
        self.samples_table.setRowCount(len(files))
        for r, path in enumerate(files):
            try:
                result = evaluate_sample_file(path)
                vals = [
                    path.name,
                    str(result.get("language", "")),
                    str(result.get("skill", "")),
                    str(result.get("cefr", "")),
                    str(result.get("score", "")),
                ]
            except Exception:  # noqa: BLE001
                sample = load_sample(path)
                vals = [
                    path.name,
                    str(sample.get("language", "")),
                    str(sample.get("skill", "")),
                    str(sample.get("expected_cefr", "")),
                    "—",
                ]
            for c, val in enumerate(vals):
                self.samples_table.setItem(r, c, QTableWidgetItem(val))
        self.samples_table.resizeColumnsToContents()

        if hasattr(self, "eval_sample"):
            cur = self.eval_sample.currentText()
            self.eval_sample.clear()
            for path in files:
                self.eval_sample.addItem(path.name, str(path))
            if cur:
                i = self.eval_sample.findText(cur)
                if i >= 0:
                    self.eval_sample.setCurrentIndex(i)

    def run_batch(self) -> None:
        try:
            report = batch_evaluate()
            summary = {
                "n_samples": report["n_samples"],
                "n_labeled": report["n_labeled"],
                "exact_cefr_hit_rate": report["exact_cefr_hit_rate"],
                "adjacent_cefr_hit_rate": report["adjacent_cefr_hit_rate"],
            }
            self.batch_out.setPlainText(json.dumps(summary, indent=2))
            self._status(
                f"Batch · n={report['n_samples']} exact={report['exact_cefr_hit_rate']}"
            )
            self.refresh_samples()
        except Exception as exc:  # noqa: BLE001
            self.batch_out.setPlainText(f"Error: {exc}")

    # ----- Rubrics -----
    def _page_rubrics(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Skill rubrics")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel(f"Bands: {', '.join(CEFR_BANDS)}")
        s.setObjectName("h2")
        lay.addWidget(s)

        self.rubric_list = QListWidget()
        self.rubric_list.currentItemChanged.connect(self._on_rubric_selected)
        lay.addWidget(self.rubric_list, 1)
        self.rubric_detail = QTextEdit()
        self.rubric_detail.setReadOnly(True)
        self.rubric_detail.setMaximumHeight(220)
        lay.addWidget(self.rubric_detail)
        return page

    def refresh_rubrics(self) -> None:
        self.rubric_list.clear()
        for path in list_rubric_files():
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.rubric_list.addItem(item)
        if self.rubric_list.count():
            self.rubric_list.setCurrentRow(0)

    def _on_rubric_selected(self, current: QListWidgetItem | None, _prev) -> None:
        if not current:
            return
        path = Path(current.data(Qt.ItemDataRole.UserRole))
        try:
            data = load_rubric(path)
            self.rubric_detail.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001
            self.rubric_detail.setPlainText(f"Error: {exc}")

    # ----- Train -----
    def _page_train(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(28, 24, 28, 24)
        t = QLabel("Toy calibration")
        t.setObjectName("h1")
        lay.addWidget(t)
        s = QLabel("Calibrate toy model against labeled samples (exact CEFR hit-rate).")
        s.setObjectName("h2")
        lay.addWidget(s)

        card = _card()
        fl = QFormLayout(card)
        fl.setContentsMargins(18, 18, 18, 18)
        self.epochs = QSpinBox()
        self.epochs.setRange(1, 50)
        self.epochs.setValue(3)
        fl.addRow("Epochs", self.epochs)
        lay.addWidget(card)

        self.train_bar = QProgressBar()
        self.train_bar.setRange(0, 0)
        self.train_bar.setVisible(False)
        lay.addWidget(self.train_bar)

        btn = _primary("Start training")
        btn.clicked.connect(self.run_train)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.train_out = QTextEdit()
        self.train_out.setReadOnly(True)
        lay.addWidget(self.train_out, 1)
        return page

    def run_train(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.train_bar.setVisible(True)
        self.train_out.append(f"Training epochs={self.epochs.value()}…")
        self._worker = TrainWorker(self.epochs.value())
        self._worker.finished_ok.connect(self._train_ok)
        self._worker.failed.connect(self._train_fail)
        self._worker.start()

    def _train_ok(self, report: dict) -> None:
        self.train_bar.setVisible(False)
        self.train_out.append(json.dumps(report, indent=2, default=str)[:4000])
        last = report.get("history", [{}])[-1].get("exact_cefr_hit_rate")
        self._status(f"Train done · exact_cefr_hit_rate={last}")

    def _train_fail(self, msg: str) -> None:
        self.train_bar.setVisible(False)
        self.train_out.append(f"Error: {msg}")
