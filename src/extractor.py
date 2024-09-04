from dataclasses import dataclass, field
from datetime import datetime
from typing import List, AnyStr
import sqlite3
import xmltodict
from tqdm import tqdm


cfops_permitidos = ['5101', '5102', '5103', '5104', '5124', '5123', '5125', '6108',
                    '6101', '6102', '6103', '6104', '6107', '6124', '6123', '6125',
                    '5251', '5252', '5253', '5254', '5255', '5256', '5257', '5258',
                    '5301', '5302', '5303', '5304', '5305', '5306', '5307', '5351',
                    '5352', '5353', '5354', '5355', '5356', '5357', '5359', '5401',
                    '5402', '5403', '5405', '5551', '5651', '5652', '5653', '5654',
                    '5655', '5656', '5667', '6251', '6252', '6253', '6254', '6255',
                    '6256', '6257', '6258', '6301', '6302', '6303', '6304', '6305',
                    '6306', '6307', '6351', '6352', '6353', '6354', '6355', '6356',
                    '6357', '6359', '6401', '6402', '6403', '6404', '6551', '6651',
                    '6652', '6653', '6654', '6655', '6656', '6667']

# TODO: IMPORTAR TODOS OS POSSÍVEIS CFOPS PERMITIDOS


@dataclass
class ICMS:
    orig: str
    cst: str
    bc: float
    aliq: float
    valor: float


@dataclass
class COFINS:
    cst: str
    bc: float
    aliq: float
    valor: float


@dataclass
class PIS:
    cst: str
    bc: float
    aliq: float
    valor: float


@dataclass
class Impostos:
    icms: ICMS
    cofins: COFINS
    pis: PIS


@dataclass
class Produto:
    comp: str
    nome: str
    valor: float
    cfop: str
    frete: float = 0.0
    impostos: Impostos = field(default_factory=Impostos)


def safe_float_convertion(value: str) -> float:
    if value == "":
        return 0.0
    else:
        return float(value.replace(',', '.'))


def get_tributo_ncm(ncm: str) -> str:
    conn = sqlite3.connect('taxations.db')
    curr = conn.cursor()
    curr.execute("SELECT TRIBUTAÇÃO FROM tic_ncm_cst WHERE ncm = ?", (ncm,))
    return curr.fetchone()


def get_ncm_produto(lines: list[AnyStr], cod_0200: str) -> str:
    for line in lines:
        print(line)
        columns = line.strip().split("|")
        if '|0200|' in line and '|9999|' not in line and '|9900|':
            if columns[2] == cod_0200:
                print(columns)
                return columns[8]


