import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from extractor import retorna_produtos_e_impostos_sped_contrib
from extractor import retorna_produtos_e_impostos_xmls
from extractor import retorna_produtos_e_impostos_cruzamento_efd_icms_pis_cofins
from transformer import retorna_retirada_icms_bc, agrupar_resultados_por_comp
from loader import create_spreadsheet


def format_cnpj(cnpj):
    # Remove tudo que não é número
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) == 0:
        return "xxx.xxx.xx/xxxx-xx"

    # Aplica a máscara de CNPJ
    formatted = "xxx.xxx.xx/xxxx-xx"
    for i in range(len(cnpj)):
        formatted = formatted.replace('x', cnpj[i], 1)
    return formatted


def on_validate(P):
    # Permite apenas números ou string vazia
    if P.isdigit() or P == "":
        return True
    return False


class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.label_file_list = None
        self.left_section = None
        self.main_frame = None
        self.right_section_frame = None
        self.cnpj_entry = None
        self.progress = None
        self.file_listbox = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "kbicon.ico")
        self.iconbitmap(icon_path)
        self.title("KB - Retirada ICMS da Base de Cálculo")
        self.geometry("600x400")

        self.resizable(True, True)

        self.file_paths = []
        self.file_type = ctk.StringVar(name="Tipo Arquivo", value="Tipo Arquivo", )
        self.client_name = ctk.StringVar()
        self.client_cnpj = ctk.StringVar()
        self.save_path = ctk.StringVar()
        self.create_widgets()
        self.configure_grid()
        self.flag = None

        ctk.set_appearance_mode("dark")  # Set the appearance mode
        ctk.set_default_color_theme(os.path.join(script_dir, "assets", "kombussines_theme.json"))  # Set the color theme

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, fg_color='#EEEEEE', corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky=ctk.NSEW)
        self.main_frame.grid_columnconfigure(0, weight=10)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.create_left_section()
        self.create_right_section()
        self.create_progress_bar()
        self.create_process_button()

    def create_left_section(self):
        self.left_section = ctk.CTkFrame(self.main_frame, fg_color='#242424')
        self.left_section.grid(row=0, column=0, pady=10, padx=(10, 0), sticky=ctk.NSEW)
        self.left_section.grid_columnconfigure(0, weight=1)
        self.left_section.grid_columnconfigure(1, weight=1)

        self.create_file_type_dropdown(self.left_section)
        self.create_file_selector(self.left_section)
        self.create_client_info(self.left_section)
        self.create_save_location(self.left_section)

    def create_file_selector(self, frame):
        # Clear any existing widgets in the frame to avoid overlap
        for widget in frame.grid_slaves(row=0, column=1):
            widget.grid_forget()

        if self.flag == "flag_sped_contrib":
            select_button = ctk.CTkButton(frame, text="Selecionar Arquivos SPED Contribuições",
                                          command=self.select_files)
            select_button.grid(row=0, column=1, sticky=ctk.NSEW, pady=18, padx=15)
        elif self.flag == "flag_icms/pis_cofins":
            select_button = ctk.CTkButton(frame, text="Selecionar Arquivo EFD ICMS/PIS COFINS",
                                          command=self.select_files)
            select_button.grid(row=0, column=1, sticky=ctk.NSEW, pady=18, padx=15)
        elif self.flag == "flag_xml":
            select_button = ctk.CTkButton(frame, text="Selecionar Arquivos XML", command=self.select_files)
            select_button.grid(row=0, column=1, sticky=ctk.NSEW, pady=18, padx=15)
        else:
            ctk.CTkLabel(frame, text="Selecione o tipo de arquivo", text_color='#FFFFFF').grid(row=0, column=1, pady=10)

    def create_file_type_dropdown(self, frame):
        options = ["SPED Contribuições", "EFC ICMS/PIS COFINS", "XML"]
        dropdown = ctk.CTkOptionMenu(frame, variable=self.file_type, values=options, command=self.update_file_list)
        dropdown.grid(row=0, column=0, pady=10)

    def create_file_list(self):
        self.label_file_list = ctk.CTkLabel(self.right_section_frame, text="Lista de arquivos:", text_color='#FFFFFF')
        self.label_file_list.grid(row=0, column=1, pady=10)
        self.file_listbox = ctk.CTkTextbox(self.right_section_frame, height=200, width=10, state="disabled")
        self.file_listbox.grid(row=1, column=1, pady=10, padx=5, sticky=ctk.NSEW)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def create_client_info(self, frame):
        ctk.CTkLabel(frame, text="Nome do Cliente:").grid(row=1, column=0, pady=5, sticky=ctk.NSEW)
        ctk.CTkEntry(frame, textvariable=self.client_name).grid(row=1, column=1, padx=10, pady=5, sticky=ctk.NSEW)
        client_cnpj = ctk.StringVar(value="xxx.xxx.xx/xxxx-xx")
        vcmd = (self.register(on_validate), '%P')

        ctk.CTkLabel(frame, text="CNPJ:").grid(row=2, column=0, pady=5, sticky=ctk.NSEW)
        self.cnpj_entry = ctk.CTkEntry(frame, textvariable=client_cnpj, validate='key', validatecommand=vcmd)
        self.cnpj_entry.grid(row=2, column=1, padx=10, pady=5, sticky=ctk.NSEW)
        self.cnpj_entry.bind("<KeyRelease>", self.on_key_release)

    def create_save_location(self, frame):
        ctk.CTkLabel(frame, text="").grid(row=4, column=0, pady=4, sticky=ctk.NSEW)
        ctk.CTkLabel(frame, text="Salvar em:").grid(row=5, column=0, padx=5, pady=5, stick=ctk.E)
        ctk.CTkLabel(frame, textvariable=self.save_path, fg_color='#3a2a25').grid(row=5, column=1, padx=5, pady=5,
                                                                                  sticky=ctk.EW)
        ctk.CTkButton(frame, text="Selecionar Pasta", command=self.select_save_location).grid(row=6, column=1, padx=5,
                                                                                              pady=5, sticky=ctk.EW)

    def create_progress_bar(self):
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=ctk.EW)
        self.progress.set(0)

    def create_process_button(self):
        process_button = ctk.CTkButton(self.main_frame, text="Criar XLSX", command=self.process_documents)
        process_button.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky=ctk.EW)

    def select_files(self):
        self.file_listbox.configure(state="normal")
        self.file_paths = filedialog.askopenfilenames(title="Selecione os arquivos")
        self.file_listbox.delete("1.0", ctk.END)
        for file_path in self.file_paths:
            self.file_listbox.insert(ctk.END, file_path + "\n")
        self.file_listbox.configure(state="disabled")

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
        if self.file_type.get() == "Tipo Arquivo":
            messagebox.showinfo("Alerta!", "Selecione o tipo do arquivo.")
            return
        results = []
        total_files = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths):
            result = []
            if self.file_type.get() == "EFC ICMS/PIS COFINS":
                result = retorna_produtos_e_impostos_cruzamento_efd_icms_pis_cofins(icms_path, pis_cofins_path)
            if self.file_type.get() == "SPED Contribuições":
                result = retorna_produtos_e_impostos_sped_contrib([file_path])
            if self.file_type.get() == "XML":
                result = retorna_produtos_e_impostos_xmls([file_path])
            results.extend(result)
            self.progress.set((i + 1) / total_files)
            self.update_idletasks()

        resultados_processados = retorna_retirada_icms_bc(results)
        if len(resultados_processados) == 0:
            messagebox.showerror("Alerta!", "Nenhum movimentação valida encontrada.")
            self.progress.set(0)
            self.destroy()
        else:
            resultados_agrupados = agrupar_resultados_por_comp(resultados_processados)

            filename = f"{self.save_path.get()}/{self.client_name.get()}.xlsx"
            create_spreadsheet(resultados_agrupados, filename, self.client_name.get(), self.client_cnpj.get())
            messagebox.showinfo("Informação", "Processamento concluído!")
            self.progress.set(0)
            self.destroy()

    def update_file_list(self, _=None):
        # Update the flag based on the selected file type
        selected_option = self.file_type.get()
        if selected_option == "SPED Contribuições":
            self.flag = "flag_sped_contrib"
        elif selected_option == "EFD ICMS/PIS COFINS":
            self.flag = "flag_icms_pis_cofins"
        elif selected_option == "XML":
            self.flag = "flag_xml"
        else:
            self.flag = None  # Reset flag if no valid option is selected

        # Refresh the file selector display
        self.create_file_selector(self.left_section)

        # Update the file list display
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", ctk.END)
        for file_path in self.file_paths:
            self.file_listbox.insert(ctk.END, file_path + "\n")
        self.file_listbox.configure(state="disabled")

    def on_key_release(self):
        current_text = self.cnpj_entry.get()
        formatted_text = format_cnpj(current_text)
        self.client_cnpj.set(formatted_text)
        self.cnpj_entry.delete(0, ctk.END)
        self.cnpj_entry.insert(0, formatted_text)
        # Move o cursor para o final
        self.cnpj_entry.icursor(ctk.END)

    def create_right_section(self):
        self.right_section_frame = ctk.CTkFrame(self.main_frame, fg_color='#242424')
        self.right_section_frame.grid(row=0, column=1, pady=10, padx=(2, 10), sticky=ctk.NSEW)
        self.right_section_frame.grid_rowconfigure(0, weight=1)
        self.right_section_frame.grid_columnconfigure(1, weight=30)
        self.create_file_list()


if __name__ == "__main__":
    app = Application()
    app.mainloop()
