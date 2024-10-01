CALL db.schema.visualization();

CALL db.labels();

CALL db.relationshipTypes();

CALL db.propertyKeys();

CALL db.indexes();

CALL db.constraints();

MATCH (n:Address)
WITH keys(n) AS properties
UNWIND properties AS property
RETURN DISTINCT property;


MATCH ()-[r:SENT]->()
WITH keys(r) AS properties
UNWIND properties AS property
RETURN DISTINCT property;