def retorna_produtos_e_impostos_cruzamento_efd_icms_pis_cofins(efd_icms_paths, efd_pis_cofins_paths) -> List[Produto]:
    produtos = []

    # Wrap efd_icms_paths with tqdm for progress tracking
    for efd_icms_path in tqdm(efd_icms_paths, desc="Processing EFD ICMS Files"):
        with open(efd_icms_path, 'r', encoding="Latin-1") as file:
            efd_data_inicio, efd_data_fim = check_sped_date(efd_icms_path, 4, 5)
            lines = file.readlines()
            orig_icms = '0'
            cst_icms = ''
            aliq_icms = 0
            bc_icms = 0
            valor_icms = 0
            comp_icms = ''
            icms_found = False

            for line in lines:
                columns = line.strip().split("|")
                if '|0000|' in line and '|9999|' not in line and '|9900|' not in line:
                    date_obj = extract_date_from_line(columns, 4)
                    comp_icms = date_obj.strftime("%m/%Y")
                if '|C190|' in line and '|9999|' not in line and '|9900|' not in line:
                    if columns[3] in cfops_permitidos:
                        cst_icms = columns[2]
                        aliq_icms = safe_float_convertion(columns[4])
                        bc_icms += safe_float_convertion(columns[6])
                        valor_icms += safe_float_convertion(columns[7])
                        icms_found = True

            if not icms_found:
                continue

            icms_total_values = ICMS(
                orig=orig_icms,
                cst=cst_icms,
                bc=bc_icms,
                aliq=aliq_icms,
                valor=valor_icms
            )

            tributado = 0
            total_produtos = 0
            data_flag = False
            produtos_found = False

            for efd_pis_cofins_path in tqdm(efd_pis_cofins_paths, desc="Processing EFD PIS/COFINS Files", leave=False):
                with open(efd_pis_cofins_path, 'r', encoding="Latin-1") as efd:
                    lines = efd.readlines()
                    cst_pis = ""
                    bc_pis = 0
                    aliq_pis = 0
                    valor_pis = 0
                    cst_cofins = ""
                    bc_cofins = 0
                    aliq_cofins = 0
                    valor_cofins = 0
                    nome_produto = ""
                    valor_produto = 0
                    cfop_produto = ""
                    frete_produto = 0

                    for index, line_pis_cofins in enumerate(lines):
                        columns = line_pis_cofins.strip().split("|")
                        if '|0000|' in line_pis_cofins:
                            if '|9999|' not in line_pis_cofins and '|9900|' not in line_pis_cofins:
                                date_obj = extract_date_from_line(columns, 6)
                                if efd_data_inicio <= date_obj <= efd_data_fim:
                                    data_flag = True
                        if data_flag:
                            if '|C100|' in line and '|9900|' not in line:
                                latest_c100_valid = is_c100_valid(line)
                            if '|C170|' in line and '|9900|' not in line:
                                if latest_c100_valid and len(columns) >= 39:
                                    total_produtos += 1
                                    cod_0200 = columns[2]
                                    ncm = get_ncm_produto(lines, cod_0200)
                                    class_tributo = get_tributo_ncm(ncm)
                                    if class_tributo == 'TRIBUTADO':
                                        tributado += 1

                                    cst_pis = columns[24]
                                    bc_pis += safe_float_convertion(columns[26])
                                    aliq_pis = safe_float_convertion(columns[27])
                                    valor_pis += safe_float_convertion(columns[30])
                                    cst_cofins = columns[31]
                                    bc_cofins += safe_float_convertion(columns[32])
                                    aliq_cofins = safe_float_convertion(columns[33])
                                    valor_cofins += safe_float_convertion(columns[36])
                                    nome_produto = columns[8]
                                    valor_produto += safe_float_convertion(columns[13])
                                    cfop_produto = columns[11]
                                    frete_produto += safe_float_convertion(columns[20])
                                    produtos_found = True

                    if not produtos_found:
                        continue

                    data_flag = False

                    if total_produtos != 0:
                        proporcao_tributados = tributado / total_produtos
                        icms_proporcional_tributado_values = ICMS(
                            orig=icms_total_values.orig,
                            cst=icms_total_values.cst,
                            bc=icms_total_values.bc * proporcao_tributados,
                            aliq=icms_total_values.aliq,
                            valor=icms_total_values.valor * proporcao_tributados
                        )

                        pis_values = PIS(
                            cst=cst_pis,
                            bc=bc_pis,
                            aliq=aliq_pis,
                            valor=valor_pis
                        )

                        cofins_values = COFINS(
                            cst=cst_cofins,
                            bc=bc_cofins,
                            aliq=aliq_cofins,
                            valor=valor_cofins
                        )

                        impostos = Impostos(
                            icms=icms_proporcional_tributado_values,
                            cofins=cofins_values,
                            pis=pis_values
                        )

                        produto = Produto(
                            comp=comp_icms,
                            nome=nome_produto,
                            valor=valor_produto,
                            cfop=cfop_produto,
                            frete=0,
                            impostos=impostos
                        )

                        produtos.append(produto)
                        break
                    else:
                        print("Data de EFD ICMS não encontrada no EFD PIS/COFINS")
    return produtos


