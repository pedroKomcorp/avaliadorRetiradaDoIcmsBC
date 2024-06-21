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
        if not self.selic_data[2019]:  # Check if data has not been fetched yet
            self.fetch_data()

        if ano not in self.selic_data or mes < 1 or mes > 12:
            raise ValueError("Ano ou mês inválido.")

        if len(self.selic_data[ano]) < mes:
            raise ValueError("Dados insuficientes para o ano/mês especificado.")

        month_data = self.selic_data[ano][mes - 1]  # Adjust for 0-based index
        return float(month_data.replace(',', '.')) / 100

