select
  name
  , type
from sqlite_master
where type = "table"
  and name = "micromigrate_migrations"
