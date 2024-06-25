from tkinter import messagebox

from src.utils import xls
from src.utils.extract import select_files, extrair_infos


def main():
    file_paths = select_files()
    if not file_paths:
        messagebox.showinfo("Informação", "Nenhum arquivo selecionado.")
        return

    client_name = "Nome do Cliente"
    client_cnpj = "CNPJ do Cliente"
    filename = "consolidated_results.xlsx"
    results = []
    for file_path in file_paths:
        result = extrair_infos(file_path)
        results.append(result)

    xls.create_spreadsheet(results, filename, client_name, client_cnpj)

    messagebox.showinfo("Informação", "Processamento concluído!")


if __name__ == "__main__":
    main()
