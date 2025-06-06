import sys
import logging
import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QFrame, QLabel, QSplitter,
                              QHeaderView, QAbstractItemView, QStyledItemDelegate, QSlider)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QFont, QColor, QBrush, QPen, QKeySequence, QDragEnterEvent, QDropEvent

logger = logging.getLogger(__name__)

class FileDropTableWidget(QTableWidget):
    """ドラッグ&ドロップ対応のテーブルウィジェット"""
    
    def __init__(self, rows, cols, supported_formats, parent=None):
        super().__init__(rows, cols, parent)
        self.supported_formats = supported_formats  # サポートするファイル形式（例: ['.jpg', '.png']）
        
        # ドラッグ&ドロップを有効化
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
        # 右クリックメニューでコピー・ペーストを可能にする
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QMenu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        
        logger.info(f"FileDropTableWidget initialized - supported formats: {self.supported_formats}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """ドラッグ開始時の処理"""
        if event.mimeData().hasUrls():
            # ファイル形式をチェック
            urls = event.mimeData().urls()
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = Path(file_path).suffix.lower()
                    if file_ext in self.supported_formats:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                logger.info(f"Drag enter accepted - {len(valid_files)} valid files")
            else:
                event.ignore()
                logger.warning(f"Drag enter rejected - no valid files for formats {self.supported_formats}")
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """ドロップ時の処理"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []
            
            # 有効なファイルのみを抽出
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = Path(file_path).suffix.lower()
                    if file_ext in self.supported_formats:
                        valid_files.append(file_path)
            
            if valid_files:
                # ドロップ位置を取得
                position = event.position().toPoint()
                item = self.itemAt(position)
                start_row = item.row() if item else 1  # ヘッダー行を避ける
                start_col = 1  # 「元の値」列（B列）に固定
                
                # ファイルパスをテーブルに追加
                self.add_file_paths(valid_files, start_row, start_col)
                
                event.acceptProposedAction()
                logger.info(f"Drop completed - {len(valid_files)} files added starting at row {start_row}")
            else:
                event.ignore()
                logger.warning("Drop rejected - no valid files")

    def add_file_paths(self, file_paths, start_row, start_col):
        """ファイルパスをテーブルに追加"""
        # 必要に応じてテーブルサイズを拡張
        required_rows = start_row + len(file_paths)
        if required_rows > self.rowCount():
            self.setRowCount(required_rows)
            logger.info(f"Table expanded to {required_rows} rows")
        
        # ファイルパスを追加
        for i, file_path in enumerate(file_paths):
            row = start_row + i
            
            # AI進捗列（A列）に「未処理」を設定
            status_item = QTableWidgetItem("未処理")
            status_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 0, status_item)
            
            # 元の値列（B列）にファイルパスを設定
            path_item = QTableWidgetItem(file_path)
            self.setItem(row, start_col, path_item)
            
            logger.info(f"Added file path at row {row}: {file_path}")

    def open_context_menu(self, position):
        """右クリックメニューを表示"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        copy_act = menu.addAction("コピー")
        paste_act = menu.addAction("ペースト")
        clear_act = menu.addAction("クリア")
        action = menu.exec(self.viewport().mapToGlobal(position))
        
        if action == copy_act:
            self.copy_selection()
        elif action == paste_act:
            self.paste_clipboard()
        elif action == clear_act:
            self.clear_selection()

    def copy_selection(self):
        """選択セルの内容をクリップボードにコピー"""
        from PySide6.QtWidgets import QApplication
        ranges = self.selectedRanges()
        if not ranges:
            return
        rng = ranges[0]
        copied_rows = []
        for row in range(rng.topRow(), rng.bottomRow() + 1):
            cells = []
            for col in range(rng.leftColumn(), rng.rightColumn() + 1):
                item = self.item(row, col)
                cells.append(item.text() if item and item.text() else "")
            copied_rows.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(copied_rows))

    def paste_clipboard(self):
        """クリップボードのテキストをペースト"""
        from PySide6.QtWidgets import QApplication, QTableWidgetItem
        text = QApplication.clipboard().text()
        if not text:
            return
        rows = text.splitlines()
        max_cols = max(len(r.split('\t')) for r in rows)
        cur_r = max(self.currentRow(), 0)
        cur_c = max(self.currentColumn(), 0)
        need_rows = cur_r + len(rows) - self.rowCount()
        need_cols = cur_c + max_cols - self.columnCount()
        if need_rows > 0 or need_cols > 0:
            new_r = self.rowCount() + max(need_rows, 0)
            new_c = self.columnCount() + max(need_cols, 0)
            self.setRowCount(new_r)
            self.setColumnCount(new_c)
        for dr, line in enumerate(rows):
            for dc, val in enumerate(line.split('\t')):
                self.setItem(cur_r + dr, cur_c + dc, QTableWidgetItem(val))

    def clear_selection(self):
        """選択セルをクリア"""
        for item in self.selectedItems():
            item.setText("")


class FileDropBorderDelegate(QStyledItemDelegate):
    """ファイルドロップ用のボーダー描画デリゲート"""
    
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        text = index.data(Qt.DisplayRole)
        
        # 「元の値」列（B列）が空の場合、ドロップ可能を示す枠線を描画
        if index.column() == 1 and not text:
            painter.save()
            pen = QPen(QColor(75, 145, 139))  # ティール色
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)  # 破線でドロップ可能を示す
            painter.setPen(pen)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(rect)
            painter.restore()


class FilePanel(QWidget):
    """画像・動画・音声処理用のファイルパネル"""
    
    def __init__(self, mode="image", parent=None):
        super().__init__(parent)
        self.mode = mode  # "image", "video", or "audio"
        self.supported_formats = self.get_supported_formats()
        self.setup_ui()
        logger.info(f"FilePanel initialized - mode: {self.mode}, formats: {self.supported_formats}")
        
    def get_supported_formats(self):
        """モードに応じたサポートファイル形式を取得"""
        if self.mode == "image":
            return ['.jpg', '.jpeg', '.png']
        elif self.mode == "video":
            return ['.mp4']
        elif self.mode == "audio":
            return ['.mp3']
        else:
            return []
    
    def setup_ui(self):
        """ファイルパネルのUI設定"""
        # レイアウト設定
        self.setStyleSheet("background-color: #F5F7FA;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 垂直スプリッター (上下のテーブルを分割)
        v_splitter = QSplitter(Qt.Vertical)
        
        # 上部テーブル (テンプレート用)
        template_container = self.create_table_container(
            label_text="テンプレ｜ト",
            table_name="template_table",
            rows=4,
            is_template=True
        )
        
        # 下部テーブル (処理エリア用)
        process_container = self.create_table_container(
            label_text="処理エリア",
            table_name="process_table",
            rows=13,
            is_template=False
        )
        
        # スプリッターに追加
        v_splitter.addWidget(template_container)
        v_splitter.addWidget(process_container)
        v_splitter.setSizes([200, 400])  # 初期サイズ比率
        
        layout.addWidget(v_splitter)
        
        # 初期化
        self.setup_initial_data()
    
    def create_table_container(self, label_text, table_name, rows, is_template):
        """テーブルコンテナを作成"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ラベル（縦書き）
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label_color = "#3A506B" if is_template else "#5D4A66"
        label.setStyleSheet(f"background-color: #E8EEF4; border: 1px solid #D1D9E6; padding: 5px; color: {label_color}; font-weight: bold;")
        label.setFixedWidth(25)
        label.setMinimumHeight(120 if is_template else 180)
        label.setWordWrap(True)
        vertical_text = "\n".join(list(label_text))
        label.setText(vertical_text)
        
        # テーブル
        table = FileDropTableWidget(rows, 12, self.supported_formats)
        table.setHorizontalHeaderLabels(["AI進捗", "元の値", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"])
        self.setup_table_style(table)
        table.setItemDelegate(FileDropBorderDelegate(table))
        
        # テーブルを属性として保存
        setattr(self, table_name, table)
        
        # レイアウトに追加
        layout.addWidget(label)
        layout.addWidget(table)
        
        return container
    
    def setup_table_style(self, table):
        """テーブルのスタイル設定"""
        # ヘッダースタイル
        table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #E8EEF4; color: #3A506B; font-weight: bold; border: 1px solid #D1D9E6; }"
        )
        table.verticalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #E8EEF4; color: #3A506B; font-weight: bold; border: 1px solid #D1D9E6; }"
        )
        
        # テーブルスタイル
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                selection-background-color: rgba(75, 145, 139, 0.3);
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(75, 145, 139, 0.3);
            }
        """)
        
        # 列幅とヘッダー設定
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setDefaultSectionSize(100)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 80)  # AI進捗列
        table.setColumnWidth(1, 300)  # 元の値列（ファイルパス用に広く）
        
        # 選択モード
        table.setSelectionBehavior(QAbstractItemView.SelectItems)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 行ヘッダー非表示
        table.verticalHeader().setVisible(False)
    
    def setup_initial_data(self):
        """初期データの設定"""
        # テンプレートテーブルの初期化
        headers = ["AI進捗", "元の値", "???", "???", "???", "???", "???", "???", "???", "???", "???", "???"]
        for col, header in enumerate(headers):
            self.template_table.setItem(0, col, QTableWidgetItem(header))
        
        # 処理テーブルの初期化
        for col, header in enumerate(headers):
            self.process_table.setItem(0, col, QTableWidgetItem(header))
        
        # ドロップヒント表示
        if self.mode == "image":
            mode_text = "画像ファイル"
        elif self.mode == "video":
            mode_text = "動画ファイル"
        elif self.mode == "audio":
            mode_text = "音声ファイル"
        else:
            mode_text = "ファイル"
        hint_text = f"{mode_text}をここにドラッグ&ドロップしてください"
        
        hint_item = QTableWidgetItem(hint_text)
        hint_item.setTextAlignment(Qt.AlignCenter)
        hint_item.setForeground(QColor(128, 128, 128))
        self.template_table.setItem(1, 1, hint_item)
        
        hint_item2 = QTableWidgetItem(hint_text)
        hint_item2.setTextAlignment(Qt.AlignCenter)
        hint_item2.setForeground(QColor(128, 128, 128))
        self.process_table.setItem(1, 1, hint_item2)
    
    def get_file_paths(self, table_name="process_table"):
        """指定されたテーブルからファイルパスを取得"""
        table = getattr(self, table_name)
        file_paths = []
        
        for row in range(1, table.rowCount()):  # ヘッダー行をスキップ
            item = table.item(row, 1)  # 元の値列
            if item and item.text().strip():
                file_path = item.text().strip()
                if os.path.exists(file_path):
                    file_paths.append(file_path)
        
        return file_paths
    
    def clear_table(self, table_name="process_table"):
        """指定されたテーブルをクリア"""
        table = getattr(self, table_name)
        for row in range(1, table.rowCount()):
            for col in range(table.columnCount()):
                table.setItem(row, col, QTableWidgetItem("")) 