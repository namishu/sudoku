<h1 align="center">Namishu Sudoku</h1>

<p align="center">打印几道数独，留一段安静思考的时间。</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="Python 3.10+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22A06B?style=flat" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/PDF-A4_portrait-E05D44?style=flat" alt="PDF：A4 纵向">
</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

<p align="center">
  <a href="examples/sudoku.pdf"><img src="examples/sudoku.png" alt="一道简单数独，格内留有手写空间" width="440"></a>
</p>

Namishu Sudoku 是一个生成可打印数独的命令行小工具。选择难度和页数，
就能得到排版完成的 A4 PDF，默认每页两道题，格内留有清晰的手写空间。
你可以用它准备课堂练习、安排家里的数独活动，或打印几页带在路上慢慢解。

不必四处寻找题目、截图拼版或手动整理答案，需要时就能生成一份新的练习。
每道题都经过唯一解检查。想在做完后核对，只需开启答案模式：每页上方是一道题，
下方是它的完整答案。

<p align="center">
  示例 PDF 文件：<a href="examples/sudoku.pdf">双题练习版</a> · <a href="examples/sudoku-answers.pdf">解答对照版</a>
</p>

## 安装

需要 **Python 3.10+**。使用 uv 或 pip 安装：

```bash
uv tool install namishu-sudoku
```

```bash
python -m pip install namishu-sudoku
```

两种方式都会提供 `namishu-sudoku` 命令。默认版式和 Rubik Regular、Medium 字体随安装包提供，
无需额外安装字体。

## 快速开始

生成**一页、两道 easy 难度的题目**，保存为 `sudoku.pdf`：

```bash
namishu-sudoku
```

生成五页较难的练习，共十道题：

```bash
namishu-sudoku --level hard --pages 5
```

让每道题的答案出现在同页下方。以下命令生成五页，共五道题及其答案：

```bash
namishu-sudoku --level hard --pages 5 --answers
```

指定输出路径，并使用随机种子复现题目内容：

```bash
namishu-sudoku --level normal --seed 42 -o exercises/practice.pdf
```

生成完成后，命令会显示文件保存位置和页数。相对路径以当前工作目录为准，
不存在的上级目录会自动创建。新文档写入成功后，会替换输出路径上已有的 PDF。
也可以通过 `python -m namishu_sudoku` 运行。

使用 A4 纸按实际大小打印。沿中间分隔线折起纸张，就能暂时遮住答案。

## 命令行选项

| 选项 | 用途 | 默认值 |
|---|---|---|
| `--level LEVEL` | `easy` 简单、`normal` 普通、`hard` 困难 | `easy` |
| `--pages N` | PDF 页数，必须为正整数 | `1` |
| `--answers` | 在每页下方显示上方题目的答案 | 关闭 |
| `-o, --output PATH` | PDF 保存路径 | `sudoku.pdf` |
| `--seed INTEGER` | 在相同设置和版本下复现题目内容 | 随机 |
| `--config PATH` | 用于覆盖版式或字体设置的 YAML 文件 | 内置设置 |
| `--help` | 显示使用说明 | |
| `--version` | 显示已安装的版本 | |

默认不生成答案，每页两道题。开启答案模式后，每页一道题及其答案，题面数字使用柔和的灰蓝色粗体；答案中原题数字淡化，补入数字使用柔和的青绿色细体。
随机种子用于在相同版本和设置下复现题目，不保证 PDF 文件字节完全相同。

## 选择难度

提供简单、普通、困难三档。每道题都有唯一解，并能通过对应档位允许的逻辑技巧解出，无需猜测：

| 难度 | 解题技巧 |
|---|---|
| `easy` 简单 | 某格只有一个候选数字，或某个数字在行、列、宫内只有一个可填位置 |
| `normal` 普通 | 简单技巧，加宫与行列之间的候选排除（锁定候选数）、显性数对 |
| `hard` 困难 | 普通技巧，加隐性数对、显性三数组、X-Wing（矩形候选排除） |

普通题必须让简单档的解题流程停滞，困难题必须让普通档的流程停滞。
评级依据本工具固定的技巧顺序，可能与其他数独应用不同。提示数字数量会变化，不用于决定难度。
困难题可能需要更多生成时间；若在有限尝试内找不到符合等级的题目，程序会报错并保留已有 PDF，
不会自动换成更简单的题。

## 自定义版式

只需填写想要修改的设置。例如，将以下内容保存为 `sudoku.yaml`，
即可缩小数字：

```yaml
numbers:
  font_size: 22
```

```bash
namishu-sudoku --config sudoku.yaml
```

未指定的设置保留默认值，包括内置字体。
[完整示例配置](https://github.com/namishu/sudoku/blob/main/examples/sudoku.yaml) 列出了全部设置，下载后即可使用。

| 设置 | 修改方式 |
|---|---|
| 纸张与边距 | `page`：页面宽高和统一边距（`margin`） |
| 棋盘 | `board`：宽度、两个棋盘之间的垂直间距（`gap`）和线条颜色 |
| 数字 | `numbers`：字号、题面数字颜色（`color`）、答案中原题数字颜色（`answer_given_color`）和补入答案颜色（`answer_color`） |
| 中间虚线 | `separator`：是否显示和颜色 |
| 自定义字体 | `font`：补入答案的字体；`bold_font`：已知数字的字体，均为 TrueType 文件路径 |

除字号使用磅外，距离和尺寸均使用毫米。`page.margin` 统一控制四边边距。棋盘线宽和分隔线的虚线样式固定。`board.gap` 默认 30 毫米，从两个棋盘边框的外沿计算。两个棋盘在页面可用区域内上下对称排列并水平居中，不显示侧边信息或页脚。
十六进制颜色需加引号，例如 `"#1f2c50"`。
未知配置项、无效数值或无法容纳内容的版式，会在替换已有 PDF 前报错。

使用自定义字体时，在 YAML 中添加 `font: fonts/MyFont-Regular.ttf` 和
`bold_font: fonts/MyFont-Medium.ttf`，分别指定常规和中等字重字体。路径相对于 YAML 文件所在目录，
也可以使用绝对路径；未指定的字体继续使用内置版本。字体会嵌入 PDF，接收文件的人无需安装。
字体无法读取或缺少数字字形时，程序会报错。
原题给定数字在题面和答案中都使用粗体；只有原本空白的单元格中补入的数字使用细体和答案颜色。

## 许可证

代码和原创文档采用 [MIT 许可证](https://github.com/namishu/sudoku/blob/main/LICENSE)。内置 Rubik Regular、Medium 字体采用
[SIL Open Font License 1.1](https://github.com/namishu/sudoku/blob/main/src/namishu_sudoku/data/OFL.txt)，同一文件中记录了字体的版权归属和来源信息。
生成的数独可以打印、分享、修改和销售。