# sped contrib
def retorna_produtos_e_impostos_sped_contrib(sped_contrib_paths) -> List[Produto] | str:
    found_0000 = False
    product_list = []
    for sped_contrib_path in sped_contrib_paths:
        try:
            with open(sped_contrib_path, 'r', encoding="Latin-1") as file:
                lines = file.readlines()
                latest_c100_valid = False
                valor_total_nota = 0.0
                frete_calculado = 0.0
                for index, line in enumerate(lines):
                    if check_line_reg('|0000|', line) and not found_0000:
                        date_obj = extract_date_from_line(line, 6)
                        comp_contrib = date_obj.strftime("%m/%Y")
                        found_0000 = True
                    if '|C100|' in line and '|9900|' not in line:
                        c100_columns = line.strip().split("|")
                        dict_c100 = get_c100_dict(c100_columns, index)
                        try:
                            valor_total_nota = float(dict_c100['16-VL_MERC'].replace(',', '.'))
                        except ValueError:
                            continue
                        frete_calculado = float(dict_c100['18-VL_FRT'].replace(',', '.'))
                        latest_c100_valid = is_c100_valid(line)
                    if '|C170|' in line:
                        columns = line.strip().split("|")
                        if latest_c100_valid and len(columns) >= 39:
                            dict_c170 = get_c170_dict(columns, index)
                            if dict_c170['11-CFOP'] in ['5202', '5927', '5949']:
                                continue
                            valor_item = float(dict_c170['07-VL_ITEM'].replace(',', '.'))
                            if dict_c170['11-CFOP'] in ['6108']:
                                valor_item += float(dict_c170['24-VL_IPI'].replace(',', '.'))
                            freteParcial = 0
                            if valor_total_nota != 0:
                                freteParcial = round((valor_item / valor_total_nota) * frete_calculado, 2)
                            valor_item_validado = round(
                                valor_item - float(dict_c170['08-VL_DESC'].replace(',', '.')), 2)
                            if freteParcial > 0:
                                valor_item_validado += freteParcial
                            if compara_valores(valor_item_validado,
                                               dict_c170['26-VL_BC_PIS'],
                                               dict_c170['32-VL_BC_COFINS']):
                                icms = ICMS(
                                    orig='0',
                                    cst=dict_c170['10-CST_ICMS'],
                                    bc=float(dict_c170['13-VL_BC_ICMS'].replace(',', '.')),
                                    aliq=float(dict_c170['14-ALIQ_ICMS'].replace(',', '.')),
                                    valor=float(dict_c170['15-VL_ICMS'].replace(',', '.'))
                                )
                                pis = PIS(
                                    cst=dict_c170['25-CST_PIS'],
                                    bc=float(dict_c170['26-VL_BC_PIS'].replace(',', '.')),
                                    aliq=float(dict_c170['27-ALIQ_PIS'].replace(',', '.')),
                                    valor=float(dict_c170['30-VL_PIS'].replace(',', '.'))
                                )
                                cofins = COFINS(
                                    cst=dict_c170['31-CST_COFINS'],
                                    bc=float(dict_c170['32-VL_BC_COFINS'].replace(',', '.')),
                                    aliq=float(dict_c170['33-ALIQ_COFINS'].replace(',', '.')),
                                    valor=float(dict_c170['36-VL_COFINS'].replace(',', '.'))
                                )
                                impostos = Impostos(
                                    icms=icms,
                                    cofins=cofins,
                                    pis=pis
                                )
                                produto = Produto(
                                    comp=comp_contrib,
                                    nome=dict_c170['04-DESCR_COMPL'],
                                    valor=valor_item_validado,
                                    cfop=dict_c170['11-CFOP'],
                                    frete=freteParcial,
                                    impostos=impostos
                                )
                                product_list.append(produto)
        except Exception as e:
            return str(e)
    return product_list


