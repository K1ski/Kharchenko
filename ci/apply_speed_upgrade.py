from __future__ import annotations

from pathlib import Path
import textwrap

PROJECT = Path("HedgeHelper_v0.1.0")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count} in {path}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8", newline="\n")


def patch_capture() -> None:
    path = PROJECT / "hedge_helper" / "capture.py"
    source = path.read_text(encoding="utf-8")
    start = source.find("def enumerate_monitors()")
    if start < 0:
        raise SystemExit("Cannot find enumerate_monitors() in capture.py")

    replacement = textwrap.dedent("""\
    def _windows_primary_monitor_rect() -> tuple[int, int, int, int] | None:
        \"\"\"Return the real Windows primary monitor rectangle, not MSS list index 1.\"\"\"
        import os
        if os.name != "nt":
            return None
        try:
            import ctypes
            from ctypes import wintypes

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            callback_type = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HANDLE,
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                wintypes.LPARAM,
            )
            primary: list[tuple[int, int, int, int]] = []
            user32 = ctypes.windll.user32

            @callback_type
            def visit(handle, _dc, _rect, _data):
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if user32.GetMonitorInfoW(handle, ctypes.byref(info)) and (info.dwFlags & 1):
                    rect = info.rcMonitor
                    primary.append((
                        int(rect.left),
                        int(rect.top),
                        int(rect.right - rect.left),
                        int(rect.bottom - rect.top),
                    ))
                return True

            user32.EnumDisplayMonitors(None, None, visit, 0)
            return primary[0] if primary else None
        except Exception:
            # Never label an arbitrary screen as primary when Windows lookup fails.
            return None


    def enumerate_monitors() -> list[MonitorInfo]:
        try:
            import mss
        except ImportError as exc:
            raise CaptureUnavailable("Не установлен mss. Установите зависимости командой pip install -r requirements.txt.") from exc
        try:
            primary_rect = _windows_primary_monitor_rect()
            with mss.mss() as grabber:
                # MSS indices identify capture targets; they do not identify the Windows primary display.
                monitors = []
                for index, monitor in enumerate(grabber.monitors[1:], start=1):
                    left = int(monitor["left"])
                    top = int(monitor["top"])
                    width = int(monitor["width"])
                    height = int(monitor["height"])
                    rect = (left, top, width, height)
                    monitors.append(MonitorInfo(
                        index=index,
                        left=left,
                        top=top,
                        width=width,
                        height=height,
                        is_primary=(rect == primary_rect) if primary_rect else False,
                    ))
                return monitors
        except Exception as exc:
            raise CaptureUnavailable(f"Не удалось получить список мониторов: {exc}") from exc
    """)
    path.write_text(source[:start] + replacement, encoding="utf-8", newline="\n")


def patch_parser() -> None:
    path = PROJECT / "hedge_helper" / "signal_parser.py"
    replace_once(
        path,
        '    "price": ("цена polymarket", "цена pm", "pm цена", "price"),\n'
        '    "cost": ("затраты polymarket", "затраты pm", "стоимость pm", "cost", "amount"),\n'
        '    "shares": ("количество акций", "акции", "shares", "share count"),',
        '    "price": ("avg. price", "avg price", "average price", "средняя цена", "цена polymarket", "цена pm", "pm цена", "price"),\n'
        '    "cost": ("total invested", "invested amount", "amount invested", "total spent", "amount spent", "затраты polymarket", "затраты pm", "стоимость pm", "cost", "amount"),\n'
        '    "shares": ("potential payout", "potential win", "потенциальная выплата", "возможная выплата", "количество акций", "акции", "shares", "share count"),',
        "Polymarket scanner field aliases",
    )

    replace_once(
        path,
        '    shares = _number(_find_field(lines, LABELS["shares"]))\n\n'
        '    confidence = sum(w.confidence for w in card.words) / max(len(card.words), 1)',
        '    shares = _number(_find_field(lines, LABELS["shares"]))\n'
        '    # In a binary Polymarket market, Potential payout in USDC is the share count.\n'
        '    # If the scanner omits invested cost, derive it from shares × average fill price.\n'
        '    if cost is None and price is not None and shares is not None:\n'
        '        price_fraction = price / Decimal("100") if price > Decimal("1") else price\n'
        '        cost = shares * price_fraction\n\n'
        '    confidence = sum(w.confidence for w in card.words) / max(len(card.words), 1)',
        "Derive invested cost from average price and payout",
    )


