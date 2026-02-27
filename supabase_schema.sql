-- ============================================================
-- Supabase Schema — Health Coaching Platform
-- Run this in your Supabase project: SQL Editor → New Query
-- ============================================================

-- Clients table
create table if not exists clients (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    pin         text not null unique,
    targets     jsonb not null default '{}',
    active      boolean not null default true,
    created_at  timestamptz not null default now()
);

-- Dashboard cache (processed CSV per client)
create table if not exists dashboard_cache (
    client_id   uuid primary key references clients(id) on delete cascade,
    csv_data    text not null,
    updated_at  timestamptz not null default now()
);

-- Coach annotations
create table if not exists annotations (
    id          uuid primary key default gen_random_uuid(),
    client_id   uuid not null references clients(id) on delete cascade,
    date        date not null,
    note        text not null,
    created_at  timestamptz not null default now()
);

-- Vitamin / mineral logs
create table if not exists vitamin_logs (
    id          uuid primary key default gen_random_uuid(),
    client_id   uuid not null references clients(id) on delete cascade,
    date        date not null,
    vitamin_d   numeric default 0,
    vitamin_c   numeric default 0,
    vitamin_b12 numeric default 0,
    omega3      numeric default 0,
    magnesium   numeric default 0,
    zinc        numeric default 0,
    iron        numeric default 0,
    other       text default '',
    notes       text default '',
    created_at  timestamptz not null default now(),
    unique (client_id, date)
);

-- ============================================================
-- Storage bucket for XML exports
-- Run in Supabase Dashboard → Storage → New bucket
-- Name: exports
-- Public: false
-- ============================================================

-- Row Level Security (RLS) — disable for now, enable when you add proper auth
alter table clients       disable row level security;
alter table dashboard_cache disable row level security;
alter table annotations   disable row level security;
alter table vitamin_logs  disable row level security;
