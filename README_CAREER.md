# AutoPTU Career

Modo carrera web bilingüe construido sobre el motor PTU de AutoPTU. El proyecto conserva el
motor y los datasets originales; `auto_ptu/career` es un dominio separado y cada combate cumple
el contrato determinista `BattleSpec + seed + ContentVersion -> BattleTranscript`.

## Vertical slice incluida

- Nueve regiones, Junior/Rookie/Regular/Elite, edad inicial 12, starters oficiales y catálogo PTU
  completo de underdogs regionales, 10 Poké Balls y
  las 69 clases PTU adaptadas con cobertura explícita de sus 709 features.
- 240 familias de decisiones y 25.920 nodos mecánicamente distintos, validados por hash para
  rechazar nodos muertos o variantes que sólo cambien texto.
- Temporadas completas de 6/8/10/12 combates PTU, progresión por edad/rendimiento, contratos,
  salud, ascenso, descenso, retiro, resumen y timeline.
- Identidad persistente por Pokémon, movimientos legales por nivel/fuente, clases con efectos
  directos, apuestas con ruleta y replays exportados antes de desmontar el motor aislado.
- React 19 + TypeScript, arena PixiJS 8 cargada sólo en `/career-game/battle/...`, replay local en
  IndexedDB y escenas exclusivas para creación, temporada, perfil, timeline y reto diario.
- Auth Supabase, esquema privado para carreras ranked, RLS en proyecciones públicas, cuota de tres
  intentos transaccional, resultados/score creados por backend y worker independiente.
- Prosa Ollama opcional con digest obligatorio, caché por contexto y fallback autoral inmediato.

## Desarrollo local

```powershell
cd C:\Users\tefa1\AutoPTUCareer\career_web
npm ci
npm run build

cd C:\Users\tefa1\AutoPTUCareer
python -m uvicorn auto_ptu.api.server:app --host 127.0.0.1 --port 8010
```

Abrir `http://127.0.0.1:8010/career-game/`. Sin variables Supabase se usa una identidad local y
archivos JSON en `portable_data/career`; las carreras libres funcionan, pero ranked requiere una
cuenta permanente cuando Supabase está configurado.

Variables de producción:

- `DATABASE_URL`: conexión Postgres privada del backend/worker.
- `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY`: validación de sesiones; nunca usar service-role en
  el navegador.
- `VITE_SUPABASE_URL` y `VITE_SUPABASE_PUBLISHABLE_KEY`: claves públicas durante el build.
- `OLLAMA_URL`, `OLLAMA_MODEL` y `OLLAMA_MODEL_DIGEST=sha256:<64 hex>`: narrativa opcional fijada.

## Supabase y Render

La migración está en `supabase/migrations`. Antes de conectar un proyecto remoto:

```powershell
npx supabase start
npx supabase db reset
npx supabase db lint --local
```

`render.yaml` define web FastAPI, worker de combates y Ollama privado. Los secretos están marcados
como `sync: false`. Debe configurarse el digest real del modelo y realizarse la revisión legal de
Pokémon, datasets y assets antes de cualquier publicación.

## Verificación

```powershell
python -m pytest -q tests/test_campaign_play.py tests/test_battle_commands.py tests/test_trainer_features.py tests/test_web_regressions.py
python -m pytest tests/test_career_domain.py tests/test_career_battle_determinism.py tests/test_career_narrative.py -q
cd career_web
npm run build
```

La procedencia exacta del fork y el hash del snapshot inicial están documentados en
`BASELINE_PROVENANCE.md`.
