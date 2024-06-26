from xml.dom import minidom


files = []

for file in files:
    with open(file, 'r') as f:
        xml = minidom.parse(f)
        nome = xml.getElementsByTagName("")

# Valor produto - <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" Id="NFe42230700209895000250550010003851571872969550"><det nItem="1"><prod><vProd>