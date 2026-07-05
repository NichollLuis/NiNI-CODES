# Bible Companion

A small full-stack Bible companion app with:

- Bible quizzes
- Verse memorization
- Daily devotionals
- Prayer journal

Run it with:

```powershell
python backend.py
```

Then open:

```text
http://127.0.0.1:8000
```

The backend serves `Pinboard webpage.html` and stores user data in `data/bible_companion.json`.

## API

- `GET /api/health`
- `GET /api/bootstrap`
- `POST /api/quiz/attempt`
- `POST /api/memory/progress`
- `POST /api/devotional/note`
- `POST /api/prayers`
- `POST /api/prayers/:id`
- `POST /api/prayers/:id/delete`
