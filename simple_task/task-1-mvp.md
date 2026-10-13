---
created_at: 2026-10-13T19:06:36+08:00
status: done # done | todo
---

> 人下达task，你执行task并记录执行过程，人验收后记录验收看到的东西判断是否完成，你继续执行task，直到人认为结束了再手动修改status

# 说明

我这个项目的思路是在输入的时候可以直接在打字的地方快速输入prompt询问ai，然后通过剪贴板获取答案后进行修改

例子

```
本文为英语的基础教学内容

# greeting

~给出一段打招呼的对话，对话者为A与B~<caret>
```

我在~~内部写的内容就是prompt内容然后鼠标停在文末，然后我使用快捷键`alt+\`，假设这之后用户不进行任何切屏或者移动鼠标的操作，用户静止不动，这时候程序自动使用键盘`ctrl+shift+home`获取鼠标前的内容以及`ctrl+shift+end`获取鼠标后的内容作为上下文内容，发送给ai要求获得回答。并且补充`<caret>`说明目前鼠标的位置。然后写入的方法是：计算目前鼠标所在位置（一般都是在~~这个prompt的后方。）前的~~内的内容有多少字符，执行对应的backspace删除掉prompt内容和~~这个包裹符号，然后在ctrl+v粘贴替换内容。这个过程就结束了

ai的system prompt要知道鼠标附近的~~内部是prompt内容，然后回答的时候他要知道是和用户一起写作的，辅助用户写内容，所以不要有额外的解释，不用顾虑太多，快速结合上下文给出用户需要的内容即可

- 使用dotenv加载.env内的DEEPSEEK_API_KEY和DEEPSEEK_ANTHROPIC_BASE_URL，不要看里面的内容，内容格式你可以看.env.example
- 使用anthropic的sdk
- 使用pyperclip处理剪贴板（先不用保存原始的剪贴板的内容，直接替换就好）
- 使用pynput模拟按键
- 模型名称是deepseek-flash
- 先假设鼠标一定位于`~prompt~`内容的后面来实现删除prompt
- 确保anthropic的客户端一直存在，不要每次提问就初始化一次，那样太慢
- system promt先写死
- 我已经加好了需要的库
- 实现后确保没有语法错误即可，我自己运行进行测试，搞一个ctrl+c的时候退出软件

## 执行记录

### MVP 实现（2026-10-13）

- 已实现 `src/inline_ai/main.py`：监听 `Alt+\`，等待快捷键松开后获取光标前后上下文。
- 使用 `Ctrl+Shift+Home/End` 选区和剪贴板获取文本，恢复文本光标，并插入 `<caret>` 标记发送给 AI。
- 从项目 `.env` 加载配置；实现期间未查看 `.env` 内容。
- 启动时创建常驻 Anthropic 客户端，使用 `deepseek-flash` 和固定 system prompt。
- 回答成功后按 `~prompt~` 的字符数退格删除，再通过剪贴板粘贴回答；忙碌时忽略重复触发。
- 支持在终端按 `Ctrl+C` 退出。请求失败、回答为空或达到输出长度限制时不替换文本。
- 已补充 README，启动命令为 `uv run inline-ai`。
- 已运行 `uv run --no-sync python -m py_compile src/inline_ai/main.py src/inline_ai/__init__.py`，语法检查通过。
- 未执行真实 API 请求或键盘操作测试，等待用户运行验收。任务状态保持 `todo`。

### 检测规则改为单个 ~ 开头（2026-10-13）

- 按输入逻辑调整：只写 `~` 开头，光标位置当作闭合标记，不再要求尾部 `~`。
- 识别规则改为取光标前最后一个 `~`，其到光标之间的内容作为 prompt。
- 删除字符数改为光标前最后一个 `~` 到光标的长度，连同 `~` 一起删除。
- system prompt 同步更新：`<caret>` 前的最后一个 `~` 之后为指令。
- README 已同步。语法检查通过，等待用户运行验收，状态保持 `todo`。

### 支持 exe 与托盘（2026-10-13）

- 新增 `build.sh`，用 pyinstaller 打包 `--onefile --windowed` 的 `dist/inline-ai.exe`。
- 新增 `src/inline_ai/icon.py`，用 Pillow 生成图标，托盘和 exe 图标共用，不依赖外部图片文件。
- 新增托盘模式：`--tray` 参数或无控制台 exe 运行时启用，右键托盘图标选“退出”关闭程序。
- 终端模式保持原样，`Ctrl+C` 退出。
- `.env` 查找位置：源码运行取项目根目录，exe 运行取 exe 所在目录。
- 打包命令：`bash build.sh`。语法检查通过，未执行打包和实际运行测试，状态保持 `todo`。

### 修复打包图标路径（2026-10-13）

- 报错原因：`--specpath` 让 spec 文件落在 `build/`，pyinstaller 按 spec 目录解析图标路径，`build/inline-ai.ico` 被拼成 `build/build/inline-ai.ico`。
- 修复：`build.sh` 里用 `cygpath -w` 把图标路径转成绝对 Windows 路径再传给 `--icon`。
- 已实际运行 `bash build.sh`，打包成功，产物 `dist/inline-ai.exe`（约 24 MB）。
- 运行时验证：从终端启动 exe，能弹出缺少 `.env` 的错误提示窗口，说明无控制台入口和报错路径正常。已结束测试进程。托盘和快捷键行为仍等用户验收，状态保持 `todo`。

### 图标透明背景与输出长度上限（2026-10-13）

- 图标背景由深色 `(30,30,30,255)` 改为全透明 `(0,0,0,0)`，圆形以外不再出现黑色方块。
- `max_tokens` 由 4096 改为 12800，README 同步。
- 已确认图标四角 alpha 为 0，语法检查通过。需要重新打包 exe 才能看到新图标。
