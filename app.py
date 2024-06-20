from dicionarios import get_c170_dict, get_c100_dict
from tkinter import Tk, filedialog, messagebox


def is_c100_valid(line):
    arq = line.strip().split("|")
    return len(arq) > 1 and arq[2] == '1'


def extrair_infos(arquivo):
    validated_data = []
    total_retirada_icms = 0.0
    total_pis = 0.0
    total_cofins = 0.0
    total_item = 0.0

    with open(arquivo, 'r', encoding="Latin-1") as file:
        lines = file.readlines()
        latest_c100_valid = False
        valorTotalNota = 0.0
        freteCalculado = 0.0

        for index, line in enumerate(lines):
            if '|C100|' in line and '|9900|' not in line:
                c100columns = line.strip().split("|")
                dictC100 = get_c100_dict(c100columns, index)
                valorTotalNota = float(dictC100['16-VL_MERC'].replace(',', '.'))
                freteCalculado = float(dictC100['18-VL_FRT'].replace(',', '.'))
                latest_c100_valid = is_c100_valid(line)
            if '|C170|' in line:
                columns = line.strip().split("|")
                if latest_c100_valid and len(columns) >= 39:
                    dictC170 = get_c170_dict(columns, index)
                    if dictC170['11-CFOP'] in ['5202', '5927', '5949']:
                        continue

                    valor_item = float(dictC170['07-VL_ITEM'].replace(',', '.'))
                    freteParcial = round((valor_item / valorTotalNota) * freteCalculado, 2)
                    valorItemValidado = round(valor_item - float(dictC170['08-VL_DESC'].replace(',', '.')), 2)
                    if freteParcial > 0:
                        valorItemValidado += freteParcial

                    if valorItemValidado == float(dictC170['26-VL_BC_PIS'].replace(',', '.')) or str(valorItemValidado) == float(dictC170['32-VL_BC_COFINS'].replace(',', '.')):
                        validated_data.append(dictC170)
                        bcliqpis = float(dictC170['26-VL_BC_PIS'].replace(',', '.')) - float(
                            dictC170['15-VL_ICMS'].replace(',', '.'))
                        pisliq = bcliqpis * (float(dictC170['27-ALIQ_PIS'].replace(',', '.')) / 100)
                        resultPis = float(dictC170['30-VL_PIS'].replace(',', '.')) - pisliq

                        bcliqcofins = float(dictC170['32-VL_BC_COFINS'].replace(',', '.')) - float(dictC170['15-VL_ICMS'].replace(',', '.'))
                        cofinslic = bcliqcofins * (float(dictC170['33-ALIQ_COFINS'].replace(',', '.')) / 100)
                        resultCofins = float(dictC170['36-VL_COFINS'].replace(',', '.')) - cofinslic

                        total_cofins += resultCofins
                        total_pis += resultPis
                        total_retirada_icms += resultPis + resultCofins
                        total_item += valor_item

    print(f"Total item: {total_item:.2f}")
    print(f"Total cofins: {total_cofins:.2f}")
    print(f"Total pis: {total_pis:.2f}")
    print(f"Total retirada: {total_retirada_icms:.2f}")


def select_files():
    root = Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(
        title="Selecione os arquivos SPED",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    return file_paths


def main():
    file_paths = select_files()
    if not file_paths:
        messagebox.showinfo("Informação", "Nenhum arquivo selecionado.")
        return

    for file_path in file_paths:
        extrair_infos(file_path)

    messagebox.showinfo("Informação", "Processamento concluído!")


if __name__ == "__main__":
    main()
