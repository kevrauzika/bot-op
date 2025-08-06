# mcp_client_oficial.py
import asyncio
import json
import subprocess
import sys
import os
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

class MCPClientCobranca:
    """Cliente MCP oficial seguindo documentação Anthropic"""
    
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.connected = False
    
    async def conectar(self, server_path: str = "mcp_server_openai.py"):
        """Conecta com o MCP Server seguindo padrão oficial"""
        try:
            # Verificar se arquivo do servidor existe
            if not os.path.exists(server_path):
                print(f"❌ Servidor MCP não encontrado: {server_path}")
                return False
            
            print(f"🔄 Conectando com MCP Server: {server_path}")
            
            # Usar AsyncExitStack como na documentação oficial
            self.exit_stack = AsyncExitStack()
            
            # Conectar usando stdio_client com StdioServerParameters
            # CORREÇÃO: command deve ser uma lista, não string
            server_params = StdioServerParameters(
                command=[sys.executable, server_path],  # LISTA ao invés de STRING
                env=os.environ.copy()
            )
            
            transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            # Criar sessão usando transporte
            read_stream, write_stream = transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Inicializar sessão
            await self.session.initialize()
            
            # Listar ferramentas disponíveis
            tools_response = await self.session.list_tools()
            tools = tools_response.tools
            
            self.connected = True
            print(f"✅ Conectado com MCP Server!")
            print(f"🛠️  Ferramentas disponíveis: {len(tools)}")
            
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar MCP Server: {e}")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Verifique se OPENAI_API_KEY está configurada")
            self.connected = False
            return False
    
    async def analisar_mensagem(
        self, 
        texto: str, 
        nome_cliente: str, 
        tipo_cobranca: str, 
        historico: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Analisa mensagem usando MCP Server"""
        
        if not self.connected or not self.session:
            print("❌ MCP Server não conectado")
            return None
        
        try:
            # Chamar ferramenta específica do MCP Server
            resultado = await self.session.call_tool(
                "analisar_mensagem_cobranca",
                {
                    "texto": texto,
                    "nome_cliente": nome_cliente,
                    "tipo_cobranca": tipo_cobranca,
                    "historico": historico
                }
            )
            
            # Extrair conteúdo da resposta
            if resultado and resultado.content:
                # Pegar o primeiro conteúdo de texto
                for content in resultado.content:
                    if hasattr(content, 'text'):
                        resposta_texto = content.text
                        
                        try:
                            analise = json.loads(resposta_texto)
                            
                            # Validar campos obrigatórios
                            campos_obrigatorios = ["intencao", "acao", "confianca", "mensagem_sugerida"]
                            for campo in campos_obrigatorios:
                                if campo not in analise:
                                    print(f"⚠️ Campo ausente na resposta IA: {campo}")
                                    if campo in ["intencao", "acao"]:
                                        analise[campo] = "nao_identificada"
                                    elif campo == "confianca":
                                        analise[campo] = 0.5
                                    else:
                                        analise[campo] = f"Resposta para {nome_cliente}"
                            
                            return analise
                            
                        except json.JSONDecodeError as je:
                            print(f"❌ Erro ao parsear JSON da IA: {je}")
                            print(f"   Resposta bruta: {resposta_texto[:200]}...")
                            return None
            
            print("⚠️ Resposta vazia do MCP Server")
            return None
            
        except Exception as e:
            print(f"❌ Erro na análise MCP: {e}")
            print(f"   Tipo: {type(e).__name__}")
            return None
    
    async def desconectar(self):
        """Desconecta do MCP Server"""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
            
            self.connected = False
            self.session = None 
            self.exit_stack = None
            print("🔌 Desconectado do MCP Server")
            
        except Exception as e:
            print(f"⚠️ Erro ao desconectar: {e}")

# Wrapper síncrono para usar no bot
class MCPClientSync:
    """Wrapper síncrono seguindo padrão oficial - MELHORADO"""
    
    def __init__(self, server_path: str = "mcp_server_openai.py"):
        self.client = MCPClientCobranca()
        self.server_path = server_path
        self.loop = None
        self.connected = False
    
    def conectar(self) -> bool:
        """Conecta de forma síncrona com melhor tratamento de erro"""
        try:
            # Verificar se arquivo existe antes de tentar conectar
            if not os.path.exists(self.server_path):
                print(f"❌ Arquivo do servidor não encontrado: {self.server_path}")
                return False
            
            # Criar novo loop de eventos
            try:
                # Tentar pegar loop existente
                self.loop = asyncio.get_event_loop()
                if self.loop.is_closed():
                    raise RuntimeError("Loop fechado")
            except RuntimeError:
                # Criar novo loop se necessário
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            # Conectar usando método oficial
            resultado = self.loop.run_until_complete(
                self.client.conectar(self.server_path)
            )
            
            self.connected = resultado
            return resultado
            
        except Exception as e:
            print(f"❌ Erro conexão síncrona: {e}")
            print(f"   Tipo: {type(e).__name__}")
            return False
    
    def analisar_mensagem(
        self, 
        texto: str, 
        nome_cliente: str, 
        tipo_cobranca: str, 
        historico: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Analisa mensagem de forma síncrona com fallbacks"""
        
        if not self.connected or not self.loop:
            print("❌ Cliente MCP não conectado")
            return self._criar_resposta_fallback(nome_cliente, "cliente_desconectado")
        
        try:
            resultado = self.loop.run_until_complete(
                self.client.analisar_mensagem(
                    texto, nome_cliente, tipo_cobranca, historico
                )
            )
            
            if resultado:
                return resultado
            else:
                print("⚠️ IA retornou resultado vazio, usando fallback")
                return self._criar_resposta_fallback(nome_cliente, "resposta_vazia")
            
        except Exception as e:
            print(f"❌ Erro análise síncrona: {e}")
            return self._criar_resposta_fallback(nome_cliente, "erro_analise")
    
    def _criar_resposta_fallback(self, nome_cliente: str, motivo: str) -> Dict[str, Any]:
        """Cria resposta de fallback quando IA falha"""
        fallbacks = {
            "cliente_desconectado": {
                "intencao": "nao_identificada",
                "sentimento": "neutro",
                "urgencia": "alta",
                "acao": "encaminhar_suporte",
                "confianca": 0.1,
                "explicacao": "Cliente MCP desconectado",
                "mensagem_sugerida": f"Olá {nome_cliente}, nossa equipe entrará em contato em breve."
            },
            "resposta_vazia": {
                "intencao": "nao_identificada", 
                "sentimento": "neutro",
                "urgencia": "media",
                "acao": "resposta_generica",
                "confianca": 0.2,
                "explicacao": "IA retornou resposta vazia",
                "mensagem_sugerida": f"Olá {nome_cliente}, recebi sua mensagem e vou analisar."
            },
            "erro_analise": {
                "intencao": "nao_identificada",
                "sentimento": "neutro", 
                "urgencia": "alta",
                "acao": "encaminhar_suporte",
                "confianca": 0.1,
                "explicacao": "Erro durante análise da IA",
                "mensagem_sugerida": f"Olá {nome_cliente}, vou encaminhar sua solicitação para nossa equipe."
            }
        }
        
        return fallbacks.get(motivo, fallbacks["erro_analise"])
    
    def desconectar(self):
        """Desconecta de forma síncrona"""
        try:
            if self.loop and self.client and self.connected:
                self.loop.run_until_complete(
                    self.client.desconectar()
                )
                
                # Fechar loop se criamos um novo
                if not self.loop.is_running():
                    self.loop.close()
                    
                self.loop = None
                self.connected = False
                
        except Exception as e:
            print(f"⚠️ Erro desconexão síncrona: {e}")

# Teste oficial
async def testar_mcp_oficial():
    """Teste seguindo padrão da documentação oficial"""
    
    client = MCPClientCobranca()
    
    try:
        # Conectar
        conectado = await client.conectar("mcp_server_openai.py")
        if not conectado:
            print("❌ Falha na conexão, cancelando teste")
            return
        
        # Testar análise
        print(f"\n🧪 TESTE 1:")
        resultado = await client.analisar_mensagem(
            "Oi, já paguei ontem via PIX",
            "João Silva",
            "mensalidade"
        )
        
        if resultado:
            print(f"📊 Resultado:")
            print(f"   Intenção: {resultado.get('intencao')}")
            print(f"   Ação: {resultado.get('acao')}")
            print(f"   Mensagem: {resultado.get('mensagem_sugerida')}")
        
    finally:
        await client.desconectar()

def testar_mcp_sync():
    """Teste do wrapper síncrono"""
    print("🧪 TESTANDO MCP CLIENT SÍNCRONO")
    print("=" * 40)
    
    client = MCPClientSync("mcp_server_openai.py")
    
    try:
        # Conectar
        if not client.conectar():
            print("❌ Falha na conexão síncrona")
            return
        
        # Testar análise
        print(f"\n🧪 TESTE SÍNCRONO:")
        resultado = client.analisar_mensagem(
            "Quero negociar um desconto",
            "Maria Silva", 
            "mensalidade"
        )
        
        if resultado:
            print(f"📊 Resultado:")
            print(f"   Intenção: {resultado.get('intencao')}")
            print(f"   Ação: {resultado.get('acao')}")
            print(f"   Confiança: {resultado.get('confianca', 0):.1%}")
        
    finally:
        client.desconectar()

if __name__ == "__main__":
    print("🧪 TESTANDO MCP CLIENT OFICIAL CORRIGIDO")
    print("=" * 50)
    
    # Teste assíncrono
    asyncio.run(testar_mcp_oficial())
    
    print("\n" + "=" * 50)
    
    # Teste síncrono 
    testar_mcp_sync()