def patch_ui() -> None:
    path = PROJECT / "hedge_helper" / "ui.py"

    replace_once(
        path,
        '            ("Акции Polymarket", self.shares_var, "N"),\n'
        '            ("Затраты, USDC", self.cost_var, "C"),',
        '            ("Shares / Potential payout Polymarket", self.shares_var, "N"),\n'
        '            ("Вложено Polymarket, USDC", self.cost_var, "C"),',
        "Clarify auto-filled Polymarket fields",
    )

    replace_once(
        path,
        '            if col == 0:\n'
        '                self.shares_entry = entry\n'
        '            inputs.columnconfigure(col, weight=1)',
        '            if col == 0:\n'
        '                self.shares_entry = entry\n'
        '            elif col == 2:\n'
        '                self.odds_entry = entry\n'
        '            inputs.columnconfigure(col, weight=1)',
        "Retain odds entry for quick focus",
    )

    replace_once(
        path,
        '    def set_from_signal(self, signal: ParsedSignal) -> None:\n'
        '        if signal.validation_status != ValidationStatus.READY or signal.polymarket_shares is None or signal.polymarket_cost_usdc is None:\n'
        '            messagebox.showwarning("Нельзя перенести", "Сигнал не имеет статуса ГОТОВ. Сначала требуется ручная проверка.", parent=self.root)\n'
        '            return\n'
        '        self.shares_var.set(str(signal.polymarket_shares))\n'
        '        self.cost_var.set(str(signal.polymarket_cost_usdc))\n'
        '        self.root.lift()\n'
        '        self._recalculate()',
        '    def set_from_signal(self, signal: ParsedSignal, *, bring_to_front: bool = True) -> None:\n'
        '        if signal.validation_status != ValidationStatus.READY or signal.polymarket_shares is None or signal.polymarket_cost_usdc is None:\n'
        '            messagebox.showwarning("Нельзя перенести", "Сигнал не имеет статуса ГОТОВ. Сначала требуется ручная проверка.", parent=self.root)\n'
        '            return\n'
        '        self.shares_var.set(str(signal.polymarket_shares))\n'
        '        self.cost_var.set(str(signal.polymarket_cost_usdc))\n'
        '        if bring_to_front:\n'
        '            self.root.lift()\n'
        '            if hasattr(self, "odds_entry"):\n'
        '                self.odds_entry.focus_set()\n'
        '        self._recalculate()',
        "Quick signal transfer without stealing focus",
    )

    replace_once(
        path,
        '        self.last_ready_signal: ParsedSignal | None = None\n'
        '        self.tracker = SignalTracker(self.db)',
        '        self.last_ready_signal: ParsedSignal | None = None\n'
        '        self.last_auto_transfer_signature: tuple[str, ...] | None = None\n'
        '        self.auto_transfer_var = tk.BooleanVar(value=self.db.get_setting("auto_transfer_signal", "1") == "1")\n'
        '        self.tracker = SignalTracker(self.db)',
        "Initialize automatic transfer setting",
    )

    replace_once(
        path,
        '        ttk.Button(bottom, text="Очередь проверки OCR", command=self.open_reviews).pack(side="left", padx=7)\n'
        '        ttk.Label(bottom, text="Интервал захвата: 1 секунда", style="Muted.TLabel").pack(side="right")',
        '        ttk.Button(bottom, text="Очередь проверки OCR", command=self.open_reviews).pack(side="left", padx=7)\n'
        '        ttk.Checkbutton(bottom, text="Автоподстановка", variable=self.auto_transfer_var,\n'
        '                        command=self._save_auto_transfer).pack(side="left", padx=7)\n'
        '        ttk.Label(bottom, text="Интервал: 1 сек.", style="Muted.TLabel").pack(side="right")',
        "Add one-toggle automatic position transfer",
    )

    replace_once(
        path,
        '    def _load_monitors(self):\n',
        '    def _save_auto_transfer(self) -> None:\n'
        '        self.db.set_setting("auto_transfer_signal", "1" if self.auto_transfer_var.get() else "0")\n'
        '        self.last_auto_transfer_signature = None\n\n'
        '    def _load_monitors(self):\n',
        "Persist auto-transfer toggle",
    )

    source = path.read_text(encoding="utf-8")
    start = source.find("    def _scan_received(self, signals: list[ParsedSignal], full_scan: bool, error: str | None):")
    end = source.find("    def transfer_ready(self):", start)
    if start < 0 or end < 0:
        raise SystemExit("Cannot find MonitorWindow._scan_received() boundaries")
    replacement = textwrap.dedent("""\
        def _scan_received(self, signals: list[ParsedSignal], full_scan: bool, error: str | None):
            successful = error is None
            try:
                result = self.tracker.process(signals, full_scan=full_scan, successful=successful, error=error)
                for item in result:
                    self._log(f"Сигнал: {item['status']}" + (f" · ID {item['signal_id']}" if item['signal_id'] else " · отправлен на проверку"))

                ready_positions: list[ParsedSignal] = []
                for signal in signals:
                    if signal.validation_status == ValidationStatus.READY:
                        self.last_ready_signal = signal
                        self.transfer_button.configure(state="normal")
                        if signal.polymarket_shares is not None and signal.polymarket_cost_usdc is not None:
                            ready_positions.append(signal)
                    elif signal.validation_status == ValidationStatus.REVIEW:
                        self._log("ПРОВЕРИТЬ: " + " ".join(signal.validation_notes))
                    elif signal.validation_status == ValidationStatus.REJECTED:
                        self._log("ОТКЛОНЁН: " + " ".join(signal.validation_notes))

                # Auto-fill only when one validated position is unambiguous in the selected screen region.
                if self.auto_transfer_var.get() and len(ready_positions) == 1:
                    signal = ready_positions[0]
                    signature = (
                        str(signal.event or ""),
                        str(signal.market or ""),
                        str(signal.bookmaker_outcome or ""),
                        str(signal.polymarket_outcome or ""),
                        str(signal.polymarket_shares),
                        str(signal.polymarket_cost_usdc),
                    )
                    if signature != self.last_auto_transfer_signature:
                        self.app.set_from_signal(signal, bring_to_front=False)
                        self.last_auto_transfer_signature = signature
                        self._log(
                            f"Автоподстановка позиции: {signal.polymarket_shares} shares, "
                            f"вложено {signal.polymarket_cost_usdc} USDC. Введите актуальный коэффициент БК."
                        )
                elif self.auto_transfer_var.get() and len(ready_positions) > 1:
                    self._log("Автоподстановка пропущена: в области найдено несколько готовых позиций. Выберите область с одной карточкой.")

            except Exception as exc:
                self._log(f"Ошибка сохранения результата OCR: {exc}")
            self.count_var.set(f"Сигналов в базе: {len(self.db.list_signals())}")
            self.review_var.set(f"На проверке: {len(self.db.list_reviews())}")
            if error:
                self._log(f"Полный scan не засчитан: {error}")

    """)
    path.write_text(source[:start] + replacement + source[end:], encoding="utf-8", newline="\n")


