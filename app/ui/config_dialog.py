from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
from utils.config import config_manager

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.resize(400, 200)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        config = config_manager.get_config()
        # APIキー
        self.api_key_edit = QLineEdit(config.get('gemini_api_key', ''))
        form.addRow("APIキー:", self.api_key_edit)
        # モデル設定
        models = config.get('models', {})
        self.trans_edit = QLineEdit(models.get('gemini_transcription', ''))
        form.addRow("Transcription Model:", self.trans_edit)
        self.minutes_edit = QLineEdit(models.get('gemini_minutes', ''))
        form.addRow("Minutes Model:", self.minutes_edit)
        self.title_edit = QLineEdit(models.get('gemini_title', ''))
        form.addRow("Title Model:", self.title_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_accept(self):
        # 設定更新
        cfg = config_manager.get_config()
        cfg['gemini_api_key'] = self.api_key_edit.text().strip()
        if 'models' not in cfg:
            cfg['models'] = {}
        cfg['models']['gemini_transcription'] = self.trans_edit.text().strip()
        cfg['models']['gemini_minutes'] = self.minutes_edit.text().strip()
        cfg['models']['gemini_title'] = self.title_edit.text().strip()
        config_manager.save_config()
        QMessageBox.information(self, "設定", "設定を保存しました。再起動してください。")
        self.accept() 