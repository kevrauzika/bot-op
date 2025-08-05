from datetime import datetime, timedelta

clientes = [
    {
        "nome": "João Silva",
        "telefone": "5599999999999",  # formato internacional
        "vencimento": datetime(2025, 8, 6),
        "tipo_cobranca": "mensalidade",
        "link_boleto": "https://exemplo.com/boleto/joao"
    },
    {
        "nome": "Maria Oliveira",
        "telefone": "5598888888888",
        "vencimento": datetime(2025, 8, 4),
        "tipo_cobranca": "renegociacao",
        "link_boleto": "https://exemplo.com/boleto/maria"
    }
]

mensagens = {
    "mensalidade": {
        "D-1": "Olá {nome}, sua mensalidade vence amanhã. Evite juros! Boleto: {link_boleto}",
        "D+1": "Olá {nome}, sua mensalidade venceu ontem. Regularize aqui: {link_boleto}"
    },
    "renegociacao": {
        "D-1": "Olá {nome}, seu acordo vence amanhã. Garanta os benefícios. Link: {link_boleto}",
        "D+1": "Olá {nome}, identificamos que seu acordo venceu ontem. Negocie agora: {link_boleto}"
    }
}

hoje = datetime.now()

for cliente in clientes:
    venc = cliente['vencimento'].date()
    tipo = cliente['tipo_cobranca']
    nome = cliente['nome']  
    link = cliente['link_boleto']

    if venc == hoje + timedelta(days=1): #D-1
        msg = mensagens[tipo]['D-1'].format(nome=nome, link_boleto=link)
        print(f'[D-1] enviar para {cliente["telefone"]}: {msg}')
    elif venc == hoje - timedelta(days=1): #D+1
        msg = mensagens[tipo]['D+1'].format(nome=nome, link_boleto=link)
        print(f'[D+1] enviar para {cliente["telefone"]}: {msg}')
    else:
        print(f'nenhum disparo para {nome} hoje')