# mcp_server_openai.py
import asyncio
import json
import os
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from openai import OpenAI

# Criar servidor MCP
app = Server("bot-cobranca-ia")

# Cliente OpenAI será inicializado quando necessário
client = None

def get_openai_client():
    """Inicializa cliente OpenAI apenas quando necessário"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY não configurada")
        client = OpenAI(api_key=api_key)
    return client

# Prompt sistema para análise de cobrança
SYSTEM_PROMPT = """
Você é um assistente especializado em análise de mensagens de cobrança.

Analise a mensagem do cliente e identifique:
1. INTENÇÃO principal
2. SENTIMENTO (positivo/neutro/negativo)
3. URGÊNCIA (baixa/média/alta)
4. AÇÃO recomendada

INTENÇÕES possíveis:
- pagamento_realizado: cliente diz que já pagou
- negociacao: quer negociar, parcelar, desconto
- solicitar_boleto: não recebeu, perdeu o boleto
- nao_reconhece: não reconhece a dívida
- dificuldade_financeira: problemas para pagar
- contestacao: contesta valor ou cobrança
- prazo_adicional: pede mais tempo
- informacao: quer detalhes sobre a dívida
- nao_identificada: não conseguiu identificar

AÇÕES possíveis:
- agradecer_confirmar: agradecer e confirmar pagamento
- enviar_opcoes_negociacao: enviar opções de negociação
- reenviar_boleto: reenviar boleto/link
- encaminhar_suporte: encaminhar para suporte humano
- oferecer_parcelamento: oferecer parcelamento
- solicitar_comprovante: pedir comprovante de pagamento
- explicar_divida: explicar detalhes da dívida
- resposta_generica: resposta padrão + humano

Retorne SEMPRE um JSON válido com:
{
    "intencao": "uma das intenções listadas",
    "sentimento": "positivo/neutro/negativo", 
    "urgencia": "baixa/media/alta",
    "acao": "uma das ações listadas",
    "confianca": 0.95,
    "explicacao": "breve explicação da análise",
    "mensagem_sugerida": "mensagem personalizada para o cliente"
}
"""

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista as ferramentas disponíveis no MCP Server"""
    return [
        Tool(
            name="analisar_mensagem_cobranca",
            description="Analisa mensagem de cliente em processo de cobrança usando IA",
            inputSchema={
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto da mensagem do cliente"
                    },
                    "nome_cliente": {
                        "type": "string", 
                        "description": "Nome do cliente"
                    },
                    "tipo_cobranca": {
                        "type": "string",
                        "description": "Tipo de cobrança (mensalidade/renegociacao)"
                    },
                    "historico": {
                        "type": "string",
                        "description": "Histórico recente do cliente (opcional)",
                        "default": ""
                    }
                },
                "required": ["texto", "nome_cliente", "tipo_cobranca"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Executa a ferramenta solicitada"""
    
    if name == "analisar_mensagem_cobranca":
        # Extrair parâmetros
        texto = arguments.get("texto", "")
        nome_cliente = arguments.get("nome_cliente", "")
        tipo_cobranca = arguments.get("tipo_cobranca", "")
        historico = arguments.get("historico", "")
        
        # Criar prompt contextualizado
        user_prompt = f"""
        CLIENTE: {nome_cliente}
        TIPO COBRANÇA: {tipo_cobranca}
        HISTÓRICO: {historico}
        
        MENSAGEM DO CLIENTE:
        "{texto}"
        
        Analise esta mensagem e retorne o JSON com sua análise:
        """
        
        try:
            # Chamar OpenAI
            openai_client = get_openai_client()
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo econômico e rápido
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Consistência nas respostas
                max_tokens=500
            )
            
            # Extrair resposta
            resposta = response.choices[0].message.content.strip()
            
            # Tentar parsear JSON
            try:
                resultado = json.loads(resposta)
                
                # Validar campos obrigatórios
                campos_obrigatorios = ["intencao", "acao", "confianca", "mensagem_sugerida"]
                for campo in campos_obrigatorios:
                    if campo not in resultado:
                        resultado[campo] = "nao_identificada" if campo in ["intencao", "acao"] else 0.5
                
                return [TextContent(
                    type="text",
                    text=json.dumps(resultado, ensure_ascii=False, indent=2)
                )]
                
            except json.JSONDecodeError:
                # Fallback se JSON inválido
                resultado_fallback = {
                    "intencao": "nao_identificada",
                    "sentimento": "neutro",
                    "urgencia": "media", 
                    "acao": "resposta_generica",
                    "confianca": 0.3,
                    "explicacao": "Erro ao processar resposta da IA",
                    "mensagem_sugerida": f"Olá {nome_cliente}, vou encaminhar sua mensagem para nossa equipe."
                }
                
                return [TextContent(
                    type="text", 
                    text=json.dumps(resultado_fallback, ensure_ascii=False, indent=2)
                )]
                
        except Exception as e:
            # Fallback em caso de erro
            resultado_erro = {
                "intencao": "nao_identificada",
                "sentimento": "neutro",
                "urgencia": "alta",
                "acao": "encaminhar_suporte", 
                "confianca": 0.1,
                "explicacao": f"Erro na API OpenAI: {str(e)}",
                "mensagem_sugerida": f"Olá {nome_cliente}, nossa equipe entrará em contato em breve."
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(resultado_erro, ensure_ascii=False, indent=2)
            )]
    
    return [TextContent(type="text", text="Ferramenta não encontrada")]

# Executar servidor MCP
async def main():
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: Defina a variável OPENAI_API_KEY")
        print("   Exemplo: export OPENAI_API_KEY='sua-api-key-aqui'")
        return
    
    print("🤖 Iniciando MCP Server com OpenAI...")
    print("🔑 API Key encontrada")
    print("🚀 Servidor rodando - aguardando conexões MCP...")
    
    # Importar e executar servidor via stdio
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as streams:
        await app.run(*streams)

if __name__ == "__main__":
    asyncio.run(main())