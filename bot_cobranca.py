from datetime import datetime, timedelta
import json
from mcp_client_oficial import MCPClientSync

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

# Cliente MCP global - inicializado no main()
mcp_client = None

def analisar_mensagem_com_ia(texto_resposta, telefone, nome_cliente, tipo_cobranca):
    """
    Substitui a função chamar_mcp_server() usando MCP Client oficial
    """
    global mcp_client
    
    if not mcp_client:
        print('❌ MCP Client não inicializado')
        return None
    
    try:
        print('🧠 Analisando mensagem com IA via MCP...')
        
        # Usar MCP Client para análise
        resultado = mcp_client.analisar_mensagem(
            texto=texto_resposta,
            nome_cliente=nome_cliente, 
            tipo_cobranca=tipo_cobranca,
            historico=""  # Por enquanto vazio, depois podemos adicionar histórico
        )
        
        if resultado:
            print('✅ MCP retornou análise com sucesso')
            return resultado
        else:
            print('⚠️ MCP retornou resultado vazio')
            return None
            
    except Exception as e:
        print(f'❌ Erro ao conectar com MCP: {e}')
        return None

def executar_acao(analise, cliente):
    """
    Executa ação baseada na análise da IA
    Adaptado para trabalhar com resposta MCP
    """
    if not analise:
        print('❌ Sem análise para executar')
        return
    
    acao = analise.get('acao')
    intencao = analise.get('intencao') 
    confianca = analise.get('confianca', 0)
    mensagem_sugerida = analise.get('mensagem_sugerida', '')

    print(f'\n📊 ANÁLISE IA:')
    print(f'   Intenção: {intencao}')
    print(f'   Confiança: {confianca:.1%}')
    print(f'   Ação: {acao}')

    # Mapear ações da IA para ações do bot
    if acao == 'agradecer_confirmar':
        enviar_resposta(cliente['telefone'], mensagem_sugerida)
        print("✅ Agradecimento enviado - aguardando confirmação de pagamento")
    
    elif acao == 'enviar_opcoes_negociacao':
        enviar_resposta(cliente['telefone'], mensagem_sugerida)
        print("💰 Opções de negociação enviadas")
        
    elif acao == "reenviar_boleto":
        # Adicionar link do boleto à mensagem
        mensagem_completa = f"{mensagem_sugerida}\n\nSeu boleto: {cliente['link_boleto']}"
        enviar_resposta(cliente["telefone"], mensagem_completa)
        print("📄 Boleto reenviado")
        
    elif acao == "encaminhar_suporte":
        enviar_resposta(cliente["telefone"], mensagem_sugerida)
        print("👤 Caso encaminhado para suporte humano")
        
    elif acao == "oferecer_parcelamento":
        enviar_resposta(cliente["telefone"], mensagem_sugerida)
        print("💳 Opções de parcelamento oferecidas")
        
    elif acao == "solicitar_comprovante":
        enviar_resposta(cliente["telefone"], mensagem_sugerida)
        print("📋 Comprovante de pagamento solicitado")
        
    elif acao == "explicar_divida":
        mensagem_completa = f"{mensagem_sugerida}\n\nDetalhes: {cliente['tipo_cobranca']} - Venc: {cliente['vencimento'].strftime('%d/%m/%Y')}"
        enviar_resposta(cliente["telefone"], mensagem_completa)
        print("📝 Explicação da dívida enviada")
        
    else:  # resposta_generica ou ação não mapeada
        enviar_resposta(cliente["telefone"], mensagem_sugerida)
        print("🤖 Resposta genérica enviada - pode precisar de humano")

def enviar_resposta(telefone, mensagem):
    """
    Simula envio de mensagem WhatsApp
    """
    print(f"📤 ENVIADO para {telefone}:")
    print(f"   {mensagem}")

def simular_resposta_cliente(cliente, resposta_simulada):
    """
    Simula resposta do cliente e processa com IA
    """
    print(f"\n📨 RESPOSTA RECEBIDA de {cliente['nome']} ({cliente['telefone']}):")
    print(f"   '{resposta_simulada}'")
    
    # Analisar com IA via MCP
    analise = analisar_mensagem_com_ia(
        resposta_simulada, 
        cliente["telefone"], 
        cliente["nome"], 
        cliente["tipo_cobranca"]
    )
    
    # Executar ação baseada na análise
    executar_acao(analise, cliente)

def executar_disparos():
    """
    Função original de disparo automático
    """
    hoje_data = datetime.now().date()
    print(f"🗓️  Verificando disparos para {hoje_data.strftime('%d/%m/%Y')}")
    print("=" * 50)

    for cliente in clientes:
        venc = cliente['vencimento'].date()
        tipo = cliente['tipo_cobranca']
        nome = cliente['nome']  
        link = cliente['link_boleto']

        if venc == hoje_data + timedelta(days=1):  # D-1
            msg = mensagens[tipo]['D-1'].format(nome=nome, link_boleto=link)
            print(f'📤 [D-1] ENVIADO para {cliente["telefone"]}: {msg}')
        elif venc == hoje_data - timedelta(days=1):  # D+1
            msg = mensagens[tipo]['D+1'].format(nome=nome, link_boleto=link)
            print(f'📤 [D+1] ENVIADO para {cliente["telefone"]}: {msg}')
        else:
            print(f'⏸️  Nenhum disparo para {nome} hoje')

def main():
    """
    Função principal com integração MCP
    """
    global mcp_client
    
    print("🤖 BOT DE COBRANÇA - INTEGRAÇÃO MCP OFICIAL")
    print("=" * 50)
    
    # 1. Inicializar cliente MCP
    print("🔄 Inicializando cliente MCP...")
    mcp_client = MCPClientSync("mcp_server_openai.py")
    
    # 2. Conectar com MCP Server
    if not mcp_client.conectar():
        print("❌ Falha ao conectar com MCP Server")
        print("   Verifique se o arquivo mcp_server_openai.py existe")
        print("   Verifique se OPENAI_API_KEY está configurada no .env")
        return
    
    try:
        # 3. Executar disparos normais
        print("\n1️⃣ DISPAROS AUTOMÁTICOS:")
        executar_disparos()
        
        print("\n2️⃣ SIMULANDO RESPOSTAS DOS CLIENTES COM IA:")
        print("=" * 50)
        
        # 4. Simulação 1: Cliente disse que pagou
        print("\n🧪 TESTE 1 - Confirmação de Pagamento:")
        simular_resposta_cliente(clientes[0], "Oi, já paguei ontem via PIX")
        
        print("\n" + "-" * 30)
        
        # 5. Simulação 2: Cliente quer negociar  
        print("\n🧪 TESTE 2 - Solicitação de Negociação:")
        simular_resposta_cliente(clientes[1], "Quero negociar um desconto")
        
        print("\n" + "-" * 30)
        
        # 6. Simulação 3: Cliente não recebeu boleto
        print("\n🧪 TESTE 3 - Solicitação de Reenvio:")
        simular_resposta_cliente(clientes[0], "Não recebi o boleto, pode enviar?")
        
        print("\n" + "-" * 30)
        
        # 7. Simulação 4: Cliente com dificuldades
        print("\n🧪 TESTE 4 - Dificuldade Financeira:")
        simular_resposta_cliente(clientes[1], "Estou desempregado, podem aguardar uns dias?")
        
    finally:
        # 8. Desconectar MCP Client
        print(f"\n🔌 Desconectando cliente MCP...")
        if mcp_client:
            mcp_client.desconectar()
        
        print("✅ Bot finalizado com sucesso!")

if __name__ == "__main__":
    main()