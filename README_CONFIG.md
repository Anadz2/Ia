# VibeCode Bot - Configuração com config.py

## 📋 Modificações Realizadas

Este bot foi modificado para usar `config.py` ao invés de arquivos `.env` e `config.yaml`, tornando-o mais compatível com Termux e mais fácil de configurar.

## 🔧 Configuração

### 1. Editar config.py

Abra o arquivo `config.py` e configure suas chaves:

```python
# Discord Bot Token (obtenha em: https://discord.com/developers/applications)
DISCORD_TOKEN = "seu_token_discord_aqui"

# Google Gemini API Key (obtenha em: https://makersuite.google.com/app/apikey)
GEMINI_API_KEY = "sua_chave_gemini_aqui"
```

### 2. Obter as Chaves

#### Discord Bot Token:
1. Acesse https://discord.com/developers/applications
2. Crie uma nova aplicação ou selecione uma existente
3. Vá para "Bot" no menu lateral
4. Copie o token e cole no `config.py`

#### Gemini API Key:
1. Acesse https://makersuite.google.com/app/apikey
2. Crie uma nova chave API
3. Copie a chave e cole no `config.py`

## 🚀 Instalação

### No Termux (Android):

```bash
# Instalar Python e pip
pkg update && pkg upgrade
pkg install python git

# Clonar/baixar o bot
cd ~
# (coloque os arquivos do bot aqui)

# Instalar dependências
pip install -r requirements.txt

# Configurar
nano config.py  # Edite com suas chaves

# Executar
python main.py
```

### No Linux/Ubuntu:

```bash
# Instalar dependências do sistema
sudo apt update
sudo apt install python3 python3-pip git

# Instalar dependências Python
pip3 install -r requirements.txt

# Configurar
nano config.py  # Edite com suas chaves

# Executar
python3 main.py
```

## 📁 Estrutura de Arquivos

```
vibecode_bot/
├── config.py              # ✅ Configurações principais (EDITE AQUI)
├── main.py                # ✅ Arquivo principal modificado
├── requirements.txt       # ✅ Dependências atualizadas
├── src/
│   ├── config_manager.py  # ✅ Gerenciador modificado
│   ├── discord_bot.py     # Código do bot Discord
│   ├── gemini_ai.py       # Integração com Gemini
│   └── ...                # Outros módulos
├── logs/                  # Logs do bot
├── temp/                  # Arquivos temporários
└── projects/              # Projetos gerados
```

## 🔍 Verificação da Configuração

Execute este comando para verificar se tudo está configurado:

```bash
python config.py
```

Você deve ver:
- ✅ Configurações válidas!
- Lista de diretórios configurados
- Status do ambiente (Termux ou padrão)

## 🐛 Solução de Problemas

### Erro: "config.py file not found"
- Certifique-se de que o arquivo `config.py` está na raiz do projeto
- Verifique se você está executando o bot do diretório correto

### Erro: "DISCORD_TOKEN não foi configurado"
- Abra `config.py` e substitua `"your_discord_bot_token_here"` pelo seu token real

### Erro: "GEMINI_API_KEY não foi configurado"
- Abra `config.py` e substitua `"your_gemini_api_key_here"` pela sua chave real

### Problemas no Termux:
- Execute: `pkg install python clang`
- Se houver erro com alguma dependência, tente: `pip install --no-deps nome_do_pacote`

## 📱 Específico para Termux

O bot detecta automaticamente se está rodando no Termux e ajusta:
- Caminhos de diretórios para o home do usuário
- Configurações específicas do ambiente Termux
- Compatibilidade com o sistema de arquivos do Android

## 🎯 Comandos do Bot

Após configurar e executar, use no Discord:

- `!code <linguagem> <descrição>` - Gerar código
- `!fix <código>` - Corrigir código
- `!explain <código>` - Explicar código
- `!help` - Ajuda completa

## 📝 Notas Importantes

1. **Nunca compartilhe** seu `config.py` com tokens reais
2. Mantenha suas chaves API seguras
3. O bot criará automaticamente os diretórios necessários
4. Logs são salvos em `logs/` para debug
5. Projetos gerados ficam em `projects/`

## 🔄 Atualizações

Para atualizar configurações sem reiniciar o bot, você pode modificar `config.py` e o bot recarregará automaticamente em alguns casos. Para mudanças críticas, reinicie o bot.