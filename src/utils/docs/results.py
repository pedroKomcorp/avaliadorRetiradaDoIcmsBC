from dataclasses import dataclass


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

    def print_pis_info(self):
        print(f"Competência: {self.comp}")
        print(f"Base PIS: {self.base_pis}")
        print(f"Valor PIS: {self.valor_pis}")
        print(f"Valor Icms: {self.valor_icms}")
        print(f"Base PIS sem ICMS: {self.base_pis_sem_icms}")
        print(f"Valor PIS sem ICMS: {self.valor_pis_sem_icms}")
        print(f"Crédito PIS: {self.cred_pis}")
        print(f"Crédito PIS atualizado: {self.cred_pis_atz}")
        print(f"Data de atualização SELIC: {self.date_atz_selic}")
        print(f"SELIC: {self.selic}")

    def print_cofins_info(self):
        print(f"Competência: {self.comp}")
        print(f"Base COFINS: {self.base_cofins}")
        print(f"Valor COFINS: {self.valor_cofins}")
        print(f"Valor Icms: {self.valor_icms}")
        print(f"Base COFINS sem ICMS: {self.base_cofins_sem_icms}")
        print(f"Valor COFINS sem ICMS: {self.valor_cofins_sem_icms}")
        print(f"Crédito COFINS: {self.cred_cofins}")
        print(f"Crédito COFINS atualizado: {self.cred_cofins_atz}")
        print(f"Data de atualização SELIC: {self.date_atz_selic}")
        print(f"SELIC: {self.selic}")
