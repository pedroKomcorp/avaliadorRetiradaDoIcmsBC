import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xls  # Supondo que xls é o módulo onde a função create_spreadsheet está definida
from extract import extrair_infos  # Supondo que extrair_infos é a função que extrai informações dos arquivos


def format_cnpj(cnpj):
    # Remove any non-digit characters
    cnpj = ''.join(filter(str.isdigit, cnpj))
    # Format the CNPJ as xxx.xxx.xxx/xxxx-xx
    formatted = ""
    for i, digit in enumerate(cnpj):
        if i in [2, 5]:
            formatted += f"{digit}."
        elif i == 8:
            formatted += f"{digit}/"
        elif i == 12:
            formatted += f"{digit}-"
        else:
            formatted += digit
    return formatted


class Application(tk.Tk):

    def validate_cnpj(self, P):
        # Allow backspace (empty string), ensure only digits, and auto-format
        if P == "" or (P.isdigit() and len(P) <= 14):
            self.client_cnpj.set(format_cnpj(P))
            return True
        return False

    def __init__(self):
        super().__init__()
        self.progress = None
        self.file_listbox = None
        self.title("Processador de Documentos")
        self.geometry("600x400")
        self.state('zoomed')
        self.file_paths = []
        self.client_name = tk.StringVar()
        self.client_cnpj = tk.StringVar()
        self.save_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        self.create_file_selector()
        self.create_file_list()
        self.create_client_info()
        self.create_save_location()
        self.create_progress_bar()
        self.create_process_button()

    def create_file_selector(self):
        select_button = tk.Button(self, text="Selecionar Arquivos", command=self.select_files)
        select_button.pack(pady=10)

    def create_file_list(self):
        self.file_listbox = tk.Listbox(self, height=10, width=50)
        self.file_listbox.pack(pady=10)

    def create_client_info(self):
        frame = tk.Frame(self)
        frame.pack(pady=10)

        tk.Label(frame, text="Nome do Cliente:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(frame, textvariable=self.client_name).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="CNPJ do Cliente:").grid(row=1, column=0, padx=5, pady=5)

        vcmd = (self.register(self.validate_cnpj), '%P')
        self.cnpj_entry = tk.Entry(frame, textvariable=self.client_cnpj, validate='key', validatecommand=vcmd)
        self.cnpj_entry.grid(row=1, column=1, padx=5, pady=5)

    def create_save_location(self):
        frame = tk.Frame(self)
        frame.pack(pady=10)

        tk.Label(frame, text="Salvar em:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(frame, textvariable=self.save_path).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame, text="Selecionar Pasta", command=self.select_save_location).grid(row=0, column=2, padx=5,
                                                                                          pady=5)

    def create_progress_bar(self):
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)

    def create_process_button(self):
        process_button = tk.Button(self, text="Criar XLSX", command=self.process_documents)
        process_button.pack(pady=10)

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
        xls.create_spreadsheet(results, filename, self.client_name.get(), self.client_cnpj.get())

        messagebox.showinfo("Informação", "Processamento concluído!")
        self.progress["value"] = 0
        app.destroy()


if __name__ == "__main__":
    app = Application()
    app.mainloop()
