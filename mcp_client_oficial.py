# mcp_client_oficial.py
import asyncio
import json
import subprocess
import sys
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any
import os

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
            print(f"🔄 Conectando com MCP Server: {server_path}")
            
            # Usar AsyncExitStack como na documentação oficial
            self.exit_stack = AsyncExitStack()
            
            # Conectar usando stdio_client com StdioServerParameters
            server_params = StdioServerParameters(
                command=f"{sys.executable} {server_path}",  # STRING, não lista!
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
            print(f"🧠 Analisando mensagem com IA via MCP...")
            
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
                        analise = json.loads(resposta_texto)
                        
                        print(f"✅ Análise IA concluída:")
                        print(f"   Intenção: {analise.get('intencao', 'N/A')}")
                        print(f"   Sentimento: {analise.get('sentimento', 'N/A')}")
                        print(f"   Confiança: {analise.get('confianca', 0):.1%}")
                        
                        return analise
            
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
    """Wrapper síncrono seguindo padrão oficial"""
    
    def __init__(self, server_path: str = "mcp_server_openai.py"):
        self.client = MCPClientCobranca()
        self.server_path = server_path
        self.loop = None
    
    def conectar(self) -> bool:
        """Conecta de forma síncrona"""
        try:
            # Criar novo loop de eventos
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Conectar usando método oficial
            resultado = self.loop.run_until_complete(
                self.client.conectar(self.server_path)
            )
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro conexão síncrona: {e}")
            return False
    
    def analisar_mensagem(
        self, 
        texto: str, 
        nome_cliente: str, 
        tipo_cobranca: str, 
        historico: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Analisa mensagem de forma síncrona"""
        
        if not self.loop:
            print("❌ Cliente não conectado")
            return None
        
        try:
            resultado = self.loop.run_until_complete(
                self.client.analisar_mensagem(
                    texto, nome_cliente, tipo_cobranca, historico
                )
            )
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro análise síncrona: {e}")
            return None
    
    def desconectar(self):
        """Desconecta de forma síncrona"""
        try:
            if self.loop and self.client:
                self.loop.run_until_complete(
                    self.client.desconectar()
                )
                self.loop.close()
                self.loop = None
                
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
        
    finally:
        await client.desconectar()

if __name__ == "__main__":
    print("🧪 TESTANDO MCP CLIENT OFICIAL")
    print("=" * 40)
    asyncio.run(testar_mcp_oficial())