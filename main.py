import tkinter as tk
from tkinter import ttk
import requests
import re
import time
import hashlib
import threading

class AnkiQuickCard:
    def __init__(self, root):
        self.root = root
        self.root.title("Anki Connect卡片推送工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 全局变量
        self.deck_names = []
        self.cards = []
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题/说明区
        self.create_title_section()
        
        # 配置区
        self.create_config_section()
        
        # 文本区（左侧原始文本，右侧预览）
        self.create_text_sections()
        
        # 功能按钮区
        self.create_button_section()
        
        # 状态提示区
        self.create_status_section()
        
        # 初始化时获取牌组列表
        self.get_deck_names()
    
    def create_title_section(self):
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Anki Connect卡片推送工具", font=('SimHei', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        hint_label = ttk.Label(title_frame, text="需先启动Anki并加载Anki Connect", foreground="blue")
        hint_label.pack(side=tk.RIGHT)
    
    def create_config_section(self):
        config_frame = ttk.LabelFrame(self.main_frame, text="配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 标签输入框
        ttk.Label(config_frame, text="标签：").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.tag_entry = ttk.Entry(config_frame, width=30)
        self.tag_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        # 取消默认标签
        
        # 牌组下拉框
        ttk.Label(config_frame, text="牌组：").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.deck_var = tk.StringVar()
        self.deck_combobox = ttk.Combobox(config_frame, textvariable=self.deck_var, width=30)
        self.deck_combobox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        # 取消默认牌组
    
    def create_text_sections(self):
        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 左侧原始文本区
        left_frame = ttk.LabelFrame(text_frame, text="原始文本", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.text_input = tk.Text(left_frame, wrap=tk.WORD, height=20)
        self.text_input.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="清空", command=self.clear_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=5)
        
        # 右侧预览区
        right_frame = ttk.LabelFrame(text_frame, text="转换预览", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.preview_text = tk.Text(right_frame, wrap=tk.WORD, height=20, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(right_frame, text="复制预览", command=self.copy_preview).pack(fill=tk.X, pady=(5, 0))
    
    def create_button_section(self):
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="解析文本", command=self.parse_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="推送至Anki", command=self.push_to_anki).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空所有", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="测试连接", command=self.test_connection).pack(side=tk.LEFT, padx=5)
    
    def create_status_section(self):
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X)
    
    def clear_text(self):
        self.text_input.delete(1.0, tk.END)
    
    def select_all(self):
        self.text_input.tag_add(tk.SEL, 1.0, tk.END)
    
    def copy_preview(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.preview_text.get(1.0, tk.END))
        self.status_var.set("提示：预览内容已复制到剪贴板")
    
    def clear_all(self):
        self.text_input.delete(1.0, tk.END)
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)
        self.status_var.set("就绪")
        self.cards = []
    
    def test_connection(self):
        try:
            url = "http://localhost:8765"
            payload = {"action": "version", "version": 6}
            response = requests.post(url, json=payload, timeout=3)
            version = response.json()["result"]
            self.status_var.set(f"Anki Connect连接成功，版本：{version}")
            # 重新获取牌组列表
            self.get_deck_names()
            return True
        except Exception as e:
            self.status_var.set("连接失败：请检查Anki是否启动，或Anki Connect是否安装")
            return False
    
    def get_deck_names(self):
        try:
            url = "http://localhost:8765"
            payload = {"action": "deckNames", "version": 6}
            response = requests.post(url, json=payload, timeout=3)
            self.deck_names = response.json()["result"]
            self.deck_combobox['values'] = self.deck_names
        except:
            pass
    
    def parse_text(self):
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            self.status_var.set("提示：请输入文本")
            return
        
        self.cards = []
        preview_content = ""
        
        # 按---分割文本
        sections = re.split(r'---+', text)
        
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            
            # 检查是否为Cloze卡片（包含{{c1::}}等格式）
            if re.search(r'\{\{c\d+::[^}]+\}\}', section):
                self.cards.append({"type": "cloze", "text": section})
                preview_content += f"【Cloze】第{i+1}张\n{section}\n\n"
            else:
                # 基础卡：按第一行作为正面，其余作为背面
                lines = section.split('\n')
                if len(lines) >= 2:
                    front = lines[0].strip()
                    back = '\n'.join(lines[1:]).strip()
                    self.cards.append({"type": "basic", "front": front, "back": back})
                    preview_content += f"【基础卡】第{i+1}张\n正面：{front}\n背面：{back}\n\n"
                else:
                    # 只有一行，作为Cloze卡处理
                    self.cards.append({"type": "cloze", "text": section})
                    preview_content += f"【Cloze】第{i+1}张\n{section}\n\n"
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview_content)
        self.preview_text.config(state=tk.DISABLED)
        
        self.status_var.set(f"解析完成，共{len(self.cards)}张卡片")
    
    def push_to_anki(self):
        if not self.cards:
            self.status_var.set("提示：请先解析文本")
            return
        
        # 测试连接
        if not self.test_connection():
            return
        
        tag = self.tag_entry.get().strip()
        if not tag:
            self.status_var.set("提示：请输入标签")
            return
        
        # 保留原始标签，不进行任何过滤
        pass
        
        deck_name = self.deck_var.get().strip()
        if not deck_name:
            self.status_var.set("提示：请选择或输入牌组")
            return
        
        # 检查牌组是否存在，不存在则创建
        if deck_name not in self.deck_names:
            try:
                url = "http://localhost:8765"
                payload = {"action": "createDeck", "version": 6, "params": {"deck": deck_name}}
                response = requests.post(url, json=payload, timeout=3)
                if response.json()["result"]:
                    self.status_var.set(f"牌组 '{deck_name}' 创建成功")
                    self.deck_names.append(deck_name)
                    self.deck_combobox['values'] = self.deck_names
            except Exception as e:
                self.status_var.set(f"错误：创建牌组失败：{str(e)}")
                return
        
        # 启动后台线程执行推送
        self.status_var.set("开始推送...")
        thread = threading.Thread(target=self._push_to_anki_thread, args=(deck_name, tag))
        thread.daemon = True  # 设置为守护线程，避免阻塞程序退出
        thread.start()
    
    def _push_to_anki_thread(self, deck_name, tag):
        # 开始推送
        success_count = 0
        fail_count = 0
        
        for i, card in enumerate(self.cards):
            # 使用after方法更新UI，避免线程安全问题，使用默认参数捕获循环变量的值
            self.root.after(0, lambda msg=f"正在推送第{i+1}张...", i=i: self.status_var.set(msg))
            
            try:
                if card["type"] == "cloze":
                    success = self.push_cloze_card(deck_name, tag, card["text"])
                else:
                    success = self.push_basic_card(deck_name, tag, card["front"], card["back"])
                
                if success:
                    success_count += 1
                    self.root.after(0, lambda msg=f"第{i+1}张推送成功", i=i: self.status_var.set(msg))
                else:
                    fail_count += 1
                    self.root.after(0, lambda msg=f"第{i+1}张推送失败", i=i: self.status_var.set(msg))
                
                # 每推送10张暂停0.5秒，避免Anki卡顿
                if (i+1) % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                fail_count += 1
                self.root.after(0, lambda msg=f"第{i+1}张推送失败：{str(e)}", i=i: self.status_var.set(msg))
            
            time.sleep(0.1)  # 短暂暂停，确保Anki有时间处理
        
        # 推送完成，使用after方法显示结果
        total = len(self.cards)
        self.root.after(0, lambda total=total, success_count=success_count, fail_count=fail_count, tag=tag, deck_name=deck_name:
            self.status_var.set(f"推送完成！共解析{total}张卡片，成功推送{success_count}张，失败{fail_count}张，标签：{tag}，牌组：{deck_name}")
        )
    
    def push_cloze_card(self, deck_name, tag, text):
        url = "http://localhost:8765"
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": deck_name,
                    "modelName": "Cloze",
                    "fields": {"Text": text},
                    "tags": [tag],
                    "options": {"allowDuplicate": False}
                }
            }
        }
        response = requests.post(url, json=payload, timeout=3)
        result = response.json()
        return result.get("result") is not None
    
    def push_basic_card(self, deck_name, tag, front, back):
        url = "http://localhost:8765"
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": deck_name,
                    "modelName": "Basic",
                    "fields": {"Front": front, "Back": back},
                    "tags": [tag],
                    "options": {"allowDuplicate": False}
                }
            }
        }
        response = requests.post(url, json=payload, timeout=3)
        result = response.json()
        return result.get("result") is not None

if __name__ == "__main__":
    root = tk.Tk()
    app = AnkiQuickCard(root)
    root.mainloop()