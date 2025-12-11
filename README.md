# Text RPG Skeleton

Minimal deterministic, turn-based RPG scaffold following layered architecture:

- `presentation`: CLI only, depends on application layer
- `application`: services, DTOs, event bus, progression
- `domain`: pure models, events, repository interfaces
- `infrastructure`: concrete adapters (in-memory repos, Open5e stub)

Run locally (prefers MySQL persistence, falls back to in-memory if unreachable):

```bash
python -m rpg
```

Use MySQL schema + Open5e import:

1) Create DB and run `src/rpg/infrastructure/db/create_tables.sql` (optionally `create_history_tables.sql`).
2) Run migration `src/rpg/infrastructure/db/migrations/001_add_world_and_hp.sql` to add `world` table and HP columns.
3) Export `RPG_DATABASE_URL`, e.g. `mysql+mysqlconnector://user:pass@localhost:3306/rpg_game`.
4) Import monsters from Open5e into MySQL (optionally pin them to the first location):
        ```bash
        python -m rpg.infrastructure.db.mysql.import_open5e_monsters --pages 2 --location-id 1
        ```
5) Run game pointing at MySQL (world state persists via `world` table):
        ```bash
        set RPG_DATABASE_URL=mysql+mysqlconnector://user:pass@localhost:3306/rpg_game
        python -m rpg
        ```

Next steps:
- Flesh out domain stats, factions, and encounter tables
- Add tests under `tests/`
