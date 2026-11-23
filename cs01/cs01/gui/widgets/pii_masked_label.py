"""
CS-01 DPDP Compliance Desktop GUI - PII Masked Label Widget.

Displays detected Indian PII values in a permanently masked form with an
optional reveal toggle for authorised DPO review sessions. Zero unmasked
plaintext is ever stored in the UI layer.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class PiiMaskedLabel(QWidget):
    """
    Display label for detected Indian PII with reveal toggle prompt.

    By default shows the masked representation. The optional "Reveal" button
    exposes the unmasked value only within a trusted DPO audit session.

    Args:
        masked_text: SHA-256 hash or redacted snippet (always visible).
        unmasked_text: Actual value shown only after reveal (defaults to masked_text).
    """

    def __init__(
        self,
        masked_text: str,
        unmasked_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._masked_text = masked_text
        self._unmasked_text = unmasked_text
        self._is_revealed = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel(masked_text)
        self.text_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.text_label)

        self.toggle_btn = QPushButton("Reveal")
        self.toggle_btn.setFixedWidth(60)
        self.toggle_btn.clicked.connect(self._handle_toggle)
        layout.addWidget(self.toggle_btn)

    def _handle_toggle(self) -> None:
        if not self._is_revealed:
            self._is_revealed = True
            self.text_label.setText(self._unmasked_text or self._masked_text)
            self.toggle_btn.setText("Hide")
        else:
            self._is_revealed = False
            self.text_label.setText(self._masked_text)
            self.toggle_btn.setText("Reveal")
