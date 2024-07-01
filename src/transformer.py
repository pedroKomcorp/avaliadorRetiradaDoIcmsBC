from collections import defaultdict
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup


class GetSelic:

    def __init__(self):
        self.url = (
            "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/pagamentos-e-parcelamentos/taxa-de"
            "-juros-selic#Selicmensalmente"
        )
        self.selic_data = {2019: [], 2020: [], 2021: [], 2022: [], 2023: [], 2024: []}

    def fetch_data(self):
        response = requests.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract data from the 2019 table
        table_2019 = soup.select_one('#parent-fieldname-text > table:nth-of-type(7)')
        if table_2019:
            for row_index in range(2, 14):
                cell = table_2019.select_one(f'tbody > tr:nth-of-type({row_index}) > td:nth-of-type(6)')
                if cell:
                    month_data = cell.text.strip()
                    self.selic_data[2019].append(month_data)

        # Extract data from the 2020-2024 table
        table_2020_2024 = soup.select_one('#parent-fieldname-text > table:nth-of-type(6)')
        if table_2020_2024:
            rows = table_2020_2024.find_all('tr')[1:]  # Skip the header row
            for row in rows:
                cells = row.find_all('td')
                for i, year in enumerate(range(2020, 2025), start=1):
                    if len(cells) >= i + 1:
                        month_data = cells[i].text.strip()
                        self.selic_data[year].append(month_data)

    def retorna_selic(self, ano, mes):
        try:
            mes += 1
            if mes == 13:
                mes = 1
                ano += 1
            if not self.selic_data[2019]:  # Check if data has not been fetched yet
                self.fetch_data()

            if ano not in self.selic_data or mes < 1 or mes > 12:
                raise ValueError("Ano ou mês inválido.")

            if len(self.selic_data[ano]) < mes:
                raise ValueError("Dados insuficientes para o ano/mês especificado.")

            month_data = self.selic_data[ano][mes - 1]  # Adjust for 0-based index
            return float(month_data.replace(',', '.')) / 100
        except ValueError:
            return print("Não existe selic para esta data ainda!")


get_selic = GetSelic()


@dataclass
class ExtractionResult:
    comp: str
    base_pis: float
    base_cofins: float
    valor_pis: float
    valor_cofins: float
    valor_icms: float
    base_pis_sem_icms: float
    base_cofins_sem_icms: float
    selic: float
    valor_pis_sem_icms: float
    valor_cofins_sem_icms: float
    cred_pis: float
    cred_pis_atz: float
    cred_cofins: float
    cred_cofins_atz: float


def retorna_retirada_icms_bc(produtos: list):
    resultados = []
    for produto in produtos:
        base_pis_sem_icms = produto.impostos.pis.bc - produto.impostos.icms.valor
        base_cofins_sem_icms = produto.impostos.cofins.bc - produto.impostos.icms.valor
        valor_pis_sem_icms = base_pis_sem_icms * (produto.impostos.pis.aliq / 100)
        valor_cofins_sem_icms = base_cofins_sem_icms * (produto.impostos.cofins.aliq / 100)
        cred_pis = produto.impostos.pis.valor - valor_pis_sem_icms
        cred_cofins = produto.impostos.cofins.valor - valor_cofins_sem_icms

        comp_mes = produto.comp.split('/')[0]
        comp_ano = produto.comp.split('/')[1]

        selic = get_selic.retorna_selic(int(comp_ano), int(comp_mes))
        selic = selic
        cred_pis_atz = cred_pis * (1 + selic)
        cred_cofins_atz = cred_cofins * (1 + selic)

        resultado = ExtractionResult(
            comp=produto.comp,
            base_pis=produto.impostos.pis.bc + produto.frete,
            base_cofins=produto.impostos.cofins.bc + produto.frete,
            valor_pis=produto.impostos.pis.valor,
            valor_cofins=produto.impostos.cofins.valor,
            valor_icms=produto.impostos.icms.valor,
            base_pis_sem_icms=base_pis_sem_icms,
            base_cofins_sem_icms=base_cofins_sem_icms,
            selic=selic,
            valor_pis_sem_icms=valor_pis_sem_icms,
            valor_cofins_sem_icms=valor_cofins_sem_icms,
            cred_pis=cred_pis,
            cred_pis_atz=cred_pis_atz,
            cred_cofins=cred_cofins,
            cred_cofins_atz=cred_cofins_atz
        )
        resultados.append(resultado)
    return resultados


def agrupar_resultados_por_comp(resultados: list):
    resultados_agrupados = defaultdict(lambda: ExtractionResult("", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    for resultado in resultados:
        if resultados_agrupados[resultado.comp].comp == "":
            resultados_agrupados[resultado.comp].comp = resultado.comp
            resultados_agrupados[resultado.comp].selic = resultado.selic
        resultados_agrupados[resultado.comp].base_pis += resultado.base_pis
        resultados_agrupados[resultado.comp].base_cofins += resultado.base_cofins
        resultados_agrupados[resultado.comp].valor_pis += resultado.valor_pis
        resultados_agrupados[resultado.comp].valor_cofins += resultado.valor_cofins
        resultados_agrupados[resultado.comp].valor_icms += resultado.valor_icms
        resultados_agrupados[resultado.comp].base_pis_sem_icms += resultado.base_pis_sem_icms
        resultados_agrupados[resultado.comp].base_cofins_sem_icms += resultado.base_cofins_sem_icms
        resultados_agrupados[resultado.comp].selic = resultado.selic
        resultados_agrupados[resultado.comp].valor_pis_sem_icms += resultado.valor_pis_sem_icms
        resultados_agrupados[resultado.comp].valor_cofins_sem_icms += resultado.valor_cofins_sem_icms
        resultados_agrupados[resultado.comp].cred_pis += resultado.cred_pis
        resultados_agrupados[resultado.comp].cred_pis_atz += resultado.cred_pis_atz
        resultados_agrupados[resultado.comp].cred_cofins += resultado.cred_cofins
        resultados_agrupados[resultado.comp].cred_cofins_atz += resultado.cred_cofins_atz
    return list(resultados_agrupados.values())
