from datetime import datetime, timedelta
import requests
import json

hoje = datetime.now()

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

def chamar_mcp_server(texto_resposta, telefone,nome_cliente,tipo_cobranca): 
    url = "http://localhost:8000/analisar"

    payload = {
        "texto": texto_resposta,
        "telefone": telefone,
        "nome_cliente": nome_cliente,
        "tipo_cobranca": tipo_cobranca
    }
    try:
        print('chmando mcpserver...')
        response = requests.post(url, json=payload,timeout=5)
        if response.status_code == 200:
            print('mcpserver retornou sucesso')
            return response.json()
        else:
            print('mcpserver retornou erro:', response.status_code)
            print(f'erro no mcpserver: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print('erro ao conectar com mcpserver:', e)
        return None

def executar_acao(analise,cliente):
    if not analise:
        print('sem analise para executar')
        return
    
    acao = analise.get('acao')
    dados = analise.get('dados_acao', {})
    intencao = analise.get('intencao')
    confianca = analise.get('confianca', 0)

    print(f'ANALISE:')
    print(f'intencao: {intencao}')
    print(f'confianca: {confianca}')
    print(f'acao: {acao}')

    if acao == 'agradecer_confirmar':
        enviar_resposta(cliente['telefone'],dados['mensagem'])
        print("Agradecimento enviado - aguardando confirmação de pagamento")
    
    elif acao == 'enviar_opcoes_negociacao':
        enviar_resposta(cliente['telefone'], dados['mensagem'])
        if dados.get('encaminhar_para_vendas'):
            print('encaminhado para vendas')
    elif acao == "reenviar_boleto":
        mensagem_completa = f"{dados['mensagem']} {cliente['link_boleto']}"
        enviar_resposta(cliente["telefone"], mensagem_completa)
        print("boleto reenviado")
    elif acao == "encaminhar_suporte":
        enviar_resposta(cliente["telefone"], dados["mensagem"])
        if dados.get("criar_ticket"):
            print(f"ticket criado - prioridade: {dados.get('prioridade', 'normal')}")
    
    elif acao == "resposta_generica":
        enviar_resposta(cliente["telefone"], dados["mensagem"])
        if dados.get("encaminhar_humano"):
            print("caso encaminhado para atendimento humano")

def enviar_resposta(telefone, mensagem):
    print(f"ENVIADO para {telefone}: {mensagem}")

def simular_resposta_cliente(cliente, resposta_simulada):
    print(f"\nRESPOSTA RECEBIDA de {cliente['nome']} ({cliente['telefone']}):")
    print(f"   '{resposta_simulada}'")
    analise = chamar_mcp_server(
        resposta_simulada, 
        cliente["telefone"], 
        cliente["nome"], 
        cliente["tipo_cobranca"]
    )
    executar_acao(analise, cliente)
def executar_disparos():
    """
    Função original de disparo automático
    """
    hoje = datetime.now().date()
    print(f"🗓️  Verificando disparos para {hoje.strftime('%d/%m/%Y')}")
    print("=" * 50)

    for cliente in clientes:
        venc = cliente['vencimento'].date()
        tipo = cliente['tipo_cobranca']
        nome = cliente['nome']  
        link = cliente['link_boleto']

        if venc == hoje + timedelta(days=1):  # D-1
            msg = mensagens[tipo]['D-1'].format(nome=nome, link_boleto=link)
            print(f'📤 [D-1] ENVIADO para {cliente["telefone"]}: {msg}')
        elif venc == hoje - timedelta(days=1):  # D+1
            msg = mensagens[tipo]['D+1'].format(nome=nome, link_boleto=link)
            print(f'📤 [D+1] ENVIADO para {cliente["telefone"]}: {msg}')
        else:
            print(f'⏸️  Nenhum disparo para {nome} hoje')


def main():
    print("🤖 BOT DE COBRANÇA - TESTE INTEGRADO")
    print("=" * 50)
    
    # 1. Executar disparos normais
    executar_disparos()
    
    print("\n")
    print("SIMULANDO RESPOSTAS DOS CLIENTES")
    
    # Simulação 1: Cliente disse que pagou
    simular_resposta_cliente(clientes[0], "Oi, já paguei ontem via PIX")
    
    print("\n" + "-" * 30)
    
    # Simulação 2: Cliente quer negociar  
    simular_resposta_cliente(clientes[1], "Quero negociar um desconto")
    
    print("\n" + "-" * 30)
    
    # Simulação 3: Cliente não recebeu boleto
    simular_resposta_cliente(clientes[0], "Não recebi o boleto, pode enviar?")

if __name__ == "__main__":
    main()