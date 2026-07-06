CREATE OR REPLACE FUNCTION get_user_for_auth(p_email TEXT)
RETURNS users
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT *
    FROM users
    WHERE email = p_email
    LIMIT 1;
$$;

REVOKE ALL ON FUNCTION get_user_for_auth(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION get_user_for_auth(TEXT) TO dml_role;

CREATE OR REPLACE FUNCTION restore_user(p_email TEXT)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    UPDATE users
    SET deleted_at = NULL
    WHERE email = p_email;
$$;

REVOKE ALL ON FUNCTION restore_user(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION restore_user(TEXT) TO dml_role;