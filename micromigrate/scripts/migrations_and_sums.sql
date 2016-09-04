
select
  name
  , case
    when completed = 1
      then checksum
      else ':failed to complete'
  end as checksum
from micromigrate_migrations
