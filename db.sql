-- ============================================================
--  Cards of Rebellion — full schema
--  Safe to re-run (uses IF NOT EXISTS / OR REPLACE)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.cards (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    tier        int2 NOT NULL DEFAULT 1 CHECK (tier BETWEEN 1 AND 6),
    base_attack int2 NOT NULL,
    base_health int2 NOT NULL,
    ability     text,
    cost        int2 NOT NULL DEFAULT 3,
    speed       int2 NOT NULL DEFAULT 5,
    created_at  timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username      text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    wins          int2 NOT NULL DEFAULT 0,
    losses        int2 NOT NULL DEFAULT 0,
    created_at    timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.player (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gold       int2 NOT NULL DEFAULT 10,
    turn       int2 NOT NULL DEFAULT 1,
    health     int2 NOT NULL DEFAULT 10,
    status     text NOT NULL DEFAULT 'shopping'
               CHECK (status IN ('shopping','searching','previewing','in_match')),
    last_seen  timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.player_cards (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id    uuid NOT NULL REFERENCES cards(id),
    slot       int2 NOT NULL CHECK (slot BETWEEN 0 AND 4),
    attack     int2 NOT NULL,
    health     int2 NOT NULL,
    speed      int2 NOT NULL DEFAULT 5,
    level      int2 NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 3),
    created_at timestamptz DEFAULT now(),
    UNIQUE (user_id, slot)
);

CREATE TABLE IF NOT EXISTS public.game_manager (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    player1_id      uuid NOT NULL REFERENCES users(id),
    player2_id      uuid REFERENCES users(id),
    turn            int2 NOT NULL,
    phase           text NOT NULL DEFAULT 'waiting'
                    CHECK (phase IN ('waiting','previewing','shopping','battling','done')),
    shop_ready      int2 NOT NULL DEFAULT 0,
    preview_ready   int2 NOT NULL DEFAULT 0,
    preview_started_at timestamptz,
    winner_id       uuid REFERENCES users(id),
    created_at      timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_player_user       ON player       (user_id);
CREATE INDEX IF NOT EXISTS idx_player_cards_user ON player_cards (user_id);
CREATE INDEX IF NOT EXISTS idx_gm_phase_turn     ON game_manager (phase, turn);

-- ── Atomic matchmaking ─────────────────────────────────────
CREATE OR REPLACE FUNCTION find_or_create_match(p_user_id uuid, p_turn int2)
RETURNS json LANGUAGE plpgsql AS $$
DECLARE
  existing_id uuid;
  result      json;
BEGIN
  SELECT id INTO existing_id
  FROM game_manager
  WHERE phase = 'waiting' AND turn = p_turn AND player1_id != p_user_id
  LIMIT 1 FOR UPDATE SKIP LOCKED;

  IF existing_id IS NOT NULL THEN
    UPDATE game_manager
    SET player2_id = p_user_id, phase = 'previewing', preview_ready = 0, shop_ready = 0,
        preview_started_at = now()
    WHERE id = existing_id;
    SELECT row_to_json(g) INTO result FROM game_manager g WHERE id = existing_id;
  ELSE
    INSERT INTO game_manager (player1_id, turn, phase)
    VALUES (p_user_id, p_turn, 'waiting')
    RETURNING row_to_json(game_manager.*) INTO result;
  END IF;

  RETURN result;
END;
$$;

-- ── Signal both ready (increments shop_ready counter) ────────
CREATE OR REPLACE FUNCTION player_ready(p_match_id uuid)
RETURNS json LANGUAGE plpgsql AS $$
DECLARE
  result json;
BEGIN
  UPDATE game_manager
  SET
    shop_ready = shop_ready + 1,
    phase = CASE WHEN shop_ready + 1 >= 2 THEN 'battling' ELSE phase END
  WHERE id = p_match_id;

  SELECT row_to_json(g) INTO result FROM game_manager g WHERE id = p_match_id;
  RETURN result;
END;
$$;

-- ── Starter cards ──────────────────────────────────────────
INSERT INTO public.cards (name, tier, base_attack, base_health, ability, cost, speed) VALUES
  ('Spades',   1, 3, 6, 'none', 3, 5),
  ('Hearts',   1, 5, 3, 'none', 3, 4),
  ('Diamonds', 1, 2, 8, 'none', 3, 6),
  ('Clubs',    1, 6, 2, 'none', 3, 3),
  ('Joker',    2, 4, 5, 'none', 4, 5),
  ('Ace',      2, 7, 4, 'none', 4, 2)
ON CONFLICT DO NOTHING;
