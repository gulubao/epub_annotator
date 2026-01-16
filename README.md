# EPUB Annotator

自动为 EPUB 电子书中的生僻英文词汇添加中文注释。

## 原理

1. **词频分析**: 使用 [wordfreq](https://github.com/rspeer/wordfreq) 基于 Zipf 频率标度识别低频词汇
2. **词典查询**: 通过 [ECDICT](https://github.com/skywind3000/ECDICT) (340万词条) 获取中文释义
3. **HTML注入**: 使用 BeautifulSoup 解析 EPUB，在难词后插入注释标签

## 安装

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 下载词典 (812MB)
mkdir -p data
curl -L -o data/ecdict.zip https://github.com/skywind3000/ECDICT/releases/download/1.0.28/ecdict-sqlite-28.zip
unzip data/ecdict.zip -d data && rm data/ecdict.zip
```

## 使用

```bash
python main.py input.epub                # 输出: input_annotated.epub
python main.py input.epub -o output.epub # 指定输出
python main.py input.epub -t 3.5         # 调整阈值
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-o` | `{stem}_annotated.epub` | 输出路径 |
| `-t` | `4.0` | Zipf阈值 (4.0≈前1万词, 3.0≈前3万词) |
| `-d` | `data/stardict.db` | 词典路径 |

## 结构

```
src/
├── annotator.py    # HTML解析与注释注入
├── dictionary.py   # 词典接口 (ECDictSqlite)
├── difficulty.py   # Zipf词频评估
└── epub_handler.py # EPUB读写
```

## 扩展词典

```python
from src.dictionary import BaseDictionary

class CustomDict(BaseDictionary):
    def lookup(self, word: str) -> str | None:
        ...
```

## 依赖

- EbookLib, BeautifulSoup4, wordfreq, lxml
- [ECDICT](https://github.com/skywind3000/ECDICT) (MIT)
