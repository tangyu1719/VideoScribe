#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox

print("创建窗口...")
root = tk.Tk()
root.title("测试窗口")
root.geometry("400x300")

label = tk.Label(root, text="测试成功！", font=("Arial", 20))
label.pack(pady=50)

button = tk.Button(root, text="确定", command=root.destroy)
button.pack(pady=20)

print("启动主循环...")
root.mainloop()
print("窗口关闭")
