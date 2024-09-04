import sqlite3
from tkinter import filedialog
from extractor import retorna_produtos_e_impostos_cruzamento_efd_icms_pis_cofins
from transformer import retorna_retirada_icms_bc
from loader import create_spreadsheet

icms = filedialog.askopenfilenames(title='ICMS')
pis_cofins = filedialog.askopenfilenames(title='PIS/COFINS')

result = retorna_produtos_e_impostos_cruzamento_efd_icms_pis_cofins(icms, pis_cofins)
resultados_processados = retorna_retirada_icms_bc(result)

create_spreadsheet(resultados_processados, 'resultados_processados.xlsx', '', '')
