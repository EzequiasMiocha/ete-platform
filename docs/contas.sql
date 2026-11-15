-- Contas da plataforma (entrar com nome de utilizador e senha): tabelas `contas` e `sessoes` no Supabase.
-- Como usar: no painel do Supabase, abrir "SQL Editor", colar este texto e carregar em "Run". Só uma vez,
-- no mesmo projecto da tabela `subscritores` (docs/subscritores.sql). As colunas são as de plataforma/contas.py.

create table if not exists public.contas (
  id                text primary key,                 -- identificador da conta
  criado_utc        text not null default '',         -- quando a conta foi criada
  utilizador        text not null unique,             -- nome de utilizador (minúsculas, sem espaços)
  nome              text not null default '',         -- nome completo (usado nas mensagens do WhatsApp)
  telefone          text not null default '',         -- número de WhatsApp, formato internacional sem "+" (opcional)
  lugar             text not null default '',         -- bairro ou lugar escolhido (opcional)
  lingua            text not null default 'pt',       -- pt, en ou fr
  senha             text not null default '',         -- impressão digital scrypt da senha (nunca a senha)
  recuperacao       text not null default '',         -- impressão digital scrypt do código de recuperação
  falhas            text not null default '0',        -- tentativas erradas seguidas
  bloqueado_ate     text not null default '',         -- conta fechada até (depois de 5 tentativas erradas)
  ultimo_acesso_utc text not null default '',         -- última entrada
  estado            text not null default 'activa'    -- activa
);
create index if not exists contas_telefone on public.contas (telefone);

create table if not exists public.sessoes (
  token      text primary key,                        -- impressão digital SHA-256 do bilhete guardado no aparelho
  conta      text not null,                           -- a conta (contas.id)
  criado_utc text not null default '',
  expira_utc text not null default ''                 -- 30 dias depois de entrar
);
create index if not exists sessoes_conta on public.sessoes (conta);

-- Segurança, como na tabela dos subscritores: Row Level Security ligado e nenhuma regra de acesso.
-- Ninguém lê nem escreve pela internet com a chave pública; só a chave de serviço (service_role),
-- guardada nos segredos do Streamlit, tem acesso. Nunca pôr a chave de serviço no código nem no repositório.
alter table public.contas enable row level security;
alter table public.sessoes enable row level security;
