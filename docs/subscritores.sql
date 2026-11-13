-- Base de dados dos alertas no WhatsApp: tabela `subscritores` no Supabase.
-- Como usar: no painel do Supabase, abrir "SQL Editor", colar este texto e carregar em "Run". Só uma vez.
-- As colunas são as mesmas da base local (plataforma/inscricoes.py).

create table if not exists public.subscritores (
  id               text primary key,                 -- identificador da inscrição
  criado_utc       text not null default '',         -- quando a pessoa se inscreveu
  nome             text not null default '',         -- nome (opcional)
  telefone         text not null default '',         -- número de WhatsApp, formato internacional sem "+" (258841234567)
  lugar            text not null default '',         -- bairro ou lugar escolhido
  lingua           text not null default 'pt',       -- pt, en ou fr
  sexo             text not null default '',         -- mulher, homem ou vazio (prefere não dizer)
  faixa_etaria     text not null default '',         -- menos_18, 18_29, 30_44, 45_59, 60_mais ou vazio
  profissao        text not null default '',         -- agricultor, pescador, comerciante, ... ou vazio
  consentimento    text not null default '',         -- quando marcou "Aceito"
  estado           text not null default 'activa',   -- activa ou removido
  boas_vindas_utc  text not null default '',         -- quando recebeu as boas-vindas
  removido_utc     text not null default '',         -- quando pediu para sair
  ultimo_envio_utc text not null default '',         -- quando recebeu o último alerta
  envios           text not null default '0'         -- quantos alertas recebeu
);

create index if not exists subscritores_telefone on public.subscritores (telefone);

-- Segurança: com Row Level Security ligado e sem nenhuma regra de acesso, ninguém lê nem escreve
-- pela internet com a chave pública. Só a chave de serviço (service_role), guardada nos segredos do
-- Streamlit e do GitHub, tem acesso. Nunca pôr a chave de serviço no código nem no repositório.
alter table public.subscritores enable row level security;

-- Versão 2 (2026-10-14): sexo, faixa etária, profissão e o registo dos envios por pessoa.
-- Numa tabela criada antes desta data, correr também estas linhas (não estragam nada se já existirem).
alter table public.subscritores add column if not exists sexo             text not null default '';  -- mulher, homem ou vazio
alter table public.subscritores add column if not exists faixa_etaria     text not null default '';  -- menos_18, 18_29, 30_44, 45_59, 60_mais
alter table public.subscritores add column if not exists profissao        text not null default '';  -- agricultor, pescador, ...
alter table public.subscritores add column if not exists ultimo_envio_utc text not null default '';  -- último alerta recebido
alter table public.subscritores add column if not exists envios           text not null default '0'; -- quantos alertas recebeu
