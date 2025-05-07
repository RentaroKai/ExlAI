import json

def main():
    path = 'app/ui/history_rules.json'
    # JSONファイル読み込み
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # idの重複を除去（先に出現したエントリを優先）
    seen = set()
    result = []
    for item in data:
        if item.get('id') not in seen:
            seen.add(item.get('id'))
            result.append(item)
        else:
            print(f"[LOG] 重複検知: id={item.get('id')} のエントリをスキップしました。")

    # ファイル書き戻し
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[LOG] history_rules.json の重複を削除しました。総エントリ: {len(data)} → {len(result)}")

if __name__ == '__main__':
    main() 