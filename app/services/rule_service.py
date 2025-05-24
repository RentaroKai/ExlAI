import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
import shutil
from pathlib import Path

from utils.config import config_manager
from .gemini_api import GeminiAPI, GeminiAPIError

logger = logging.getLogger(__name__)

class ProcessMode:
    """処理モード定義"""
    NORMAL = "normal"      # テキスト処理
    IMAGE = "image"        # 画像処理  
    VIDEO = "video"        # 動画処理

class RuleService:
    """
    ルール管理APIクライアントのスケルトン
    create_rule / regenerate_rule / get_rules / delete_rule / apply_rule を提供する
    """
    def __init__(self, rules_path: Optional[str] = None):
        # 履歴保存先ファイルパスの設定
        if getattr(sys, 'frozen', False):
            # PyInstaller onefile実行環境時: exeと同じフォルダにpersistentに配置
            exec_dir = os.path.dirname(sys.executable)
            # パッケージ内のデフォルトファイルパス
            packaged_rules = os.path.join(sys._MEIPASS, 'history_rules.json')
            # 永続化用パス
            persistent_rules = os.path.join(exec_dir, 'history_rules.json')
            # 初回起動時にコピー
            if not os.path.exists(persistent_rules):
                try:
                    shutil.copy(packaged_rules, persistent_rules)
                    logger.info(f"Copied default history to {persistent_rules}")
                except Exception as e:
                    logger.error(f"Failed to copy default history_rules.json: {e}")
            self.rules_path = persistent_rules
        else:
            # 通常実行時はUIフォルダ内のhistory_rules.jsonを利用
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            default_path = os.path.join(base_dir, 'app', 'ui', 'history_rules.json')
            self.rules_path = rules_path or default_path
        self._load_rules()
        self.gemini = GeminiAPI()

    def _load_rules(self) -> None:
        """ローカルストレージからルール一覧を読み込む"""
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # JSON が 'rules' キーを持つ場合はその配列を利用、リストの場合はそのまま
                if isinstance(data, dict) and 'rules' in data:
                    self._rules = data['rules']
                elif isinstance(data, list):
                    self._rules = data
                else:
                    logger.warning(f"Unexpected rules format in {self.rules_path}")
                    self._rules = []
                logger.debug(f"Loaded rules from {self.rules_path}")
                
                # IDマイグレーション: idフィールドがないルールに連番IDを付与
                needs_save = False
                for idx, rule in enumerate(self._rules):
                    if "id" not in rule:
                        rule["id"] = idx
                        logger.info(f"Assigned new id={idx} to rule title={rule.get('title')}")
                        needs_save = True
                    # モードマイグレーション: modeフィールドがないルールにnormalモードを付与
                    if "mode" not in rule:
                        rule["mode"] = ProcessMode.NORMAL
                        logger.info(f"Assigned normal mode to rule id={rule.get('id')}")
                        needs_save = True
                
                if needs_save:
                    logger.info("Migrated rules, saving updated rules with IDs and modes.")
                    self._save_rules()

                # --- 追加: stray 'rule_name' キーの削除と重複IDのクリーンアップ ---
                cleanup_save = False
                # 'rule_name' フィールドがあれば削除
                for rule in self._rules:
                    if 'rule_name' in rule:
                        del rule['rule_name']
                        logger.info(f"Removed stray 'rule_name' from rule id={rule.get('id')}")
                        cleanup_save = True
                # 重複IDのルールを除外
                seen_ids = set()
                unique_rules = []
                for rule in self._rules:
                    rid = rule.get('id')
                    if rid in seen_ids:
                        logger.warning(f"Duplicate rule id={rid} detected and removed")
                        cleanup_save = True
                        continue
                    seen_ids.add(rid)
                    unique_rules.append(rule)
                self._rules = unique_rules
                if cleanup_save:
                    logger.info("Cleaned up stray fields and duplicates, saving rules.")
                    self._save_rules()
            except Exception as e:
                logger.error(f"Failed to load rules: {e}")
                self._rules = []
        else:
            self._rules = []

    def _save_rules(self) -> None:
        """現在のルール一覧をローカルストレージに保存する"""
        try:
            with open(self.rules_path, 'w', encoding='utf-8') as f:
                json.dump(self._rules, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved rules to {self.rules_path}")
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")

    def _generate_json_example(self, sample_data: Dict[str, Any]) -> Dict[str, str]:
        """sample_data から json_format_example をヘッダー→空文字のマップ形式で生成する"""
        logger.info("Generating json_format_example map from sample_data...")
        headers = sample_data.get("headers", [])

        # バリデーション: ヘッダーが存在すること
        if not headers:
            logger.error("sample_data missing headers.")
            return {}

        # 出力対象ヘッダーを抽出 (インデックス3以降、空文字除外)
        output_headers = [
            h for idx, h in enumerate(headers, start=1)
            if idx >= 3 and h.strip()
        ]
        logger.debug(f"Output headers for example: {output_headers}")

        if not output_headers:
            logger.warning("No output headers found (column 3 onwards, non-empty). Returning empty example map.")
            return {}

        # 各ヘッダーに対して空文字をセット
        example_map: Dict[str, str] = { key: "" for key in output_headers }
        logger.info(f"Generated json_format_example map with keys: {output_headers}")
        return example_map

    def create_rule(self, samples: List[Dict[str, Any]], mode: str = ProcessMode.NORMAL) -> Dict[str, Any]:
        """
        新規ルールをAIに生成させ、ローカルに保存 (3ステップ：prompt/json例/title)
        引数 samples: [{"input": str, "output": Dict[str,str], "fields": List[str]}]
        引数 mode: 処理モード（ProcessMode定数）
        戻り値: metadata dict (rule_name, etc.)
        """
        # --- 入力サンプルをテーブル形式で構築 ---
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # fields に空文字が含まれている場合は除外する
        fields = [f for f in samples[0].get('fields', []) if f] if samples else []
        headers_init = ["AIの進捗", "元の値"] + fields
        # AIの進捗欄は空文字とし、上部パネルでは値を表示しない
        rows_init = [["", s.get('input','')] + [s.get('output',{}).get(f,'') for f in fields] for s in samples]
        sample_data = {"headers": headers_init, "rows": rows_init}
        logger.debug(f"Generated sample_data: {sample_data}")

        # --- Phase1: 動的プロンプト生成 ---
        prompt_instructions = []
        # ヘッダー説明
        field_list = "、".join(fields)
        prompt_instructions.append(
            f"以下に示すのは、ある入力データ（「元の値」）と、それに対して特定の処理を行った結果得られた複数の出力項目（{field_list}）の具体例です。\n"
        )
        prompt_instructions.append("**データ例:**")
        # サンプルごとの例を動的に生成
        for idx, s in enumerate(samples):
            prompt_instructions.append(f"例{idx+1}")
            prompt_instructions.append(f"元の値: {s.get('input', '')}")
            for f in fields:
                prompt_instructions.append(f"項目名={f}: {s.get('output', {}).get(f, '')}")
        # 依頼部分
        prompt_instructions.append("\n**依頼:**")
        prompt_instructions.append(
            f"これらの入力（元の値）と出力（各項目）の関係性を分析し、「元の値」のようなデータを入力として与えた際に、これらの出力項目（{field_list}）を生成させるためにAIに与えるべき指示（プロンプト）を推測し、作成してください。"
        )
        prompt_instructions.append("\n生成するプロンプトの要件:")
        prompt_instructions.append("* 提示された例だけでなく、他の同様の入力に対しても適用できるような、汎用的な指示にしてください。")
        prompt_instructions.append("* プロンプトは、AIに対する指示として機能する、端的で短い文章にまとめること。返答例は別途添付するためここでは端的な表現を心がけること")
        # JSON形式で出力させ、promptキーの値を取得する指示を追加
        prompt_instructions.append("返答はJSON形式で {\"prompt\": \"<プロンプト>\"} のみを返し、他の文言を含めないでください。")
        # AIに送信するプロンプト全文をログ出力する
        prompt_content = "\n".join(prompt_instructions)
        logger.info(f"★aiに送った全文だよ★\n{prompt_content}")
        try:
            logger.info("Generating rule prompt via Gemini API (JSON format)...")
            resp1 = self.gemini.client.models.generate_content(
                model=self.gemini.transcription_model,
                contents=prompt_content
            )
            text = resp1.text.strip()
            # コードブロックや余分な記号を除去
            if text.startswith("```"):
                text = re.sub(r"```(?:json)?\\n?", "", text)
                text = text.rstrip("`\\n ")
            # JSON部分を抽出してパース
            start = text.find("{")
            end = text.rfind("}")
            json_str = text[start:end+1] if start != -1 and end != -1 else text
            try:
                data = json.loads(json_str)
                rule_prompt = data.get("prompt", "").strip()
                logger.info(f"Parsed rule prompt from JSON: {rule_prompt}")
            except Exception as e:
                logger.error(f"プロンプトJSONパースエラー: {e}, raw text: '{text}'")
                rule_prompt = ""
        except Exception as e:
            logger.error(f"プロンプト生成エラー: {e}")
            rule_prompt = ""

        # --- Phase2: JSONフォーマット例生成 (Pythonで実装) ---
        logger.info("Generating json_format_example using _generate_json_example...")
        json_format_example = self._generate_json_example(sample_data)
        logger.debug(f"Generated json_format_example: {json_format_example}")

        # --- Phase3: タイトル生成 ---
        title_instructions = [
            "次の命令文にふさわしい短いルール名を日本語で返してください。",
            "返答は {\"rule_name\": \"<ルール名>\"} の形式で JSON のみを返し、他の文言を含めないでください。",
            f"命令文: {rule_prompt}"
        ]
        # AIに送信するタイトル生成用プロンプト全文をログ出力する
        title_content = "\n".join(title_instructions)
        logger.info(f"★aiに送った全文だよ★\n{title_content}")
        logger.info("Generating rule title via Gemini API...")
        resp3 = self.gemini.client.models.generate_content(
            model=self.gemini.title_model,
            contents=title_content
        )
        # JSONパースして rule_name を取得
        text = resp3.text.strip()
        # コードブロックやバッククオートを除去
        if text.startswith("```"):
            # ```json や ``` コードブロックマーカーを削除
            text = re.sub(r"```(?:json)?\\n?", "", text)
            text = text.rstrip("`\\n ") # 末尾のバッククオート、改行、スペースを削除
        # JSON部分を抽出
        start = text.find("{")
        end = text.rfind("}")
        json_str = text[start:end+1] if start != -1 and end != -1 else text
        try:
            data = json.loads(json_str)
            rule_name = data.get("rule_name", "").strip()
            logger.info(f"Generated rule title: {rule_name}")
        except Exception as e:
            logger.error(f"タイトルJSONパースエラー: {e}, raw text: '{text}'")
            # フォールバックで生テキストをタイトルとして使用
            rule_name = text if text else f"ルール生成 {now}" # 空文字の場合はデフォルト名
            logger.warning(f"Using raw text or default as title: {rule_name}")


        # --- ルールオブジェクト作成・保存 ---
        rule_obj = {
            "title": rule_name,
            "prompt": rule_prompt,
            "json_format_example": json_format_example,
            "sample_data": sample_data,
            "mode": mode  # モード情報を追加
        }
        # 新規ID付与
        existing_ids = [r.get("id", -1) for r in self._rules]
        new_id = max(existing_ids) + 1 if existing_ids else 0
        rule_obj["id"] = new_id
        logger.info(f"Assigned id={new_id} to new rule '{rule_name}' with mode={mode}")
        # ローカルファイルに保存
        self._rules.append(rule_obj)
        self._save_rules()
        logger.info(f"Rule id={new_id} ('{rule_name}') created and saved with mode={mode}.")

        # 戻り値用メタデータ
        metadata = rule_obj.copy()
        metadata['rule_name'] = rule_name
        return metadata

    def regenerate_rule(self, rule_id: int, samples: List[Dict[str, Any]], mode: str = None) -> Dict[str, Any]:
        """
        既存ルールを再生成し、更新する
        """
        # 指定ルールを検索
        updated_idx = -1
        old_mode = ProcessMode.NORMAL  # デフォルト値
        for idx, r in enumerate(self._rules):
            if r.get("id") == rule_id:
                updated_idx = idx
                old_mode = r.get("mode", ProcessMode.NORMAL)  # 既存のモードを保持
                break
        if updated_idx == -1:
            raise GeminiAPIError(f"ルール id={rule_id} が見つかりません")

        # モードが指定されていない場合は既存のモードを使用
        if mode is None:
            mode = old_mode

        # 追加: regenerate_rule開始時のデバッグログ
        logger.debug(f"Starting regenerate_rule: rule_id={rule_id}, updated_idx={updated_idx}, current_ids={[r.get('id') for r in self._rules]}")
        logger.info(f"Regenerating rule id={rule_id} with mode={mode}...")
        # 新しいサンプルデータでルールを作成 (create_ruleを呼び出す)
        try:
            new_rule_metadata = self.create_rule(samples, mode)
            # 追加: create_rule後のデバッグログ
            logger.debug(f"After create_rule: metadata returned={new_rule_metadata}")
            logger.debug(f"Current rule IDs after create: {[r.get('id') for r in self._rules]}")

            if 0 <= updated_idx < len(self._rules) -1: # 末尾に追加されたので、それより前にあるはず
                 # 追加: 古いルール削除前のデバッグログ
                 logger.debug(f"Deleting old rule at index={updated_idx}, id={rule_id}")
                 del self._rules[updated_idx]
                 # 追加: 古いルール削除後のデバッグログ
                 logger.debug(f"Rule IDs after deletion: {[r.get('id') for r in self._rules]}")
                 self._save_rules()  # 削除後に再度保存
                 logger.info(f"Old rule id={rule_id} removed after regeneration.")
                 return new_rule_metadata  # 新しいルールのメタデータを返す
            else:
                 # 追加: 想定外パス時のデバッグログ
                 logger.warning(f"Could not delete old rule id={rule_id}, unexpected updated_idx={updated_idx} with current length={len(self._rules)}")
                 logger.debug(f"Rules remain unchanged: {[r.get('id') for r in self._rules]}")
                 self._save_rules()  # 念のため保存
                 return new_rule_metadata

        except Exception as e:
            logger.error(f"Error regenerating rule id={rule_id}: {e}")
            # 再生成に失敗した場合、元のルールはそのまま残る
            raise GeminiAPIError(f"ルール id={rule_id} の再生成に失敗しました: {e}")


    def get_rules(self, mode: str = None) -> List[Dict[str, Any]]:
        """
        保存済みルールのメタ情報リストを返却
        引数 mode: 指定されている場合は、そのモードのルールのみを返却
        """
        # ローカルファイルから最新の状態を読み込む（他のプロセスによる変更を反映するため）
        # self._load_rules()
        # ↑UIから頻繁に呼ばれる可能性があるため、毎回ロードするのは効率が悪い。
        # 保存時に同期が取れている前提とする。必要であればUI側でリフレッシュを促す。
        
        if mode is None:
            return self._rules
        else:
            # 指定されたモードのルールのみを返却
            filtered_rules = [rule for rule in self._rules if rule.get("mode", ProcessMode.NORMAL) == mode]
            logger.debug(f"Filtered rules for mode={mode}: {len(filtered_rules)} out of {len(self._rules)} total rules")
            return filtered_rules

    def delete_rule(self, rule_id: int) -> bool:
        """
        指定したrule_idのルールを削除する
        成功時にTrue、失敗時にFalseを返却
        """
        initial_length = len(self._rules)
        self._rules = [r for r in self._rules if r.get("id") != rule_id]
        if len(self._rules) < initial_length:
            self._save_rules()
            logger.info(f"Rule id={rule_id} deleted successfully.")
            return True
        else:
            logger.warning(f"削除対象のルール id={rule_id} が見つかりませんでした")
            return False


    def apply_rule(self, rule_id: int, inputs: List[str]) -> List[Dict[str, Any]]:
        """
        指定したルールを入力リストに適用し、結果を返却
        (注: 現在の実装はサンプルデータとの完全一致のみ。将来的にはAI適用が必要)
        """
        # ルールを検索
        rule = next((r for r in self._rules if r.get("id") == rule_id), None)
        if not rule:
            raise GeminiAPIError(f"ルール id={rule_id} が見つかりません")

        sample_data = rule.get('sample_data', {})
        headers = sample_data.get('headers', [])
        rows = sample_data.get('rows', [])
        results = []
        rule_mode = rule.get('mode', ProcessMode.NORMAL)  # ルールのモードを取得

        if not headers or not rows:
             logger.warning(f"Rule id={rule_id} has empty sample_data. Cannot apply rule based on samples.")
             # サンプルがない場合、全入力に対してエラーを返す
             return [{"input": inp, "output": {}, "status": "error", "error_msg": "ルールにサンプルデータがありません"} for inp in inputs]

        # 出力ヘッダーのインデックスを取得 (3列目以降)
        output_indices = [idx for idx, h in enumerate(headers, start=1) if idx >= 3 and h.strip()]
        output_headers = [headers[i-1] for i in output_indices]
        # ログ: 処理開始
        logger.info(f"apply_rule 開始: rule_id={rule_id} mode={rule_mode} 対象行数={len(inputs)}件")

        logger.info(f"Applying rule id={rule_id} based on sample matching...")
        for inp in inputs:
            # マッチするサンプル行を検索 (2列目が入力値と一致するか)
            match = next((row for row in rows if len(row) > 1 and row[1] == inp), None)
            if match:
                try:
                    # 出力フィールド生成
                    out = {}
                    for idx, key in zip(output_indices, output_headers):
                         if idx -1 < len(match): # 行の長さチェック
                             out[key] = match[idx - 1]
                         else:
                             logger.warning(f"Index {idx-1} out of bounds for matched row in rule id={rule_id} for input '{inp}'. Header: '{key}'")
                             out[key] = "" # インデックス外の場合は空文字

                    results.append({"input": inp, "output": out, "status": "success"})
                    logger.debug(f"Input '{inp}' matched sample. Output: {out}")
                except Exception as e:
                     logger.error(f"Error processing matched row for input '{inp}' in rule id={rule_id}: {e}")
                     results.append({"input": inp, "output": {}, "status": "error", "error_msg": f"サンプル処理中にエラー発生: {e}"})

            else:
                logger.debug(f"Input '{inp}' did not match any sample in rule id={rule_id}, calling AI.")
                # サンプル一致しない場合はAIを呼び出して処理
                try:
                    # モードに応じて処理方法を変更
                    if rule_mode == ProcessMode.IMAGE or rule_mode == ProcessMode.VIDEO:
                        # 画像・動画の場合はメディア解析APIを使用
                        logger.info(f"Processing {rule_mode} file: {inp}")
                        
                        # ファイルパスの検証
                        file_path = Path(inp)
                        if not file_path.exists():
                            raise FileNotFoundError(f"ファイルが見つかりません: {inp}")
                        
                        # プロンプトの組み立て
                        media_prompt = f"{rule.get('prompt', '')}\n\n以下の項目について回答してください:\n"
                        for header in output_headers:
                            media_prompt += f"- {header}\n"
                        media_prompt += f"\n回答は以下のJSONフォーマットで返してください:\n"
                        media_prompt += json.dumps(rule.get("json_format_example", {}), ensure_ascii=False, indent=2)
                        
                        # 画像・動画解析APIを呼び出し
                        logger.debug(f"メディア解析プロンプト:\n{media_prompt}")
                        if rule_mode == ProcessMode.IMAGE:
                            ai_response = self.gemini.analyze_image(inp, media_prompt)
                        else:  # VIDEO
                            ai_response = self.gemini.analyze_video(inp, media_prompt)
                        
                        # レスポンスをJSON解析
                        text = ai_response.strip()
                        # コードブロックマーカー除去
                        if text.startswith("```"):
                            text = re.sub(r"```(?:json)?\n?", "", text)
                            text = text.rstrip("`\n ")
                        # JSON部分抽出
                        start = text.find("{")
                        end = text.rfind("}")
                        json_str = text[start:end+1] if start != -1 and end != -1 else text
                        data = json.loads(json_str)
                        out = {key: data.get(key, "") for key in output_headers}
                        
                        results.append({"input": inp, "output": out, "status": "success"})
                        logger.debug(f"Media analysis output for input '{inp}': {out}")
                        
                    else:
                        # テキストモードの場合は従来の処理
                        # プロンプトの組み立て
                        lines = [
                            rule.get("prompt", ""),
                            "次のようなJSONフォーマットで返答してください。",
                            json.dumps(rule.get("json_format_example", {}), ensure_ascii=False, indent=2),
                            f"元の値: {inp}"
                        ]
                        combined_prompt = "\n".join(lines)
                        # 送信プロンプトをログに出力
                        logger.debug(f"送信プロンプト内容:\n{combined_prompt}")
                        logger.info(f"リアルデータ変換用モデル: {self.gemini.minutes_model} を使用してAI呼び出しを実行")
                        resp = self.gemini.client.models.generate_content(
                            model=self.gemini.minutes_model,
                            contents=combined_prompt
                        )
                        text = resp.text.strip()
                        # コードブロックマーカー除去
                        if text.startswith("```"):
                            text = re.sub(r"```(?:json)?\n?", "", text)
                            text = text.rstrip("`\n ")
                        # JSON部分抽出
                        start = text.find("{")
                        end = text.rfind("}")
                        json_str = text[start:end+1] if start != -1 and end != -1 else text
                        data = json.loads(json_str)
                        out = {key: data.get(key, "") for key in output_headers}
                        results.append({"input": inp, "output": out, "status": "success"})
                        logger.debug(f"AI output for input '{inp}': {out}")
                        
                except Exception as e:
                    logger.error(f"AI処理エラー for input '{inp}': {e}")
                    results.append({"input": inp, "output": {}, "status": "error", "error_msg": str(e)})

        # ログ: 処理完了
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = len(results) - success_count
        logger.info(f"apply_rule 完了: success={success_count}件 error={error_count}件")
        return results

    def update_rule(self, rule_id: int, new_data: Dict[str, Any]) -> bool:
        """既存ルールのtitle、prompt、modeを更新し保存する"""
        logger.info(f"Updating rule id={rule_id} with data={new_data}")
        for r in self._rules:
            if r.get("id") == rule_id:
                r["title"] = new_data.get("title", r["title"])
                r["prompt"] = new_data.get("prompt", r["prompt"])
                if "mode" in new_data:
                    r["mode"] = new_data["mode"]
                    logger.info(f"Rule id={rule_id} mode updated to {new_data['mode']}")
                self._save_rules()
                logger.info(f"Rule id={rule_id} updated successfully.")
                return True
        logger.warning(f"Rule id={rule_id} not found for update.")
        return False 