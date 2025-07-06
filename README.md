# 🤖 VibeCode Bot - Advanced AI Discord Code Generator

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue.svg)](https://discordpy.readthedocs.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Um bot Discord extremamente avançado que utiliza IA Google Gemini para gerar código completo, testar automaticamente e corrigir erros até entregar projetos perfeitos em formato ZIP.

## ✨ Características Principais

### 🧠 IA Avançada com Múltiplas Personas
- **7 Personas Especializadas**: Senior Developer, Code Reviewer, Debugger, Architect, Tester, Optimizer, Security Expert
- **Geração Inteligente**: Código completo e funcional baseado em descrições naturais
- **Análise Contextual**: Detecta automaticamente linguagem, tipo de projeto e complexidade

### 🔧 Sistema de Correção Automática
- **Testes Automatizados**: Execução segura e análise de sintaxe/lógica
- **Correção Inteligente**: Loop infinito de correção até código perfeito
- **Múltiplas Estratégias**: Conservative, Standard, Aggressive, Rewrite, Hybrid
- **Prevenção de Loops**: Sistema anti-travamento com mudanças drásticas

### 📦 Entrega Profissional
- **Projetos Completos**: Estrutura organizada com todos os arquivos necessários
- **Documentação Automática**: README detalhado, instruções de setup e execução
- **Empacotamento ZIP**: Entrega instantânea via Discord
- **Metadados Completos**: Informações de qualidade, testes e correções

### 🛡️ Segurança e Qualidade
- **Sandbox Seguro**: Execução isolada de código
- **Análise de Segurança**: Detecção de operações perigosas
- **Validação Completa**: Verificação de sintaxe, lógica e performance
- **Logging Avançado**: Monitoramento completo de todas as operações

## 🚀 Instalação Rápida

### 1. Pré-requisitos
```bash
# Python 3.7 ou superior
python --version

# Git (para clonar o repositório)
git --version
```

### 2. Clone e Configure
```bash
# Clone o repositório
git clone <repository-url>
cd vibecode_bot

# Execute o setup automático
python setup.py
```

### 3. Configure as APIs
Edite o arquivo `.env` criado:
```env
# Token do Discord Bot (Discord Developer Portal)
DISCORD_TOKEN=seu_token_discord_aqui

# Chave da API Gemini (Google AI Studio)
GEMINI_API_KEY=sua_chave_gemini_aqui
```

### 4. Execute o Bot
```bash
# Método 1: Script principal
python main.py

# Método 2: Script rápido
python run.py
```

## 📋 Configuração Detalhada

### Obtendo Token Discord
1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Crie uma nova aplicação
3. Vá para a seção "Bot" e crie um bot
4. Copie o token e cole no `.env`
5. Configure permissões necessárias:
   - Send Messages
   - Attach Files
   - Use Slash Commands
   - Read Message History

### Obtendo Chave Gemini
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova chave de API
3. Copie a chave e cole no `.env`

### Configuração Avançada
Edite `config/config.yaml` para personalizar:
```yaml
bot:
  command_prefix: "!"
  max_file_size_mb: 25

gemini:
  model: "gemini-1.5-pro"
  temperature: 0.7
  max_tokens: 8192

testing:
  max_execution_time: 30
  max_correction_attempts: 10
  sandbox_enabled: true
```

## 💡 Como Usar

### Comandos Principais
```
!code <descrição>     - Gera código baseado na descrição
!help                 - Mostra ajuda completa
!stats                - Estatísticas do bot
!status               - Status atual do bot
```

### Exemplos de Uso
```
!code crie um bot discord em python que responde "olá" quando alguém digita "oi"

!code faça um web scraper em python que coleta preços de produtos

!code crie uma calculadora simples em javascript com interface HTML

!code desenvolva um sistema de login em python com banco de dados SQLite

!code faça um jogo da velha em python com interface gráfica
```

### Linguagens Suportadas
- **Python** - Aplicações, bots, web scrapers, APIs
- **JavaScript** - Web apps, Node.js, React, APIs
- **Java** - Aplicações desktop, Spring Boot
- **C++** - Aplicações de performance, jogos
- **Go** - Microserviços, APIs, ferramentas CLI
- **Rust** - Aplicações de sistema, performance
- **HTML/CSS** - Páginas web, interfaces

## 🏗️ Arquitetura do Sistema

### Componentes Principais
```
vibecode_bot/
├── src/
│   ├── discord_bot.py      # Bot Discord principal
│   ├── gemini_ai.py        # Sistema de IA com personas
│   ├── code_tester.py      # Testes automatizados
│   ├── code_corrector.py   # Correção inteligente
│   ├── project_manager.py  # Gerenciamento de projetos
│   ├── config_manager.py   # Configurações
│   └── logger.py           # Sistema de logging
├── config/
│   └── config.yaml         # Configurações principais
├── logs/                   # Logs do sistema
├── temp/                   # Arquivos temporários
├── projects/               # Projetos gerados
└── main.py                 # Ponto de entrada
```

### Fluxo de Geração
1. **Recepção**: Usuário envia comando `!code`
2. **Análise**: IA analisa e detecta parâmetros
3. **Geração**: Gemini gera código com persona apropriada
4. **Teste**: Sistema executa e analisa código
5. **Correção**: Loop automático de correção se necessário
6. **Empacotamento**: Criação de projeto completo
7. **Entrega**: Envio de ZIP via Discord

### Personas de IA
- **Senior Developer**: Código limpo e profissional
- **Code Reviewer**: Análise de qualidade e bugs
- **Debugger**: Correção de erros específicos
- **Architect**: Estrutura e organização
- **Tester**: Casos de teste e validação
- **Optimizer**: Performance e eficiência
- **Security Expert**: Segurança e vulnerabilidades

## 🔧 Desenvolvimento

### Estrutura de Desenvolvimento
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Executar testes
python -m pytest tests/

# Verificar código
python -m pylint src/

# Formatar código
python -m black src/
```

### Adicionando Novas Funcionalidades
1. Crie módulos em `src/`
2. Adicione testes em `tests/`
3. Atualize configurações se necessário
4. Documente mudanças

### Logs e Debugging
```bash
# Logs em tempo real
tail -f logs/vibecodebot.log

# Logs de erro
tail -f logs/vibecodebot_errors.log

# Debug mode
LOG_LEVEL=DEBUG python main.py
```

## 📊 Monitoramento

### Métricas Disponíveis
- Total de requisições processadas
- Taxa de sucesso de geração
- Número de correções realizadas
- Tempo médio de processamento
- Uso de recursos do sistema

### Comandos de Status
```
!stats    # Estatísticas detalhadas
!status   # Status atual do bot
```

### Logs Estruturados
- **INFO**: Operações normais
- **WARNING**: Situações de atenção
- **ERROR**: Erros recuperáveis
- **CRITICAL**: Erros fatais

## 🛠️ Solução de Problemas

### Problemas Comuns

**Bot não conecta:**
```bash
# Verifique token Discord
echo $DISCORD_TOKEN

# Teste conectividade
python -c "import discord; print('Discord.py OK')"
```

**Erro de API Gemini:**
```bash
# Verifique chave API
echo $GEMINI_API_KEY

# Teste API
python -c "import google.generativeai as genai; print('Gemini OK')"
```

**Erro de permissões:**
- Verifique permissões do bot no Discord
- Confirme que o bot está no servidor
- Teste com comando simples primeiro

**Erro de dependências:**
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# Verificar versão Python
python --version  # Deve ser 3.7+
```

### Debug Avançado
```bash
# Modo debug completo
DEBUG=1 LOG_LEVEL=DEBUG python main.py

# Teste componentes individuais
python -c "from src.gemini_ai import get_gemini_ai; ai = get_gemini_ai(); print('AI OK')"
```

## 📈 Performance

### Otimizações Implementadas
- **Cache de IA**: Reutilização de respostas similares
- **Execução Assíncrona**: Processamento paralelo
- **Cleanup Automático**: Limpeza de arquivos temporários
- **Limitação de Rate**: Prevenção de spam

### Limites do Sistema
- **Arquivo máximo**: 25MB por projeto
- **Timeout execução**: 30 segundos
- **Tentativas correção**: 10 máximo
- **Cooldown usuário**: 30 segundos

## 🔒 Segurança

### Medidas de Segurança
- **Sandbox isolado** para execução de código
- **Filtros de segurança** para operações perigosas
- **Validação de entrada** em todos os comandos
- **Logs de auditoria** completos
- **Rate limiting** por usuário

### Operações Bloqueadas
- Acesso ao sistema de arquivos
- Conexões de rede não autorizadas
- Execução de comandos do sistema
- Importação de módulos perigosos

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: Use o GitHub Issues para bugs e sugestões
- **Documentação**: Consulte este README e comentários no código
- **Logs**: Sempre inclua logs relevantes ao reportar problemas

## 🎯 Roadmap

### Próximas Funcionalidades
- [ ] Suporte a mais linguagens de programação
- [ ] Interface web para configuração
- [ ] Sistema de plugins
- [ ] Integração com GitHub
- [ ] Análise de código existente
- [ ] Geração de testes automatizados
- [ ] Suporte a bancos de dados
- [ ] Deploy automático

### Melhorias Planejadas
- [ ] Cache inteligente de gerações
- [ ] Métricas avançadas
- [ ] Interface de administração
- [ ] Backup automático de projetos
- [ ] Integração com CI/CD

---

**Desenvolvido com ❤️ e muita ☕ para a comunidade de desenvolvedores**

*VibeCode Bot - Transformando ideias em código desde 2024* 🚀