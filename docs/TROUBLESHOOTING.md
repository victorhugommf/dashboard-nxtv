# Troubleshooting - Dashboard Desktop

## 🐛 Problemas Comuns e Soluções

### Erro: "Unexpected token 'N', ...NaN... is not valid JSON"

**Problema:** A API estava retornando valores `NaN` (Not a Number) do pandas, que não são válidos em JSON.

**Causa:** Dados faltantes ou nulos na planilha do Google Sheets eram convertidos para `NaN` pelo pandas.

**Solução Implementada:**
- Adicionada função `safe_value()` para tratar valores NaN/None
- Implementada limpeza de dados antes de `value_counts()`
- Substituição de valores NaN por strings vazias ou null

**Código da Solução:**
```python
def safe_value(self, value, default=''):
    """Converte valores NaN/None para string segura"""
    if pd.isna(value) or value is None:
        return default
    return str(value) if value != '' else default
```

### Erro: "Planilha não acessível"

**Problema:** Dashboard não consegue acessar a planilha do Google Sheets.

**Possíveis Causas:**
1. Planilha não está pública
2. ID da planilha incorreto
3. Problemas de rede

**Soluções:**
1. Verificar se a planilha está configurada como "Qualquer pessoa com o link pode visualizar"
2. Confirmar o ID da planilha na URL
3. Testar acesso manual: `https://docs.google.com/spreadsheets/d/ID_DA_PLANILHA/export?format=csv&gid=0`

### Erro: "Colunas obrigatórias não encontradas"

**Problema:** A planilha não contém as colunas esperadas pelo sistema.

**Colunas Esperadas:**
- `name` ou `nome` (obrigatório)
- `email` (obrigatório)
- `phone` ou `telefone`
- `city` ou `cidade`
- `isp` ou `provedor`
- `utm_medium` ou `canal`
- `received_at` ou `data_recebimento`

**Solução:** Ajustar os cabeçalhos da planilha ou modificar o mapeamento no código.

## 🔧 Desenvolvimento

### Hot Reload não funciona

**Problema:** Mudanças no código não são refletidas automaticamente.

**Soluções:**
1. Verificar se está usando o modo desenvolvimento: `./scripts/dev.sh`
2. Confirmar que os volumes estão montados corretamente
3. Verificar logs: `docker compose -f docker-compose.dev.yml logs -f frontend-dev`

### Container não inicia

**Problema:** Containers falham ao iniciar.

**Diagnóstico:**
```bash
# Verificar status
docker compose -f docker-compose.dev.yml ps

# Ver logs
docker compose -f docker-compose.dev.yml logs

# Reconstruir se necessário
docker compose -f docker-compose.dev.yml build --no-cache
```

## 📊 Dados

### Dados não aparecem no dashboard

**Checklist:**
1. ✅ API está respondendo: `curl http://localhost:5001/api/health`
2. ✅ Planilha está acessível: `curl "https://docs.google.com/spreadsheets/d/ID/export?format=csv&gid=0"`
3. ✅ Dados têm formato correto
4. ✅ Colunas obrigatórias existem

### Performance lenta

**Otimizações:**
1. Reduzir quantidade de dados na planilha
2. Usar cache no backend (futuro)
3. Implementar paginação (futuro)

## 🚀 Deploy

### Modo Produção vs Desenvolvimento

**Desenvolvimento (Hot Reload):**
```bash
./scripts/dev.sh
```
- Mudanças instantâneas
- Debug ativo
- Volumes montados

**Produção (Otimizado):**
```bash
./scripts/prod.sh
```
- Build otimizado
- Nginx
- Performance máxima

## 📞 Suporte

Para problemas não listados aqui:
1. Verificar logs dos containers
2. Testar endpoints da API individualmente
3. Confirmar configuração da planilha
4. Verificar conectividade de rede