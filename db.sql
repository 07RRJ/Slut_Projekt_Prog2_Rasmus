-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.cards (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  tier smallint NOT NULL DEFAULT 1 CHECK (tier >= 1 AND tier <= 6),
  base_attack smallint NOT NULL,
  base_health smallint NOT NULL,
  ability text,
  cost smallint NOT NULL DEFAULT 3,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT cards_pkey PRIMARY KEY (id)
);
CREATE TABLE public.game_manager (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  player1_id uuid NOT NULL,
  player2_id uuid,
  turn smallint NOT NULL,
  phase text NOT NULL DEFAULT 'waiting'::text CHECK (phase = ANY (ARRAY['waiting'::text, 'previewing'::text, 'shopping'::text, 'battling'::text, 'done'::text])),
  winner_id uuid,
  shop_ready smallint NOT NULL DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT game_manager_pkey PRIMARY KEY (id),
  CONSTRAINT game_manager_player2_id_fkey FOREIGN KEY (player2_id) REFERENCES public.users(id),
  CONSTRAINT game_manager_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.users(id),
  CONSTRAINT game_manager_player1_id_fkey FOREIGN KEY (player1_id) REFERENCES public.users(id)
);
CREATE TABLE public.player (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  gold smallint NOT NULL DEFAULT 10,
  turn smallint NOT NULL DEFAULT 1,
  health smallint NOT NULL DEFAULT 10,
  status text NOT NULL DEFAULT 'shopping'::text CHECK (status = ANY (ARRAY['shopping'::text, 'searching'::text, 'previewing'::text, 'in_match'::text])),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT player_pkey PRIMARY KEY (id),
  CONSTRAINT player_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.player_cards (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  card_id uuid NOT NULL,
  slot smallint NOT NULL CHECK (slot >= 0 AND slot <= 4),
  attack smallint NOT NULL,
  health smallint NOT NULL,
  level smallint NOT NULL DEFAULT 1 CHECK (level >= 1 AND level <= 3),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT player_cards_pkey PRIMARY KEY (id),
  CONSTRAINT player_cards_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT player_cards_card_id_fkey FOREIGN KEY (card_id) REFERENCES public.cards(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  username text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  wins smallint NOT NULL DEFAULT 0,
  losses smallint NOT NULL DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);