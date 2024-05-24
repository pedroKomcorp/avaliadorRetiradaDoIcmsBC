import pandas as pd
import glob
import re
from dicionarios import get_c170_dict

def is_c100_valid(line):
    arq = line.strip().split("|")
    return len(arq) > 1 and arq[2] == '1'

def extrair_infos(arquivo):
    validated_data = []
    file_name = re.search(r'PISCOFINS_\d{8}_\d{8}', arquivo).group()
    total_vl_item = 0.0

    with open(arquivo, 'r', encoding="Latin-1") as file:
        lines = file.readlines()
        latest_c100_valid = False

        for index, line in enumerate(lines):
            if '|C100|' in line:
                latest_c100_valid = is_c100_valid(line)

            if '|C170|' in line:
                columns = line.strip().split("|")
                if latest_c100_valid and len(columns) >= 39:
                    dictC170 = get_c170_dict(columns, index)
                    # Nova validação para CFOP
                    if dictC170['11-CFOP'] == '5202':
                        continue
                    if dictC170['11-CFOP'] == '5927':
                        continue

                    if dictC170['26-VL_BC_PIS'] == '0' or dictC170['32-VL_BC_COFINS'] == '0':
                        validated_data.append(dictC170)
                        total_vl_item += float(dictC170['07-VL_ITEM'].replace(',', '.'))
                    elif dictC170['07-VL_ITEM'] == dictC170['26-VL_BC_PIS'] or dictC170['07-VL_ITEM'] == dictC170['32-VL_BC_COFINS']:
                        validated_data.append(dictC170)
                        total_vl_item += float(dictC170['07-VL_ITEM'].replace(',', '.'))

    df_validated = pd.DataFrame(validated_data)
    validated_csv_file_path = f'C:\\Users\\pedro.neto\\Documents\\leitorSped\\data\\output\\{file_name}_C170_validated_data.csv'
    df_validated.to_csv(validated_csv_file_path, index=False, sep='|', encoding='utf-8')

    print(f"VL TOTAL ITENS EM {file_name}: {total_vl_item:.2f}")

def main():
    file_paths = glob.glob('C:\\Users\\pedro.neto\\Documents\\leitorSped\\data\\input\\*.txt')

    for file_path in file_paths:
        extrair_infos(file_path)

if __name__ == "__main__":
    main()
