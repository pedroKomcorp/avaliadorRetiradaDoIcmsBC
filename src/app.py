import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.utils.docs import xlsx
from src.utils.extractor.sped_contrib_extract import extrair_infos
import os


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cnpj_entry = None
        self.progress = None
        self.file_listbox = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "icon.ico")
        self.iconbitmap(icon_path)
        self.title("KB - Retirada ICMS da Base de Cálculo")

        self.geometry("600x400")
        self.resizable(False, False)

        self.file_paths = []
        self.file_type = tk.StringVar(value="SPED ICMS IPI")
        self.client_name = tk.StringVar()
        self.client_cnpj = tk.StringVar()
        self.save_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        self.create_left_section()
        self.create_file_list()
        self.create_progress_bar()
        self.create_process_button()
        # self.create_save_location()
        # self.create_progress_bar()
        # self.create_process_button()

    def create_left_section(self):
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.create_file_selector(frame)
        self.create_file_type_dropdown(frame)
        self.create_client_info(frame)
        self.create_save_location(frame)

    def create_file_selector(self, frame):
        select_button = tk.Button(frame, text="Selecionar Arquivos", command=self.select_files)
        select_button.grid(row=0, column=0, sticky=tk.NW, pady=18, padx=15)

    def create_file_type_dropdown(self, frame):
        options = ["SPED Contribuições", "SPED ICMS IPI", "NF-C"]
        dropdown = tk.OptionMenu(frame, self.file_type, self.file_type.get(), *options, command=self.update_file_list)
        dropdown.grid(row=0, column=1, pady=10)

    def create_file_list(self):
        self.file_listbox = tk.Listbox(self, height=10, width=50)
        self.file_listbox.grid(row=0, column=1, pady=10, padx=10, sticky=tk.NS)

    def create_client_info(self, frame):
        tk.Label(frame, text="Nome do Cliente:").grid(row=1, column=0, pady=5, sticky=tk.NSEW)
        tk.Entry(frame, textvariable=self.client_name).grid(row=1, column=1, padx=10, pady=5)
        client_cnpj = tk.StringVar(value="xxx.xxx.xx/xxxx-xx")
        vcmd = (self.register(self.on_validate), '%P')

        self.cnpj_entry = tk.Entry(frame, textvariable=client_cnpj, validate='key', validatecommand=vcmd)
        self.cnpj_entry.grid(row=2, column=1, padx=10, pady=5)
        self.cnpj_entry.bind("<KeyRelease>", self.on_key_release)

    def create_save_location(self, frame):
        tk.Label(frame, text="").grid(row=4, column=0, pady=4, sticky=tk.NSEW)
        tk.Label(frame, text="Salvar em:").grid(row=5, column=0, padx=5, pady=5)
        tk.Entry(frame, textvariable=self.save_path).grid(row=5, column=1, padx=5, pady=5)
        tk.Button(frame, text="Selecionar Pasta", command=self.select_save_location).grid(row=6, column=1, padx=5,
                                                                                          pady=5)

    def create_progress_bar(self):
        self.progress = ttk.Progressbar(self, orient="horizontal", length=250, mode="determinate")
        self.progress.grid(row=1, column=1, padx=10, pady=10)

    def create_process_button(self):
        process_button = tk.Button(self, text="Criar XLSX", command=self.process_documents)
        process_button.grid(row=2, column=0, pady=10)

    def select_files(self):
        self.file_paths = filedialog.askopenfilenames(title="Selecione os arquivos")
        self.file_listbox.delete(0, tk.END)
        for file_path in self.file_paths:
            self.file_listbox.insert(tk.END, file_path)

    def select_save_location(self):
        folder_selected = filedialog.askdirectory(title="Selecione a pasta para salvar")
        if folder_selected:
            self.save_path.set(folder_selected)

    def process_documents(self):
        if not self.file_paths:
            messagebox.showinfo("Informação", "Nenhum arquivo selecionado.")
            return
        if not self.client_name.get() or not self.client_cnpj.get():
            messagebox.showinfo("Informação", "Nome do Cliente e CNPJ são obrigatórios.")
            return
        if not self.save_path.get():
            messagebox.showinfo("Informação", "Selecione o local para salvar o arquivo.")
            return

        results = []
        self.progress["maximum"] = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths):
            result = extrair_infos(file_path)
            results.append(result)
            self.progress["value"] = i + 1
            self.update_idletasks()

        filename = f"{self.save_path.get()}/{self.client_name.get()}.xlsx"
        xlsx.create_spreadsheet(results, filename, self.client_name.get(), self.client_cnpj.get())

        messagebox.showinfo("Informação", "Processamento concluído!")
        self.progress["value"] = 0
        self.destroy()

    def update_file_list(self, _=None):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.file_paths:
            self.file_listbox.insert(tk.END, file_path)

    def on_validate(self, P):
        # Permite apenas números ou string vazia
        if P.isdigit() or P == "":
            return True
        return False

    def on_key_release(self, event):
        current_text = self.cnpj_entry.get()
        formatted_text = self.format_cnpj(current_text)
        self.client_cnpj.set(formatted_text)
        self.cnpj_entry.delete(0, tk.END)
        self.cnpj_entry.insert(0, formatted_text)
        # Move o cursor para o final
        self.cnpj_entry.icursor(tk.END)

    def format_cnpj(self, cnpj):
        # Remove tudo que não é número
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) == 0:
            return "xxx.xxx.xx/xxxx-xx"

        # Aplica a máscara de CNPJ
        formatted = "xxx.xxx.xx/xxxx-xx"
        for i in range(len(cnpj)):
            formatted = formatted.replace('x', cnpj[i], 1)
        return formatted


if __name__ == "__main__":
    app = Application()
    app.mainloop()