def add_tests() -> None:
    tests = PROJECT / "tests" / "test_fast_flow_upgrade.py"
    tests.write_text(textwrap.dedent("""\
        from decimal import Decimal

        from hedge_helper.models import CardCandidate
        from hedge_helper.signal_parser import parse_card


        def _card(text: str) -> CardCandidate:
            return CardCandidate(
                text=text,
                words=[],
                top=0,
                bottom=100,
                segmentation_confidence=1.0,
            )


        def test_potential_payout_and_average_price_fill_polymarket_position():
            signal = parse_card(_card(
                "Event: Team A vs Team B\\\\n"
                "Market: Moneyline\\\\n"
                "Bookmaker outcome: Team A\\\\n"
                "Polymarket outcome: Team B\\\\n"
                "Odds: 1.90\\\\n"
                "Avg. Price: 46¢\\\\n"
                "Potential payout: $125.00"
            ))
            assert signal.polymarket_shares == Decimal("125.00")
            assert signal.polymarket_price_cents == Decimal("46")
            assert signal.polymarket_cost_usdc == Decimal("57.5000")


        def test_explicit_invested_amount_takes_precedence_over_derived_cost():
            signal = parse_card(_card(
                "Event: Team A vs Team B\\\\n"
                "Market: Moneyline\\\\n"
                "Bookmaker outcome: Team A\\\\n"
                "Polymarket outcome: Team B\\\\n"
                "Odds: 1.90\\\\n"
                "Avg. Price: 46¢\\\\n"
                "Potential payout: $125.00\\\\n"
                "Amount invested: $57.40"
            ))
            assert signal.polymarket_shares == Decimal("125.00")
            assert signal.polymarket_cost_usdc == Decimal("57.40")
    """), encoding="utf-8", newline="\n")


def main() -> None:
    if not PROJECT.is_dir():
        raise SystemExit(f"Restored source directory not found: {PROJECT}")
    patch_capture()
    patch_parser()
    patch_ui()
    add_tests()
    print("Applied Hedge Helper speed-flow upgrade: real primary-monitor detection, scanner position aliases, auto-fill and tests.")


if __name__ == "__main__":
    main()
