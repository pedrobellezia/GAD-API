-- Futuramente implementar uma role especifica para cron
SELECT cron.schedule(
    'delete_soft_deleted_users',
    '0 0 * * *',
    $$
    DELETE FROM users
    WHERE deleted_at IS NOT NULL
      AND deleted_at < NOW() - INTERVAL '1 month';
    $$
);
