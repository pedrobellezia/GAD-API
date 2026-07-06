-- Avaliar o custo de subquerrys e se vale a pena criar criar deleted_at para cada tabela
ALTER TABLE agencies
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE agencies
    FORCE ROW LEVEL SECURITY;
ALTER TABLE designers
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE designers
    FORCE ROW LEVEL SECURITY;
ALTER TABLE writers
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE writers
    FORCE ROW LEVEL SECURITY;
ALTER TABLE clients
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients
    FORCE ROW LEVEL SECURITY;
ALTER TABLE users
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE users
    FORCE ROW LEVEL SECURITY;

CREATE POLICY hide_soft_deleted_users
    ON users
    AS RESTRICTIVE
    FOR ALL
    USING (
    users.deleted_at is NULL
    );
CREATE POLICY hide_soft_deleted_clients
    ON clients
    AS RESTRICTIVE
    FOR ALL
    USING (
    EXISTS (SELECT 1
            FROM users
            WHERE users.id = clients.id
              AND users.deleted_at IS NULL)
    );
CREATE POLICY hide_soft_deleted_writers
    ON writers
    AS RESTRICTIVE
    FOR ALL
    USING (
    EXISTS (SELECT 1
            FROM users
            WHERE users.id = writers.id
              AND users.deleted_at IS NULL)
    );
CREATE POLICY hide_soft_deleted_agencies
    ON agencies
    AS RESTRICTIVE
    FOR ALL
    USING (
    EXISTS (SELECT 1
            FROM users
            WHERE users.id = agencies.id
              AND users.deleted_at IS NULL)
    );
CREATE POLICY hide_soft_deleted_designers
    ON designers
    AS RESTRICTIVE
    FOR ALL
    USING (
    EXISTS (SELECT 1
            FROM users
            WHERE users.id = designers.id
              AND users.deleted_at IS NULL)
    );