def check_sped_date(sped_path, pos_initial, pos_end):
    from datetime import datetime

    with open(sped_path, 'r', encoding='latin-1') as sped:
        lines = sped.readlines()
        for line in lines:
            if line.startswith('|0000|'):
                columns = line.split('|')
                date_initial = datetime.strptime(columns[pos_initial], '%d%m%Y')
                date_end = datetime.strptime(columns[pos_end], '%d%m%Y')
                return date_initial, date_end


def compara_valores(valor_validado, valor_pis, valor_cofins, tolerancia=3):
    """
    Compara o valor_validado com valor_pis e valor_cofins, retornando True se a diferença entre eles
    for menor ou igual à tolerância, tanto para cima quanto para baixo.

    :param valor_validado: Valor a ser validado.
    :param valor_pis: Valor da base PIS.
    :param valor_cofins: Valor da base COFINS.
    :param tolerancia: Tolerância permitida para a diferença.
    :return: True se a diferença for menor ou igual à tolerância, false caso contrário.
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


def get_c170_dict(columns, index):
    return {
        '01-REG': columns[1],
        '02-NUM_ITEM': columns[2],
        '03-COD_ITEM': columns[3],
        '04-DESCR_COMPL': columns[4],
        '05-QTD': columns[5],
        '06-UNID': columns[6],
        '07-VL_ITEM': columns[7],
        '08-VL_DESC': columns[8],
        '09-IND_MOV': columns[9],
        '10-CST_ICMS': columns[10],
        '11-CFOP': columns[11],
        '12-COD_NAT': columns[12],
        '13-VL_BC_ICMS': columns[13],
        '14-ALIQ_ICMS': columns[14],
        '15-VL_ICMS': columns[15],
        '16-VL_BC_ICMS_ST': columns[16],
        '17-ALIQ_ST': columns[17],
        '18-VL_ICMS_ST': columns[18],
        '19-IND_APUR': columns[19],
        '20-CST_IPI': columns[20],
        '21-COD_ENQ': columns[21],
        '22-VL_BC_IPI': columns[22],
        '23-ALIQ_IPI': columns[23],
        '24-VL_IPI': columns[24],
        '25-CST_PIS': columns[25],
        '26-VL_BC_PIS': columns[26],
        '27-ALIQ_PIS': columns[27],
        '28-QUANT_BC_PIS': columns[28],
        '29-ALIQ_PIS_REAIS': columns[29],
        '30-VL_PIS': columns[30],
        '31-CST_COFINS': columns[31],
        '32-VL_BC_COFINS': columns[32],
        '33-ALIQ_COFINS': columns[33],
        '34-QUANT_BC_COFINS': columns[34],
        '35-ALIQ_COFINS_REAIS': columns[35],
        '36-VL_COFINS': columns[36],
        '37-COD_CTA': columns[37],
        '38-VL_ABAT_NT': columns[38],
        '39-LINHA': index
    }


def get_c100_dict(columns, index):
    # Garantir que a lista 'columns' tem pelo menos 30 elementos
    if len(columns) < 30:
        raise ValueError(f"Lista de colunas com tamanho insuficiente: esperado 30, mas obteve {len(columns)}.")

    return {
        '01-REG': columns[1],
        '02-IND_OPER': columns[2],
        '03-IND_EMIT': columns[3],
        '04-COD_PART': columns[4],
        '05-COD_MOD': columns[5],
        '06-COD_SIT': columns[6],
        '07-SER': columns[7],
        '08-NUM_DOC': columns[8],
        '09-CHV_NFE': columns[9],
        '10-DT_DOC': columns[10],
        '11-DT_E_S': columns[11],
        '12-VL_DOC': columns[12],
        '13-IND_PGTO': columns[13],
        '14-VL_DESC': columns[14],
        '15-VL_ABAT_NT': columns[15],
        '16-VL_MERC': columns[16],
        '17-IND_FRT': columns[17],
        '18-VL_FRT': columns[18],
        '19-VL_SEG': columns[19],
        '20-VL_OUT_DA': columns[20],
        '21-VL_BC_ICMS': columns[21],
        '22-VL_ICMS': columns[22],
        '23-VL_BC_ICMS_ST': columns[23],
        '24-VL_ICMS_ST': columns[24],
        '25-VL_IPI': columns[25],
        '26-VL_PIS': columns[26],
        '27-VL_COFINS': columns[27],
        '28-VL_PIS_ST': columns[28],
        '29-VL_COFINS_ST': columns[29],
        '30-LINHA': index
    }


def is_c100_valid(line):
    """
    Confere segundo campo do registro C100
    """
    arq = line.strip().split("|")
    return len(arq) > 1 and arq[2] == '1'


# Nota fiscal
def retorna_produtos_e_impostos_xmls(xml_paths) -> List[Produto]:
    product_list = []
    for xml_path in xml_paths:
        try:
            with open(xml_path, 'rb') as file:
                parsed_xml = xmltodict.parse(file)
                data = parsed_xml['nfeProc']['NFe']['infNFe']['ide']['dhEmi']
                comp_date = parse_date(data)
                if comp_date:
                    comp_xml = comp_date.strftime('%m/%Y')
                else:
                    comp_xml = "Invalid Date"

                products = parsed_xml['nfeProc']['NFe']['infNFe']['det']

                if not isinstance(products, list):
                    products = [products]

                for product in products:
                    prod_data = product['prod']
                    imposto_data = product['imposto']

                    # TODO: Parar análise do produto caso ele tenha CFOP X

                    # TODO: Parar análise do produto caso seja uma nota de entrada

                    frete = float(prod_data.get('vFrete', 0.0))

                    icms_data = imposto_data['ICMS']
                    icms_key = next(iter(icms_data))
                    icms = icms_data[icms_key]

                    cofins_data = imposto_data['COFINS']['COFINSAliq'] if 'COFINSAliq' in imposto_data[
                        'COFINS'] else None
                    pis_data = imposto_data['PIS']['PISAliq'] if 'PISAliq' in imposto_data['PIS'] else None

                    produto_info = Produto(
                        comp=comp_xml,
                        nome=prod_data['xProd'],
                        valor=float(prod_data['vProd']),
                        cfop=prod_data['CFOP'],
                        frete=frete,
                        impostos=Impostos(
                            icms=ICMS(
                                orig=icms.get('orig', 'N/A'),
                                cst=icms.get('CST', 'N/A'),
                                bc=float(icms.get('vBC', 0)),
                                aliq=float(icms.get('pICMS', 0)),
                                valor=float(icms.get('vICMS', 0)),
                            ),
                            cofins=COFINS(
                                cst=cofins_data.get('CST', 'N/A') if cofins_data else 'N/A',
                                bc=float(cofins_data.get('vBC', 0)) if cofins_data else 0.0,
                                aliq=float(cofins_data.get('pCOFINS', 0)) if cofins_data else 0.0,
                                valor=float(cofins_data.get('vCOFINS', 0)) if cofins_data else 0.0
                            ),
                            pis=PIS(
                                cst=pis_data.get('CST', 'N/A') if pis_data else 'N/A',
                                bc=float(pis_data.get('vBC', 0)) if pis_data else 0.0,
                                aliq=float(pis_data.get('pPIS', 0)) if pis_data else 0.0,
                                valor=float(pis_data.get('vPIS', 0)) if pis_data else 0.0
                            )
                        )
                    )
                    product_list.append(produto_info)
        except Exception as e:
            print(e)
            continue

    return product_list


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError as e:
        print(f"Error parsing date: {date_str} - {e}")
        return None


def check_line_reg(reg: str, line: str): return reg in line and '9900' not in line


def extract_date_from_line(columns, pos):
    date_str = columns[pos]
    day = date_str[:2]
    month = date_str[2:4]
    year = date_str[4:8]

    return datetime(int(year), int(month), int(day))
