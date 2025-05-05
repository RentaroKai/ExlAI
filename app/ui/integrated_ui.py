import sys
import logging
logger = logging.getLogger(__name__)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .excel_panel import ExcelPanel
from .ai_panel import AIPanel
from .config_dialog import ConfigDialog

class IntegratedExcelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIエクセル - 統合UI")
        self.setGeometry(100, 100, 1300, 700)
        # メニューバーの作成
        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル")
        # CSV入出力アクション
        from PySide6.QtWidgets import QFileDialog
        load_csv_act = file_menu.addAction("CSV読み込み")
        load_csv_act.triggered.connect(self.load_csv)
        save_csv_act = file_menu.addAction("CSV保存")
        save_csv_act.triggered.connect(self.save_csv)
        settings_menu = menubar.addMenu("設定")
        config_act = settings_menu.addAction("環境設定")
        config_act.triggered.connect(self.open_config_dialog)
        
        # メインウィジェット
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # スプリッター (左右の領域を区切るためのもの)
        h_splitter = QSplitter(Qt.Horizontal)
        
        # 左側：エクセルパネル
        self.excel_panel = ExcelPanel()
        
        # 右側：AIパネル
        # AIPanelを生成し、ExcelPanelへの参照を持たせる
        self.ai_panel = AIPanel()
        self.ai_panel.excel_panel = self.excel_panel
        
        # 水平スプリッターに左右のパネルを追加
        h_splitter.addWidget(self.excel_panel)
        h_splitter.addWidget(self.ai_panel)
        
        # 水平スプリッターの初期サイズ比率を設定（左:右 = 7:3）
        h_splitter.setSizes([700, 300])
        
        # メインレイアウトにスプリッターを追加
        main_layout.addWidget(h_splitter)
        
        # パネル間の連携を設定
        self.connect_panels()
    
    def connect_panels(self):
        """左側パネルと右側パネル間の連携を設定"""
        # 処理ボタンのイベント接続
        self.ai_panel.process_selected_btn.clicked.connect(self.process_selected)
        self.ai_panel.process_all_btn.clicked.connect(self.process_all)
    
    def process_selected(self):
        """選択行のみ処理する"""
        # 現在のルールチェック
        rule_id = self.ai_panel.current_rule
        if not rule_id:
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(self.ai_panel.process_selected_btn.mapToGlobal(self.ai_panel.process_selected_btn.rect().center()), "ルールが選択されていません", self)
            return
        # 処理対象テーブルを判定
        if self.excel_panel.sample_table.hasFocus():
            active_table = self.excel_panel.sample_table
        else:
            active_table = self.excel_panel.data_table
        # 選択行取得
        selected_items = active_table.selectedItems()
        rows = sorted({item.row() for item in selected_items if item.row() > 0})
        if not rows:
            return
        # 入力文字列リスト作成
        inputs = []
        for row in rows:
            item = active_table.item(row, 1)
            inputs.append(item.text() if item and item.text() else "")
        # ルール適用
        try:
            results = self.ai_panel.rule_service.apply_rule(rule_id, inputs)
            from PySide6.QtWidgets import QTableWidgetItem
            from PySide6.QtCore import Qt
            for row, result in zip(rows, results):
                # 進捗列設定
                status = result.get('status')
                mark = '✓' if status == 'success' else '✗'
                check_item = QTableWidgetItem(mark)
                check_item.setTextAlignment(Qt.AlignCenter)
                active_table.setItem(row, 0, check_item)
                # 出力フィールド更新
                output = result.get('output', {})
                for header, val in output.items():
                    # ヘッダー列を検索して更新
                    for c in range(active_table.columnCount()):
                        hdr = active_table.item(0, c)
                        if hdr and hdr.text() == header:
                            active_table.setItem(row, c, QTableWidgetItem(val))
                            break
        except Exception as e:
            logger.error(f"ルール適用エラー: {e}")
    
    def process_all(self):
        """すべての行を処理する"""
        rule_id = self.ai_panel.current_rule
        if not rule_id:
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(self.ai_panel.process_all_btn.mapToGlobal(self.ai_panel.process_all_btn.rect().center()), "ルールが選択されていません", self)
            return
        # 両テーブルの入力リストを構築
        tables = [self.excel_panel.sample_table, self.excel_panel.data_table]
        for tbl in tables:
            inputs = []
            rows = list(range(1, tbl.rowCount()))
            for row in rows:
                item = tbl.item(row, 1)
                inputs.append(item.text() if item and item.text() else "")
            # ルール適用
            try:
                results = self.ai_panel.rule_service.apply_rule(rule_id, inputs)
                from PySide6.QtWidgets import QTableWidgetItem
                from PySide6.QtCore import Qt
                for row, result in zip(rows, results):
                    status = result.get('status')
                    mark = '✓' if status == 'success' else '✗'
                    check_item = QTableWidgetItem(mark)
                    check_item.setTextAlignment(Qt.AlignCenter)
                    tbl.setItem(row, 0, check_item)
                    output = result.get('output', {})
                    for header, val in output.items():
                        for c in range(tbl.columnCount()):
                            hdr = tbl.item(0, c)
                            if hdr and hdr.text() == header:
                                tbl.setItem(row, c, QTableWidgetItem(val))
                                break
            except Exception as e:
                logger.error(f"ルール適用エラー: {e}")

    def load_csv(self):
        from PySide6.QtWidgets import QFileDialog
        import logging
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV読み込み", "", "CSV files (*.csv)")
        if file_path:
            try:
                self.excel_panel.load_csv(file_path)
            except Exception as e:
                logging.error(f"CSV読み込みエラー: {e}")

    def save_csv(self):
        from PySide6.QtWidgets import QFileDialog
        import logging
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV保存", "", "CSV files (*.csv)")
        if file_path:
            try:
                self.excel_panel.save_csv(file_path)
            except Exception as e:
                logging.error(f"CSV保存エラー: {e}")

    def open_config_dialog(self):
        """設定ダイアログを開く"""
        dlg = ConfigDialog(self)
        dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedExcelUI()
    window.show()
    sys.exit(app.exec()) 