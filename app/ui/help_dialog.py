import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QWidget, QPushButton, QScrollArea, 
                             QTextEdit, QGroupBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QIcon

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ExlAI - ヘルプ")
        self.setMinimumSize(900, 700)
        self.setMaximumSize(1200, 800)
        
        # カラーパレット定義
        self.colors = {
            'background': '#f8f9fa',      # 明るいグレー背景（読みやすい）
            'surface': '#e9ecef',         # 薄いグレーサーフェス（落ち着いた）
            'headline': '#212529',        # ダークグレー（メインテキスト）
            'paragraph': '#495057',       # ミディアムグレー（段落テキスト）
            'accent': '#dc3545',          # 赤（ポイント使いのみ）
            'secondary': '#6c757d',       # セカンダリグレー
            'button': '#198754',          # 緑系ボタン（目に優しい）
            'button_text': '#ffffff',     # ボタンテキスト（白）
            'stroke': '#dc3545',          # 赤ストローク（エッジ使い）
            'tertiary': '#f1f3f4'         # 第三色（薄いグレー）
        }
        
        # ダイアログ全体のスタイル設定
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['background']};
                color: {self.colors['headline']};
            }}
        """)
        
        # アイコンの設定
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # ヘッダー部分
        self._create_header(main_layout, base_dir)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {self.colors['surface']};
                background-color: {self.colors['background']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {self.colors['surface']};
                color: {self.colors['paragraph']};
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['button_text']};
            }}
            QTabBar::tab:hover {{
                background-color: {self.colors['accent']};
                color: {self.colors['button_text']};
            }}
        """)
        
        # 各タブを作成
        tab_widget.addTab(self._create_welcome_tab(), "はじめに")
        tab_widget.addTab(self._create_tutorial_tab(), "基本操作")
        tab_widget.addTab(self._create_examples_tab(), "使用例")
        tab_widget.addTab(self._create_faq_tab(), "よくある質問")
        tab_widget.addTab(self._create_tech_tab(), "技術情報")
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        close_button.setFixedWidth(120)
        close_button.setFixedHeight(35)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['button']};
                color: {self.colors['button_text']};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent']};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                transform: translateY(1px);
            }}
        """)
        
        # レイアウトに追加
        main_layout.addWidget(tab_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

    def _create_header(self, main_layout, base_dir):
        """ヘッダー部分を作成"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['surface']};
                border: none;
                border-radius: 16px;
                padding: 30px;
            }}
        """)
        header_frame.setMaximumHeight(140)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(10)
        
        # メインタイトル「HELP」
        help_title = QLabel("HELP")
        help_title.setFont(QFont("Arial", 48, QFont.Bold))
        help_title.setStyleSheet(f"""
            color: {self.colors['headline']}; 
            margin: 0; 
            padding: 0;
            letter-spacing: 8px;
        """)
        help_title.setAlignment(Qt.AlignCenter)
        
        # サブタイトル
        subtitle_label = QLabel("ExlAI ユーザーガイド")
        subtitle_label.setFont(QFont("Arial", 18, QFont.Bold))
        subtitle_label.setStyleSheet(f"""
            color: {self.colors['paragraph']}; 
            margin: 0; 
            padding: 0;
            letter-spacing: 2px;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # 説明文
        desc_label = QLabel("AI powered Excel Assistant")
        desc_label.setFont(QFont("Arial", 14))
        desc_label.setStyleSheet(f"""
            color: {self.colors['secondary']}; 
            margin: 0; 
            padding: 0;
            letter-spacing: 1px;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(help_title)
        header_layout.addWidget(subtitle_label)
        header_layout.addWidget(desc_label)
        
        main_layout.addWidget(header_frame)

    def _create_welcome_tab(self):
        """はじめにタブを作成"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.colors['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['tertiary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.colors['background']};")
        content_layout = QVBoxLayout(content)
        
        # このアプリの魅力
        appeal_group = self._create_styled_group("このアプリの魅力", [
            "エクセル感覚でAI処理",
            "csv形式で出力",
            "画像・動画もOK",
            "無料のAPIキーで今すぐ始められる"
        ], "appeal")
        
        # こんなことができます
        examples_group = self._create_styled_group("こんなことができます", [
            "氏名分割: 「田中太郎」→「田中」「太郎」",
            "文章校正: 誤字脱字の修正、適切な表現への変換",
            "データ整形: バラバラなフォーマットを統一された形式に",
            "分類・抽出: 文章から重要な情報を自動抽出",
            "画像解析: 写真からテキスト情報を抽出・整理",
            "動画処理: 動画内容の要約や分類・タグ付け",
            "パターン変換: 決まったルールでデータを変換"
        ], "examples")
        
        # 安心ポイント
        safety_group = self._create_styled_group("初心者でも安心", [
            "ちょっとづつ試せる: 選択した項目だけ処理できる",
            "やり直し可能: ルールはいつでも修正・再生成できる",
            "無料or安い: 無料モデルや安いモデルで試せる"            
        ], "safety")
        
        content_layout.addWidget(appeal_group)
        content_layout.addWidget(examples_group)
        content_layout.addWidget(safety_group)
        content_layout.addStretch()
        
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)
        
        return tab

    def _create_tutorial_tab(self):
        """基本操作タブを作成"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.colors['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['tertiary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.colors['background']};")
        content_layout = QVBoxLayout(content)
        
        # 準備段階
        prep_group = self._create_step_group("準備: APIキーを取得しよう", "1", [
            "① https://aistudio.google.com/app/apikey にアクセス",
            "② Googleアカウントでログイン",
            "③ 「Create API Key」ボタンをクリック",
            "④ 生成されたAPIキーをコピー",
            "⑤ ExlAIの「設定」メニューから貼り付け"
        ], "完全無料で使えます！クレジットカード登録も不要です。")
        
        # テンプレート作成
        template_group = self._create_step_group("ステップ1: テンプレートを作成", "2", [
            "① 上部の「テンプレート」エリアを確認",
            f"② A列に処理したい元データの例を入力",
            f"③ B列以降に出力したい項目名を入力",
            "④ 最低1行の入力→出力例を作成",
            "⑤ 例が多いほど精度が向上します"
        ], "例: A列「田中太郎」→ B列「姓」→ C列「名」")
        
        # ルール生成
        rule_group = self._create_step_group("ステップ2: AIにルールを学習させる", "3", [
            "① 右側パネルの「テンプレートからルール生成」ボタンをクリック",
            "② AIが処理パターンを分析中... (30秒〜1分程度)",
            "③ 生成完了のメッセージを確認",
            "④ ルール履歴に新しいルールが追加される",
            "⑤ 💡 あらかじめ登録された履歴を参考にすると効率的！"
        ], "失敗した場合: テンプレートの例を増やして再実行してください")
        
        # データ処理
        process_group = self._create_step_group("ステップ3: データを一括処理", "4", [
            "① 下部の「データ入力エリア」（緑枠）を確認",
            "② A列に処理したいデータを入力またはコピペ",
            "③ 「未処理を一括処理」ボタンをクリック",
            "④ AIが各行を自動処理して結果を表示",
            "⑤ エラー行があれば「エラー」と表示される"
        ], "部分処理: 特定の行だけ処理したい場合は「選択行だけ処理」を使用")
        
        # 保存
        save_group = self._create_step_group("ステップ4: 結果を保存", "5", [
            "① メニューバー「ファイル」→「CSV保存」を選択",
            "② 保存先フォルダと名前を指定",
            "③ 保存完了！Excelで開けます",
            "④ 最新データは自動的にバックアップされます"
        ], "自動バックアップ: メニューから「最後の処理データを開く」で復元可能")
        
        content_layout.addWidget(prep_group)
        content_layout.addWidget(template_group)
        content_layout.addWidget(rule_group)
        content_layout.addWidget(process_group)
        content_layout.addWidget(save_group)
        content_layout.addStretch()
        
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)
        
        return tab

    def _create_examples_tab(self):
        """使用例タブを作成"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.colors['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['tertiary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.colors['background']};")
        content_layout = QVBoxLayout(content)
        
        # 例1: 氏名分割
        name_example = self._create_example_group(
            "例1: 氏名を姓と名に分割",
            "テンプレート設定",
            "A列: 田中太郎\nB列: 姓\nC列: 名",
            "期待される出力",
            "A列: 田中太郎 → B列: 田中、C列: 太郎\nA列: 佐藤花子 → B列: 佐藤、C列: 花子"
        )
        
        # 例2: 住所正規化
        address_example = self._create_example_group(
            "例2: 住所の表記統一",
            "テンプレート設定",
            "A列: 東京都渋谷区1-1-1\nB列: 都道府県\nC列: 市区町村\nD列: 番地",
            "期待される出力",
            "A列: 東京都渋谷区1-1-1 → B列: 東京都、C列: 渋谷区、D列: 1-1-1"
        )
        
        # 例3: 文章校正
        text_example = self._create_example_group(
            "例3: 文章の誤字脱字修正",
            "テンプレート設定",
            "A列: お疲れさまでした。明日の会議の資料を送付いたしまず。\nB列: 修正後",
            "期待される出力",
            "A列: お疲れさまでした。明日の会議の資料を送付いたしまず。\n→ B列: お疲れさまでした。明日の会議の資料を送付いたします。"
        )
        
        # 例4: カテゴリ分類
        category_example = self._create_example_group(
            "例4: 商品のカテゴリ分類",
            "テンプレート設定",
            "A列: iPhone 15 Pro\nB列: カテゴリ\nC列: ブランド",
            "期待される出力",
            "A列: iPhone 15 Pro → B列: スマートフォン、C列: Apple\nA列: MacBook Air → B列: ノートPC、C列: Apple"
        )
        
        # 例5: 画像解析
        image_example = self._create_example_group(
            "例5: 画像からの情報抽出",
            "テンプレート設定",
            "A列: 名刺画像のファイルパス\nB列: 会社名\nC列: 氏名\nD列: 職種",
            "期待される出力",
            "A列: card001.jpg → B列: 株式会社ABC、C列: 田中太郎、D列: 営業部\nA列: receipt001.png → B列: コンビニXYZ、C列: レシート、D列: 食品"
        )
        
        # 例6: 動画処理
        video_example = self._create_example_group(
            "例6: 動画内容の分析",
            "テンプレート設定",
            "A列: 動画ファイルパス\nB列: ジャンル\nC列: 要約\nD列: 重要度",
            "期待される出力",
            "A列: meeting001.mp4 → B列: 会議、C列: 来月の売上目標について議論、D列: 高\nA列: tutorial001.mp4 → B列: 教育、C列: エクセル基本操作の説明、D列: 中"
        )
        
        content_layout.addWidget(name_example)
        content_layout.addWidget(address_example)
        content_layout.addWidget(text_example)
        content_layout.addWidget(category_example)
        content_layout.addWidget(image_example)
        content_layout.addWidget(video_example)
        content_layout.addStretch()
        
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)
        
        return tab

    def _create_faq_tab(self):
        """よくある質問タブを作成"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.colors['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['tertiary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.colors['background']};")
        content_layout = QVBoxLayout(content)
        
        # FAQ項目
        faqs = [
            {
                "q": "セルの行数や列数を増やしたい時は？",
                "a": [
                    "・他のアプリ（Excel等）からデータをコピーして、そのままペーストしてください",
                    "・ペーストすると自動的に必要な分だけ行数・列数が増えます",
                    "・【NEW】行ヘッダー・列ヘッダーを右クリックして「挿入」を選択",
                    "・行や列の削除も右クリックメニューから可能です",
                    "・重要な列（AI進捗、A列）や行（ヘッダー行）は保護されており削除できません"
                ]
            },
            {
                "q": "エラーが表示された時は？",
                "a": [
                    "・APIキーが正しく設定されているか確認",
                    "・無料の場合は利用上限に引っかかっている可能性があるので、時間を置いて再実行"
                ]
            },
            {
                "q": "履歴機能を効果的に使うには？",
                "a": [
                    "・右側パネルの「ルール履歴」であらかじめ登録されたルールを確認",
                    "・過去に作成したルールを再利用することで時間を大幅短縮",
                    "・似たような処理パターンがないか履歴をチェック",
                    "・履歴からルールをコピーして、少し修正するだけで新しいルールに",
                    "・よく使うルールは分かりやすい名前を付けて管理"
                ]
            },
            {
                "q": "画像や動画も処理できますか？",
                "a": [
                    "・はい、Gemini APIのマルチモーダル機能により対応",
                    "・画像: 名刺、レシート、文書、図表などの解析が可能",
                    "・動画: 内容の要約、分類、重要シーンの抽出など",
                    "・A列にファイルパスを入力し、抽出したい情報を列見出しで指定",
                    "・対応形式: JPEG、PNG、MP4、MOV等の一般的な形式",
                    "・ファイルサイズの上限: 画像20MB、動画200MB程度まで"
                ]
            },
            {
                "q": "処理の精度を上げるには？",
                "a": [
                    "・設定から高性能なAIモデルに変更する",
                    "・ルールを手動で詳細編集する"
                ]
            },
            {
                "q": "料金について教えて",
                "a": [
                    "・モデルをFlashに指定した場合、無料枠内でほぼ十分",
                    "・画像・動画処理も無料枠内で利用可能",
                    "・大量処理時は有料プランへの切り替えがおすすめ",
                    "・アプリ自体の利用料金は一切かかりません"
                ]
            },
            {
                "q": "データのプライバシーは？",
                "a": [
                    "・無料APIキーの場合、Googleの学習データとして使用される可能性あり",
                    "・機密性の高いデータは有料APIキーの使用を推奨",
                    "・ローカルでの処理ではなく、クラウドAPI経由での処理",
                    "・処理されたデータはアプリ内に残りません",
                    "・詳細はGoogleのプライバシーポリシーを確認"
                ]
            },
            {
                "q": "ファイルの読み込み・保存について",
                "a": [
                    "・CSV形式での読み込み・保存に対応",
                    "・Excelファイル(.xlsx)は一度CSVに変換してから読み込んで",
                    "・最後の処理データはメニューからいつでも復元可能",
                    "・文字エンコードは自動判定（UTF-8推奨）"
                ]
            },
            {
                "q": "設定のカスタマイズ",
                "a": [
                    "・AIモデルの種類を変更可能",
                    "・APIキーの管理"
                ]
            }
        ]
        
        for faq in faqs:
            faq_group = self._create_faq_item(faq["q"], faq["a"])
            content_layout.addWidget(faq_group)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content)
        layout.addWidget(scroll_area)
        
        return tab

    def _create_tech_tab(self):
        """技術情報タブを作成"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {self.colors['background']};")
        layout = QVBoxLayout(tab)
        
        tech_info = QTextEdit()
        tech_info.setReadOnly(True)
        tech_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors['background']};
                color: {self.colors['paragraph']};
                border: 2px solid {self.colors['surface']};
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors['tertiary']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors['button']};
                border-radius: 6px;
                min-height: 20px;
            }}
        """)
        
        tech_info.setHtml(f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: {self.colors['paragraph']};">
                <h2 style="color: {self.colors['headline']}; border-bottom: 2px solid {self.colors['accent']}; padding-bottom: 10px;">
                    開発者向け技術情報
                </h2>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">技術スタック</h3>
                <ul style="margin-left: 20px;">
                    <li><b style="color: {self.colors['headline']};">言語</b>: Python 3.x</li>
                    <li><b style="color: {self.colors['headline']};">UI フレームワーク</b>: PySide6 (Qt for Python)</li>
                    <li><b style="color: {self.colors['headline']};">AI エンジン</b>: Gemini API (google-genai)</li>
                    <li><b style="color: {self.colors['headline']};">データ処理</b>: 標準CSV、pandas互換</li>
                    <li><b style="color: {self.colors['headline']};">パッケージング</b>: PyInstaller</li>
                </ul>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">プロジェクト構造</h3>
                <pre style="background-color: {self.colors['surface']}; color: {self.colors['paragraph']}; padding: 15px; border-radius: 8px; border-left: 4px solid {self.colors['accent']};">
ExlAI/
├── app/                    # アプリケーションコア
│   ├── services/          # ビジネスロジック
│   │   ├── gemini_api.py     # Gemini API連携
│   │   └── rule_service.py   # ルール生成・適用
│   ├── ui/                # ユーザーインターフェース
│   │   ├── integrated_ui.py  # メインウィンドウ
│   │   ├── excel_panel.py    # データテーブル
│   │   ├── ai_panel.py       # AI操作パネル
│   │   └── help_dialog.py    # ヘルプダイアログ
│   └── workers/           # バックグラウンド処理
├── utils/                 # ユーティリティ
├── doc/                   # ドキュメント・画像
├── config.json           # 設定ファイル
├── requirements.txt      # 依存関係
└── run_app.py           # エントリーポイント
                </pre>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">コアコンポーネント</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="background-color: {self.colors['surface']};">
                        <th style="border: 1px solid {self.colors['secondary']}; padding: 12px; text-align: left; color: {self.colors['headline']};">ファイル</th>
                        <th style="border: 1px solid {self.colors['secondary']}; padding: 12px; text-align: left; color: {self.colors['headline']};">役割</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;"><code style="color: {self.colors['accent']};">integrated_ui.py</code></td>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;">メインウィンドウと全体統合</td>
                    </tr>
                    <tr style="background-color: {self.colors['surface']};">
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;"><code style="color: {self.colors['accent']};">excel_panel.py</code></td>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;">エクセル風UIとデータテーブル</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;"><code style="color: {self.colors['accent']};">ai_panel.py</code></td>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;">AIルール管理と処理操作</td>
                    </tr>
                    <tr style="background-color: {self.colors['surface']};">
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;"><code style="color: {self.colors['accent']};">rule_service.py</code></td>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;">ルール生成・適用ロジック</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;"><code style="color: {self.colors['accent']};">gemini_api.py</code></td>
                        <td style="border: 1px solid {self.colors['secondary']}; padding: 12px;">Gemini API連携処理</td>
                    </tr>
                </table>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">開発・実行環境</h3>
                <div style="background-color: {self.colors['surface']}; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 4px solid {self.colors['accent']};">
                    <h4 style="color: {self.colors['headline']};">開発環境セットアップ:</h4>
                    <pre style="background-color: {self.colors['tertiary']}; color: {self.colors['paragraph']}; padding: 10px; border-radius: 6px; margin-top: 10px;">
# 依存関係のインストール
pip install -r requirements.txt

# 開発実行
python run_app.py

# テスト実行
python -m app.ui.integrated_ui</pre>
                </div>
                
                <div style="background-color: {self.colors['surface']}; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid {self.colors['accent']};">
                    <h4 style="color: {self.colors['headline']};">パッケージング:</h4>
                    <pre style="background-color: {self.colors['tertiary']}; color: {self.colors['paragraph']}; padding: 10px; border-radius: 6px; margin-top: 10px;">
# 実行可能ファイル生成
pyinstaller --clean ExlAI.spec</pre>
                </div>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">API連携</h3>
                <p>AIモデルの設定は <code style="color: {self.colors['accent']};">config.json</code> で管理されています：</p>
                <ul style="margin-left: 20px;">
                    <li><b style="color: {self.colors['headline']};">APIキー管理</b>: 暗号化して保存</li>
                    <li><b style="color: {self.colors['headline']};">モデル設定</b>: gemini-pro、gemini-pro-vision等</li>
                    <li><b style="color: {self.colors['headline']};">マルチモーダル対応</b>: 画像・動画ファイルの解析機能</li>
                    <li><b style="color: {self.colors['headline']};">処理オプション</b>: タイムアウト、リトライ回数等</li>
                    <li><b style="color: {self.colors['headline']};">ログ設定</b>: デバッグレベル、出力先等</li>
                </ul>
                
                <h3 style="color: {self.colors['accent']}; margin-top: 30px;">拡張開発</h3>
                <div style="background-color: {self.colors['surface']}; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 4px solid {self.colors['accent']};">
                    <p><b style="color: {self.colors['headline']};">新規AIモデル対応:</b> <code style="color: {self.colors['accent']};">gemini_api.py</code> を拡張</p>
                    <p><b style="color: {self.colors['headline']};">ルール生成ロジック:</b> <code style="color: {self.colors['accent']};">rule_service.py</code> の <code style="color: {self.colors['accent']};">create_rule</code> メソッド</p>
                    <p><b style="color: {self.colors['headline']};">UI拡張:</b> PySide6のMVCパターンに従った設計</p>
                    <p><b style="color: {self.colors['headline']};">データ処理:</b> CSV操作はpandasライクなインターフェース</p>
                </div>
            </div>
        """)
        
        layout.addWidget(tech_info)
        
        return tab

    def _create_styled_group(self, title, items, group_type="default"):
        """スタイル付きグループを作成"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 20px;
                color: {self.colors['headline']};
                border: 2px solid {self.colors['accent']};
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 18px;
                background-color: {self.colors['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                background-color: {self.colors['surface']};
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        for item in items:
            label = QLabel(f"• {item}")
            label.setTextFormat(Qt.RichText)
            label.setWordWrap(True)
            label.setStyleSheet(f"""
                margin: 10px 15px; 
                font-size: 17px; 
                line-height: 1.7;
                color: {self.colors['paragraph']};
            """)
            layout.addWidget(label)
        
        group.setLayout(layout)
        return group

    def _create_step_group(self, title, step_num, items, tip):
        """ステップ付きグループを作成"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 19px;
                color: {self.colors['headline']};
                border: 2px solid {self.colors['accent']};
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 18px;
                background-color: {self.colors['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                background-color: {self.colors['surface']};
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # ステップ内容
        for item in items:
            label = QLabel(item)
            label.setTextFormat(Qt.RichText)
            label.setOpenExternalLinks(True)
            label.setWordWrap(True)
            label.setStyleSheet(f"""
                margin: 10px 15px; 
                font-size: 17px; 
                line-height: 1.7;
                color: {self.colors['paragraph']};
            """)
            layout.addWidget(label)
        
        # ヒント
        if tip:
            tip_label = QLabel(f"💡 {tip}")
            tip_label.setTextFormat(Qt.RichText)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet(f"""
                margin: 15px; 
                padding: 15px; 
                background-color: {self.colors['background']}; 
                border-left: 4px solid {self.colors['accent']}; 
                font-size: 16px;
                border-radius: 6px;
                color: {self.colors['paragraph']};
            """)
            layout.addWidget(tip_label)
        
        group.setLayout(layout)
        return group

    def _create_example_group(self, title, setup_title, setup_content, output_title, output_content):
        """使用例グループを作成"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 19px;
                color: {self.colors['headline']};
                border: 2px solid {self.colors['accent']};
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 18px;
                background-color: {self.colors['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                background-color: {self.colors['surface']};
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # セットアップ部分
        setup_label = QLabel(f"{setup_title}:")
        setup_label.setStyleSheet(f"margin: 10px 15px; font-size: 17px; color: {self.colors['headline']}; font-weight: bold;")
        layout.addWidget(setup_label)
        
        setup_content_label = QLabel(setup_content)
        setup_content_label.setStyleSheet(f"""
            margin: 5px 20px; 
            padding: 15px; 
            background-color: {self.colors['background']}; 
            border-radius: 6px;
            border-left: 3px solid {self.colors['accent']};
            font-family: 'Courier New', monospace;
            font-size: 16px;
            color: {self.colors['paragraph']};
        """)
        layout.addWidget(setup_content_label)
        
        # 出力部分
        output_label = QLabel(f"{output_title}:")
        output_label.setStyleSheet(f"margin: 15px 15px 10px 15px; font-size: 17px; color: {self.colors['headline']}; font-weight: bold;")
        layout.addWidget(output_label)
        
        output_content_label = QLabel(output_content)
        output_content_label.setStyleSheet(f"""
            margin: 5px 20px; 
            padding: 15px; 
            background-color: {self.colors['background']}; 
            border-radius: 6px;
            border-left: 3px solid {self.colors['accent']};
            font-family: 'Courier New', monospace;
            font-size: 16px;
            color: {self.colors['paragraph']};
        """)
        layout.addWidget(output_content_label)
        
        group.setLayout(layout)
        return group

    def _create_faq_item(self, question, answers):
        """FAQ項目を作成"""
        group = QGroupBox(question)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 18px;
                color: {self.colors['headline']};
                border: 2px solid {self.colors['accent']};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: {self.colors['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                background-color: {self.colors['surface']};
                color: {self.colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout()
        for answer in answers:
            label = QLabel(answer)
            label.setWordWrap(True)
            label.setStyleSheet(f"""
                margin: 8px 15px; 
                font-size: 17px; 
                line-height: 1.7;
                color: {self.colors['paragraph']};
            """)
            layout.addWidget(label)
        
        group.setLayout(layout)
        return group

if __name__ == "__main__":
    # テスト用コード
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.exec() 