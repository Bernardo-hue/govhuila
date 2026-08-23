# Governo Digital — Protótipo Streamlit

Protótipo de sistema de gestão documental e tramitação electrónica para um Governo Provincial.

## Funcionalidades

- Login e logout.
- Painel de gestão.
- Digitalização/registo de documentos.
- Upload de PDF, imagens, DOCX e XLSX.
- Indexação e pesquisa por metadados.
- Organização por categoria.
- Registo e acompanhamento de processos.
- Tramitação entre secretarias e municípios.
- Base de dados SQLite.
- Registo básico de auditoria.

## Executar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Conta de demonstração:

- utilizador: `admin`
- palavra-passe: `admin123`

## Deploy no Streamlit Community Cloud

1. Crie um repositório no GitHub.
2. Envie `app.py`, `requirements.txt` e `README.md`.
3. No Streamlit Community Cloud, escolha o repositório.
4. Defina `app.py` como ficheiro principal.
5. Faça o deploy.

## Atenção para produção

Este é um protótipo. Para um sistema governamental real, recomenda-se:

- PostgreSQL em vez de SQLite.
- Armazenamento de ficheiros em object storage.
- Hash de passwords com Argon2 ou bcrypt.
- Gestão de utilizadores e perfis/permissões.
- HTTPS obrigatório.
- MFA.
- Criptografia de dados sensíveis.
- Backups automáticos e política de retenção.
- Auditoria imutável.
- OCR para documentos digitalizados.
- Assinatura digital.
- Workflow configurável por secretaria.
- Antivírus/validação de uploads.
- Limites de tamanho e tipos de ficheiro.
- Controlo de acesso por órgão/município.
- Testes e revisão de segurança antes da entrada em produção.
