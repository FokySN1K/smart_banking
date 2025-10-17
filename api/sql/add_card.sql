INSERT INTO card (owner_id, name, is_active, description)
VALUES (%(owner_id)s, %(name)s, true, %(description)s)
RETURNING id, owner_id, name, is_active, description;
