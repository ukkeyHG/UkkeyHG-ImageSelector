# UkkeyHG-ImageSelector

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](#ライセンス)

幅判定 + 3-way (Image+Mask) 選択 ComfyUI カスタムノード。

reference image の幅を見て、3つの調整済み (Image + Mask) ペアから1つを選んで後段に流します。

## 解決する問題

例: Gemini で生成された画像が3パターンのいずれかのサイズになるケース:
- **1376×768**（16:9 標準）
- **1264×840**（3:2 寄り）
- **2752×1536**（16:9 高解像度）

LTX2 ネイティブの **1280×704** にしたい場合、サイズごとに **異なるスケール係数 + 異なるパディング量** が必要。3つの調整ワークフローを並列で実行しておき、reference image の幅で選ぶのが綺麗な解決策です。

## 配線図

```
Load Image ─┬─→ [調整1: scale + outpaint] ─→ Image+Mask ┐
            ├─→ [調整2: scale + outpaint] ─→ Image+Mask ─┤
            ├─→ [調整3: scale + outpaint] ─→ Image+Mask ┤
            │                                            ↓
            └────────reference_image─────→ [UkkeyHG-ImageSelector]
                                                  │
                                                  ↓
                                            Image, MASK
                                                  ↓
                                            [VAE Encode (for Inpainting)]
                                                  ↓
                                                  …
```

## ノード仕様

### 入力

| ピン名 | 型 | 説明 |
|---|---|---|
| `reference_image` | IMAGE | 幅判定に使う元画像（通常 Load Image の直接出力） |
| `image_a` / `mask_a` | IMAGE / MASK | 調整1 の出力（width_a に一致するとき選ばれる） |
| `width_a` | INT | デフォルト `1376`（1376×768 ペア） |
| `image_b` / `mask_b` | IMAGE / MASK | 調整2 の出力 |
| `width_b` | INT | デフォルト `1264`（1264×840 ペア） |
| `image_c` / `mask_c` | IMAGE / MASK | 調整3 の出力 |
| `width_c` | INT | デフォルト `2752`（2752×1536 ペア） |
| `tolerance` | INT | 幅一致の許容誤差（デフォルト 8 px）。Gemini の出力揺れを吸収 |

### 出力

| ピン名 | 型 | 説明 |
|---|---|---|
| `image` | IMAGE | 選択された (image, mask) ペアの IMAGE |
| `mask` | MASK | 同じく MASK |
| `selected_branch` | STRING | デバッグ用: どのブランチが選ばれたか + 数値情報 |

### 動作仕様

1. `reference_image` の shape (B, H, W, C) から W を取得
2. width_a/b/c それぞれと比較 → tolerance 以内なら採用
3. 全部マッチしなかった場合は **最も近いもの**を fallback として採用 + コンソールに警告
4. 採用した IMAGE / MASK と "Branch A/B/C" のラベル文字列を出力

## インストール

```
ComfyUI/
└── custom_nodes/
    └── UkkeyHG-ImageSelector/   ← このフォルダごとコピー
        ├── __init__.py
        ├── nodes.py
        └── README.md
```

ComfyUI を再起動 → 右クリック → **Add Node** → **UkkeyHG** > **Image Selector (3-way by width)** で配置可能。

## 使い方（ワークフロー組み立て例）

1. **Load Image** ノード配置
2. 出力 IMAGE を3経路に複製し、それぞれの **調整ワークフロー（調整1/2/3）** に接続
   - 調整1: 1376×768 用のスケール + パディング + outpaint
   - 調整2: 1264×840 用のスケール + パディング + outpaint
   - 調整3: 2752×1536 用のスケール + パディング + outpaint
3. **UkkeyHG-ImageSelector** 配置
4. 各入力を接続:
   - `reference_image` ← Load Image の IMAGE 出力（**調整後ではなく原画**）
   - `image_a` / `mask_a` ← 調整1 の出力
   - `image_b` / `mask_b` ← 調整2 の出力
   - `image_c` / `mask_c` ← 調整3 の出力
5. width_a/b/c は通常デフォルト（1376/1264/2752）のままでOK
6. 出力 IMAGE と MASK を **VAE Encode (for Inpainting)** に接続
7. 後段の inpaint KSampler / VAE Decode へ続ける

`selected_branch` 出力は **Show Text** ノードに繋ぐと、どのブランチが採用されたかリアルタイムで確認できてデバッグに便利です。

## 依存

- ComfyUI 本体のみ（追加 pip パッケージ不要）
- Python 3.8+
- torch（ComfyUI が既に依存しているもの）

## ライセンス

MIT（自由に改変・再配布OK）

## カスタマイズ

- **width_a/b/c の数値**: ノードの widget で直接変更可能。Gemini の出力サイズが変わった場合はここを書き換えるだけで対応
- **3パターンより多い場合**: `nodes.py` の `UkkeyHGImageSelector` クラスをコピーして `UkkeyHGImageSelector4Way` のような4分岐版を作るのが楽（candidates リストに項目を追加するだけ）
- **アスペクト比で判定したい場合**: `select` メソッドで `ref_aspect = ref_width / ref_height` を計算して比較に使う

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| ノードが ComfyUI に出てこない | フォルダ配置ミス | `ComfyUI/custom_nodes/UkkeyHG-ImageSelector/` 直下に `__init__.py` があるか確認 |
| `WARNING: no width match within tolerance` がコンソールに出る | reference image が想定外サイズ | tolerance を増やすか、width_a/b/c のいずれかを実際の値に変更 |
| 常に Branch A が選ばれる | reference_image が間違ってる | Load Image の **Image 出力**を直接 reference_image に接続しているか確認（調整後の IMAGE ではダメ） |
| Image だけ出て Mask が空になる | 調整1/2/3 の出力 mask 接続漏れ | 各調整ワークフローに mask を生成するノード（例: ImagePadForOutpaint）が含まれてるか確認 |

