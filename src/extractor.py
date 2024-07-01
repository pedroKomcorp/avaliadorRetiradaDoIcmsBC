from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import xmltodict


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


# sped contrib
def retorna_produtos_e_impostos_sped_contrib(sped_contrib_paths) -> List[Produto]:
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
                        date_obj = extract_date_from_line(line)
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

                            valor_item_validado = round(valor_item - float(dict_c170['08-VL_DESC'].replace(',', '.')),
                                                        2)
                            if freteParcial > 0:
                                valor_item_validado += freteParcial

                            if compara_valores(valor_item_validado, dict_c170['26-VL_BC_PIS'],
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
            print(f"Erro ao processar o arquivo {sped_contrib_path}: {e}")
    return product_list


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
                data = parsed_xml['nfeProc']['NFe']['infNFe']['ide']['dhEmi']  # initial format 2024-03-01T11:21:05-03:00
                comp_date = parse_date(data)  # Parse the date string
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

                    cofins_data = imposto_data['COFINS']['COFINSAliq'] if 'COFINSAliq' in imposto_data['COFINS'] else None
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


def extract_date_from_line(line):
    columns = line.strip().split('|')
    date_str = columns[6]
    day = date_str[:2]
    month = date_str[2:4]
    year = date_str[4:8]

    date_obj = datetime(int(year), int(month), int(day))
    return date_obj