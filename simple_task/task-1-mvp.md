---
created_at: 2026-10-13T19:06:36+08:00
status: todo # done | todo
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
