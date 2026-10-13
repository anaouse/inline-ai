import os
import sys
import threading
import time
import uuid
from pathlib import Path

import pyperclip
from anthropic import Anthropic
from dotenv import load_dotenv
from pynput import keyboard

try:
    import pystray
except ImportError:  # 终端模式下没有 pystray 也能运行
    pystray = None

from inline_ai.icon import make_icon


SYSTEM_PROMPT = """你正在与用户一起写作。用户消息是正在编辑的全文，<caret> 标记当前文本光标的位置。
光标紧邻的前方有一个 ~，从 ~ 到光标之间是用户给你的指令，不是正文，光标后方是光标之后已有的正文。
请结合光标前后的上下文执行这个指令。你的回答会直接替换从 ~ 到光标之间的整段内容。
只输出需要插入的正文，不要解释、开场白或额外的包裹标记，除非指令要求这些内容。
不要重复周围已有的正文，不要输出 <caret>、~ 或指令本身。直接给出用户需要的内容。"""


def log(message: str):
    print(message, flush=True)


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def show_error(message: str):
    log(message)
    if not getattr(sys, "frozen", False):
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "Inline AI", 0x10)
    except Exception:
        pass


class InlineAI:
    def __init__(self, client: Anthropic):
        self.client = client
        self.controller = keyboard.Controller()
        self.stopping = threading.Event()
        self.busy = threading.Lock()
        self.pressed = set()
        self.pending = False
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.icon = None

    @staticmethod
    def is_alt(key):
        return key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r)

    @staticmethod
    def is_backslash(key):
        return getattr(key, "char", None) == "\\" or getattr(key, "vk", None) == 220

    def on_press(self, key):
        self.pressed.add(key)
        if self.is_backslash(key) and any(self.is_alt(k) for k in self.pressed):
            if not self.busy.locked():
                self.pending = True

    def on_release(self, key):
        self.pressed.discard(key)
        # 等快捷键完全松开，避免 Alt 干扰接下来模拟的按键。
        if self.pending and not any(
            self.is_alt(k) or self.is_backslash(k) for k in self.pressed
        ):
            self.pending = False
            if self.busy.acquire(blocking=False):
                threading.Thread(target=self.run_task, daemon=True).start()

    def shortcut(self, key, shift=False):
        with self.controller.pressed(keyboard.Key.ctrl):
            if shift:
                with self.controller.pressed(keyboard.Key.shift):
                    self.controller.tap(key)
            else:
                self.controller.tap(key)
        time.sleep(0.08)

    def copy_selection(self):
        # 空选区通常不会更新剪贴板，用标记区分空文本和上次复制的内容。
        marker = f"inline-ai-{uuid.uuid4()}"
        pyperclip.copy(marker)
        self.shortcut("c")
        deadline = time.monotonic() + 0.6
        while time.monotonic() < deadline:
            text = pyperclip.paste()
            if text != marker:
                return text.replace("\r\n", "\n")
            time.sleep(0.02)
        return ""

    def get_context(self):
        self.shortcut(keyboard.Key.home, shift=True)
        before = self.copy_selection()
        if before:
            self.controller.tap(keyboard.Key.right)
            time.sleep(0.08)

        self.shortcut(keyboard.Key.end, shift=True)
        after = self.copy_selection()
        if after:
            self.controller.tap(keyboard.Key.left)
            time.sleep(0.08)
        return before, after

    def notify(self, message: str):
        if self.icon is not None:
            try:
                self.icon.notify(message, "Inline AI")
            except Exception:
                pass

    def run_task(self):
        try:
            if self.stopping.is_set():
                return
            before, after = self.get_context()
            start = before.rfind("~")
            if start == -1 or not before[start + 1 :].strip():
                self.notify("光标前需要有一个 ~，其到光标之间的 prompt 不能为空。")
                log("光标前需要有一个 ~，其到光标之间的 prompt 不能为空，本次未修改文本。")
                return

            prompt_length = len(before) - start
            log("正在请求 AI，请保持当前窗口和光标不动……")
            response = self.client.messages.create(
                model="deepseek-flash",
                max_tokens=12800,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": before + "<caret>" + after}],
            )
            answer = "".join(
                block.text for block in response.content if block.type == "text"
            )
            if self.stopping.is_set():
                return
            if response.stop_reason == "max_tokens":
                self.notify("回答超过长度限制，本次未修改文本。")
                log("回答超过长度限制，本次未修改文本。")
                return
            if not answer.strip():
                self.notify("AI 未返回正文，本次未修改文本。")
                log("AI 未返回正文，本次未修改文本。")
                return

            pyperclip.copy(answer)
            for _ in range(prompt_length):
                if self.stopping.is_set():
                    return
                self.controller.tap(keyboard.Key.backspace)
            self.shortcut("v")
            log("已替换 prompt。")
        except Exception as exc:
            self.notify(f"执行失败：{exc}")
            log(f"执行失败：{exc}")
        finally:
            self.busy.release()

    def shutdown(self):
        self.stopping.set()
        self.listener.stop()
        self.client.close()

    def build_tray(self):
        if pystray is None:
            return None
        menu = pystray.Menu(pystray.MenuItem("退出", self.on_quit))
        self.icon = pystray.Icon(
            "inline-ai", make_icon(64), "Inline AI（Alt+\\ 生成）", menu
        )
        return self.icon

    def on_quit(self, icon, item):
        self.shutdown()
        icon.stop()

    def run(self, with_tray: bool):
        self.listener.start()
        if with_tray:
            icon = self.build_tray()
            if icon is None:
                show_error("缺少 pystray，无法启动托盘。")
                self.shutdown()
                return
            try:
                icon.run()
            finally:
                self.shutdown()
            return

        log("Inline AI 已启动：Alt+\\ 生成并替换，终端 Ctrl+C 退出。")
        try:
            while self.listener.is_alive():
                self.listener.join(timeout=0.5)
        except KeyboardInterrupt:
            log("\n正在退出。")
        finally:
            self.shutdown()


def main():
    load_dotenv(base_dir() / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_ANTHROPIC_BASE_URL")
    if not api_key or not base_url:
        show_error("请在 .env 中设置 DEEPSEEK_API_KEY 和 DEEPSEEK_ANTHROPIC_BASE_URL。")
        return

    client = Anthropic(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=0,
    )
    app = InlineAI(client)
    with_tray = getattr(sys, "frozen", False) or "--tray" in sys.argv
    if with_tray and pystray is None:
        show_error("缺少 pystray，无法启动托盘模式。")
        client.close()
        return
    app.run(with_tray)


if __name__ == "__main__":
    main()
