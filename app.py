# -*- coding: utf-8 -*-
"""考勤处理工具 - 图形界面

依赖：xlrd==1.2.0, xlwt==1.3.0
打包（Windows）：
    pyinstaller --noconfirm --onefile --windowed --name 考勤处理工具 app.py
"""

import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import check_process


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('考勤处理工具')
        self.root.geometry('720x520')
        self.root.minsize(640, 460)

        self.input_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.out_var = tk.StringVar(value='结果.xls')
        self.days_var = tk.StringVar(value='4')

        self.log_queue: queue.Queue = queue.Queue()
        self.running = False

        self._build_ui()
        self.root.after(100, self._drain_log)

    def _build_ui(self):
        pad = {'padx': 8, 'pady': 6}

        # 输入文件
        frm_in = ttk.LabelFrame(self.root, text='1. 选择原始打卡流水（.xls）')
        frm_in.pack(fill='x', **pad)
        ttk.Entry(frm_in, textvariable=self.input_var).pack(side='left', fill='x', expand=True, padx=8, pady=8)
        ttk.Button(frm_in, text='浏览…', command=lambda: self._pick_file(self.input_var)).pack(side='left', padx=8, pady=8)

        # 模板文件
        frm_tpl = ttk.LabelFrame(self.root, text='2. 选择标准化模板（.xls，含员工姓名表头）')
        frm_tpl.pack(fill='x', **pad)
        ttk.Entry(frm_tpl, textvariable=self.file_var).pack(side='left', fill='x', expand=True, padx=8, pady=8)
        ttk.Button(frm_tpl, text='浏览…', command=lambda: self._pick_file(self.file_var)).pack(side='left', padx=8, pady=8)

        # 输出文件 + 天数
        frm_opt = ttk.LabelFrame(self.root, text='3. 输出与参数')
        frm_opt.pack(fill='x', **pad)
        ttk.Label(frm_opt, text='输出文件：').grid(row=0, column=0, sticky='w', padx=8, pady=8)
        ttk.Entry(frm_opt, textvariable=self.out_var).grid(row=0, column=1, sticky='we', padx=8, pady=8)
        ttk.Button(frm_opt, text='另存为…', command=self._pick_out).grid(row=0, column=2, padx=8, pady=8)
        ttk.Label(frm_opt, text='考勤天数：').grid(row=1, column=0, sticky='w', padx=8, pady=8)
        ttk.Entry(frm_opt, textvariable=self.days_var, width=10).grid(row=1, column=1, sticky='w', padx=8, pady=8)
        frm_opt.columnconfigure(1, weight=1)

        # 操作按钮
        frm_btn = ttk.Frame(self.root)
        frm_btn.pack(fill='x', **pad)
        self.run_btn = ttk.Button(frm_btn, text='开始处理', command=self._on_run)
        self.run_btn.pack(side='left', padx=8)
        ttk.Button(frm_btn, text='清空日志', command=self._clear_log).pack(side='left', padx=8)

        # 日志
        frm_log = ttk.LabelFrame(self.root, text='处理日志')
        frm_log.pack(fill='both', expand=True, **pad)
        self.log_text = tk.Text(frm_log, height=12, wrap='word', state='disabled')
        self.log_text.pack(side='left', fill='both', expand=True, padx=8, pady=8)
        scroll = ttk.Scrollbar(frm_log, command=self.log_text.yview)
        scroll.pack(side='right', fill='y', pady=8)
        self.log_text.config(yscrollcommand=scroll.set)

    # ---- 文件选择 ----
    def _pick_file(self, var):
        path = filedialog.askopenfilename(
            title='选择 Excel 文件',
            filetypes=[('Excel 97-2003', '*.xls'), ('所有文件', '*.*')]
        )
        if path:
            var.set(path)

    def _pick_out(self):
        path = filedialog.asksaveasfilename(
            title='保存输出文件',
            defaultextension='.xls',
            filetypes=[('Excel 97-2003', '*.xls')]
        )
        if path:
            self.out_var.set(path)

    # ---- 日志 ----
    def _append_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

    def _drain_log(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == '__DONE__':
                    self.on_done()
                    continue
                self._append_log(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log)

    # ---- 执行 ----
    def _on_run(self):
        if self.running:
            return

        input_path = self.input_var.get().strip()
        file_path = self.file_var.get().strip()
        out_path = self.out_var.get().strip()
        days = self.days_var.get().strip()

        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror('错误', '请选择有效的原始打卡流水文件。')
            return
        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror('错误', '请选择有效的标准化模板文件。')
            return
        if not out_path:
            messagebox.showerror('错误', '请填写输出文件路径。')
            return
        try:
            int(days)
        except ValueError:
            messagebox.showerror('错误', '考勤天数必须是整数。')
            return

        self.running = True
        self.run_btn.config(state='disabled', text='处理中…')
        self._append_log(f'开始处理：流水={input_path}，模板={file_path}，天数={days}')

        t = threading.Thread(target=self._worker, args=(input_path, file_path, days, out_path), daemon=True)
        t.start()

    def _worker(self, input_path, file_path, days, out_path):
        def log(msg):
            self.log_queue.put(str(msg))
        try:
            check_process.process(input_path, file_path, days, out_path, log=log)
            self.log_queue.put('__DONE__')
        except Exception as e:
            self.log_queue.put(f'处理失败：{e}')
            self.log_queue.put('__DONE__')

    def on_done(self):
        self.running = False
        self.run_btn.config(state='normal', text='开始处理')


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
