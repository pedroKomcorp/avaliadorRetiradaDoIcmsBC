import datetime

from src.utils.dicionarios import get_c170_dict, get_c100_dict
from tkinter import Tk, filedialog
from src.utils.results import ExtractionResult
from src.utils.getSelic import GetSelic


def check_line_reg(reg: str, line: str):
    return reg in line and '9900' not in line


def extract_date_from_line(line):
    columns = line.strip().split('|')
    date_str = columns[6]
    day = date_str[:2]
    month = date_str[2:4]
    year = date_str[4:8]

    date_obj = datetime.datetime(int(year), int(month), int(day))
    return date_obj


def is_c100_valid(line):
    """
    Confere segundo campo do registro C100
    """
    arq = line.strip().split("|")
    return len(arq) > 1 and arq[2] == '1'


def compara_valores(valor_validado, valor_pis, valor_cofins, tolerancia=3):
    """
    Compara o valor_validado com valor_pis e valor_cofins, retornando True se a diferença entre eles
    for menor ou igual à tolerância, tanto para cima quanto para baixo.

    :param valor_validado: Valor a ser validado.
    :param valor_pis: Valor da base PIS.
    :param valor_cofins: Valor da base COFINS.
    :param tolerancia: Tolerância permitida para a diferença.
    :return: True se a diferença for menor ou igual à tolerância, False caso contrário.
    """

    if valor_pis == "" or valor_cofins == "" or valor_pis is None or valor_cofins is None:
        valor_cofins = 0.0
        valor_pis = 0.0
    else:
        valor_pis = float(valor_pis.replace(',', '.'))
        valor_cofins = float(valor_cofins.replace(',', '.'))

    diferenca_pis = abs(valor_validado - valor_pis)
    diferenca_cofins = abs(valor_validado - valor_cofins)

    return diferenca_pis <= tolerancia or diferenca_cofins <= tolerancia


def extrair_infos(arquivo):
    get_selic = GetSelic()
    # Initialize variables
    comp = ""
    base_pis = 0.0
    base_cofins = 0.0
    valor_pis = 0.0
    valor_cofins = 0.0
    valor_icms = 0.0
    base_pis_sem_icms = 0.0
    base_cofins_sem_icms = 0.0
    selic = 0.0
    cred_pis = 0.0
    cred_pis_atz = 0.0
    cred_cofins = 0.0
    cred_cofins_atz = 0.0
    valor_pis_sem_icms = 0.0
    valor_cofins_sem_icms = 0.0

    found_0000 = False

    with open(arquivo, 'r', encoding="Latin-1") as file:
        lines = file.readlines()
        latest_c100_valid = False
        valorTotalNota = 0.0
        freteCalculado = 0.0

        for index, line in enumerate(lines):
            if check_line_reg('|0000|', line) and not found_0000:
                date_obj = extract_date_from_line(line)
                comp = date_obj.strftime("%m/%Y")

                # Get the selic for the found date
                selic = get_selic.retorna_selic(date_obj.year, date_obj.month)
                found_0000 = True

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
                    if dictC170['11-CFOP'] in ['6108']:
                        valor_item += float(dictC170['24-VL_IPI'].replace(',', '.'))
                    freteParcial = round((valor_item / valorTotalNota) * freteCalculado, 2)
                    valorItemValidado = round(valor_item - float(dictC170['08-VL_DESC'].replace(',', '.')), 2)
                    if freteParcial > 0:
                        valorItemValidado += freteParcial

                    if compara_valores(valorItemValidado, dictC170['26-VL_BC_PIS'], dictC170['32-VL_BC_COFINS']):
                        base_pis += float(dictC170['26-VL_BC_PIS'].replace(',', '.'))
                        valor_pis += float(dictC170['30-VL_PIS'].replace(',', '.'))
                        base_cofins += float(dictC170['32-VL_BC_COFINS'].replace(',', '.'))
                        valor_cofins += float(dictC170['36-VL_COFINS'].replace(',', '.'))
                        valor_icms += float(dictC170['15-VL_ICMS'].replace(',', '.'))
                        base_pis_sem_icms = base_pis - valor_icms
                        base_cofins_sem_icms = base_cofins - valor_icms
                        valor_pis_sem_icms = base_pis_sem_icms * (
                                float(dictC170['27-ALIQ_PIS'].replace(',', '.')) / 100)
                        valor_cofins_sem_icms = base_cofins_sem_icms * (
                                float(dictC170['33-ALIQ_COFINS'].replace(',', '.')) / 100)
                        cred_pis = valor_pis - valor_pis_sem_icms
                        cred_pis_atz = cred_pis * (1 + selic)
                        cred_cofins = valor_cofins - valor_cofins_sem_icms
                        cred_cofins_atz = cred_cofins * (1 + selic)

    return ExtractionResult(
        comp, base_pis, base_cofins, valor_pis, valor_cofins,
        valor_icms, base_pis_sem_icms, base_cofins_sem_icms,
        selic, valor_pis_sem_icms, valor_cofins_sem_icms,
        cred_pis, cred_pis_atz, cred_cofins, cred_cofins_atz
    )


def select_files():
    root = Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(
        title="Selecione os arquivos SPED",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    return file_paths

