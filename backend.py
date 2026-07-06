from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
import json
import mimetypes
import re
import os
import threading
import time


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "bible_companion.json"
HOME_FILE = ROOT / "Pinboard webpage.html"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

STORE_LOCK = threading.Lock()

QUIZZES = [
    {
        "id": "foundations",
        "title": "Bible Foundations",
        "description": "Creation, covenants, gospel basics, and the early church.",
        "questions": [
            {
                "prompt": "Who built the ark before the flood?",
                "options": ["Noah", "Moses", "Abraham", "David"],
                "answer": 0,
                "reference": "Genesis 6:14",
            },
            {
                "prompt": "Which book records the birth of the church at Pentecost?",
                "options": ["Romans", "Acts", "Hebrews", "Revelation"],
                "answer": 1,
                "reference": "Acts 2",
            },
            {
                "prompt": "What is the first book of the Bible?",
                "options": ["Exodus", "Genesis", "Psalms", "Matthew"],
                "answer": 1,
                "reference": "Genesis 1:1",
            },
            {
                "prompt": "Who interpreted Pharaoh's dreams in Egypt?",
                "options": ["Joseph", "Samuel", "Daniel", "Joshua"],
                "answer": 0,
                "reference": "Genesis 41",
            },
        ],
    },
    {
        "id": "jesus-life",
        "title": "Life of Jesus",
        "description": "Moments from the Gospels and the teachings of Christ.",
        "questions": [
            {
                "prompt": "Where was Jesus born?",
                "options": ["Nazareth", "Jerusalem", "Bethlehem", "Capernaum"],
                "answer": 2,
                "reference": "Luke 2:4-7",
            },
            {
                "prompt": "Which disciple walked on water toward Jesus?",
                "options": ["Peter", "John", "Thomas", "Andrew"],
                "answer": 0,
                "reference": "Matthew 14:28-29",
            },
            {
                "prompt": "What prayer did Jesus teach His disciples?",
                "options": ["Hannah's Prayer", "The Lord's Prayer", "Jabez's Prayer", "Solomon's Prayer"],
                "answer": 1,
                "reference": "Matthew 6:9-13",
            },
            {
                "prompt": "Who found the empty tomb first in John's Gospel?",
                "options": ["Mary Magdalene", "Martha", "Peter", "Nicodemus"],
                "answer": 0,
                "reference": "John 20:1",
            },
        ],
    },
    {
        "id": "wisdom",
        "title": "Wisdom and Worship",
        "description": "Psalms, Proverbs, and spiritual habits.",
        "questions": [
            {
                "prompt": "Which book begins, 'The LORD is my shepherd'?",
                "options": ["Psalm 23", "Psalm 91", "Proverbs 3", "Isaiah 40"],
                "answer": 0,
                "reference": "Psalm 23:1",
            },
            {
                "prompt": "According to Proverbs, what is the beginning of wisdom?",
                "options": ["Hard work", "The fear of the LORD", "Silence", "Wealth"],
                "answer": 1,
                "reference": "Proverbs 9:10",
            },
            {
                "prompt": "Which king is known for asking God for wisdom?",
                "options": ["Saul", "Solomon", "Hezekiah", "Ahab"],
                "answer": 1,
                "reference": "1 Kings 3:9-12",
            },
            {
                "prompt": "Which Psalm says God's word is a lamp to my feet?",
                "options": ["Psalm 1", "Psalm 19", "Psalm 119", "Psalm 150"],
                "answer": 2,
                "reference": "Psalm 119:105",
            },
        ],
    },
]

MEMORY_VERSES = [
    {
        "id": "john-3-16",
        "reference": "John 3:16",
        "text": "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.",
        "theme": "Gospel",
    },
    {
        "id": "psalm-119-105",
        "reference": "Psalm 119:105",
        "text": "Your word is a lamp to my feet and a light to my path.",
        "theme": "Guidance",
    },
    {
        "id": "philippians-4-6",
        "reference": "Philippians 4:6",
        "text": "Do not be anxious about anything, but in everything by prayer and supplication with thanksgiving let your requests be made known to God.",
        "theme": "Prayer",
    },
    {
        "id": "romans-8-28",
        "reference": "Romans 8:28",
        "text": "And we know that for those who love God all things work together for good, for those who are called according to his purpose.",
        "theme": "Hope",
    },
]

DEVOTIONALS = [
    {
        "id": "quiet-trust",
        "title": "Quiet Trust",
        "reference": "Psalm 46:10",
        "verse": "Be still, and know that I am God.",
        "reflection": "Stillness is not empty time. It is the space where hurry loosens its grip and trust becomes possible again.",
        "prompt": "Where do you need to practice stillness today?",
    },
    {
        "id": "daily-bread",
        "title": "Daily Bread",
        "reference": "Matthew 6:11",
        "verse": "Give us this day our daily bread.",
        "reflection": "Jesus teaches us to ask for today's provision, not tomorrow's stockpile. Grace often arrives in daily portions.",
        "prompt": "Name one need you can bring honestly to God today.",
    },
    {
        "id": "rooted-love",
        "title": "Rooted in Love",
        "reference": "Ephesians 3:17",
        "verse": "That Christ may dwell in your hearts through faith, that you, being rooted and grounded in love.",
        "reflection": "A rooted life is not easily pulled from peace. God's love gives depth beneath every visible season.",
        "prompt": "What would change if you moved through today from being loved?",
    },
    {
        "id": "renewed-mercy",
        "title": "Renewed Mercy",
        "reference": "Lamentations 3:22-23",
        "verse": "The steadfast love of the LORD never ceases; his mercies never come to an end; they are new every morning.",
        "reflection": "Morning mercy means yesterday does not get the final word. God meets His people with fresh compassion.",
        "prompt": "What old burden can you set down before beginning again?",
    },
]


def now():
    return int(time.time())


def default_store():
    return {
        "prayers": [
            {
                "id": 1,
                "title": "Family peace",
                "body": "Pray for patience, forgiveness, and gentle conversations this week.",
                "tag": "Family",
                "answered": False,
                "createdAt": now(),
            }
        ],
        "memoryProgress": {},
        "quizAttempts": [],
        "devotionalNotes": {},
        "updatedAt": now(),
    }


def read_store():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        write_store(default_store())
    with DATA_FILE.open("r", encoding="utf-8") as file:
        store = json.load(file)

    store.setdefault("prayers", [])
    store.setdefault("memoryProgress", {})
    store.setdefault("quizAttempts", [])
    store.setdefault("devotionalNotes", {})
    return store


def write_store(store):
    DATA_DIR.mkdir(exist_ok=True)
    store["updatedAt"] = now()
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(store, file, indent=2)


def request_json(handler):
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def public_quiz(quiz):
    return {
        **quiz,
        "questions": [
            {
                "prompt": question["prompt"],
                "options": question["options"],
                "reference": question["reference"],
            }
            for question in quiz["questions"]
        ],
    }


def today_devotional():
    day_index = int(time.strftime("%j", time.gmtime())) - 1
    return DEVOTIONALS[day_index % len(DEVOTIONALS)]


def store_summary(store):
    learned = sum(1 for value in store["memoryProgress"].values() if value == "learned")
    best_scores = {}
    for attempt in store["quizAttempts"]:
        quiz_id = attempt.get("quizId")
        score = int(attempt.get("score", 0))
        total = max(1, int(attempt.get("total", 1)))
        current = best_scores.get(quiz_id, 0)
        best_scores[quiz_id] = max(current, round((score / total) * 100))

    return {
        "openPrayers": sum(1 for prayer in store["prayers"] if not prayer.get("answered")),
        "answeredPrayers": sum(1 for prayer in store["prayers"] if prayer.get("answered")),
        "learnedVerses": learned,
        "quizAttempts": len(store["quizAttempts"]),
        "bestScores": best_scores,
    }


class BibleCompanionHandler(BaseHTTPRequestHandler):
    server_version = "BibleCompanion/1.0"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, message, status):
        self.send_json({"error": message}, status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            return self.send_json({"ok": True, "app": "Bible Companion"})

        if path == "/api/bootstrap":
            with STORE_LOCK:
                store = read_store()
            return self.send_json({
                "quizzes": [public_quiz(quiz) for quiz in QUIZZES],
                "memoryVerses": MEMORY_VERSES,
                "devotional": today_devotional(),
                "prayers": sorted(store["prayers"], key=lambda item: item["createdAt"], reverse=True),
                "memoryProgress": store["memoryProgress"],
                "devotionalNotes": store["devotionalNotes"],
                "stats": store_summary(store),
            })

        return self.serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/quiz/attempt":
            body = request_json(self)
            quiz_id = str(body.get("quizId", "")).strip()
            quiz = next((item for item in QUIZZES if item["id"] == quiz_id), None)
            if not quiz:
                return self.send_error_json("Quiz not found", 404)

            try:
                answers = [int(answer) for answer in body.get("answers", [])]
            except (TypeError, ValueError):
                return self.send_error_json("answers must be a list of numbers", 400)

            checked = []
            score = 0
            for index, question in enumerate(quiz["questions"]):
                selected = answers[index] if index < len(answers) else -1
                correct = int(question["answer"])
                score += 1 if selected == correct else 0
                checked.append({
                    "selected": selected,
                    "correct": correct,
                    "isCorrect": selected == correct,
                    "reference": question["reference"],
                })

            with STORE_LOCK:
                store = read_store()
                store["quizAttempts"].append({
                    "quizId": quiz_id,
                    "score": score,
                    "total": len(quiz["questions"]),
                    "createdAt": now(),
                })
                write_store(store)

            return self.send_json({
                "score": score,
                "total": len(quiz["questions"]),
                "results": checked,
                "stats": store_summary(store),
            })

        if path == "/api/memory/progress":
            body = request_json(self)
            verse_id = str(body.get("verseId", "")).strip()
            status = str(body.get("status", "practicing")).strip()
            if not any(verse["id"] == verse_id for verse in MEMORY_VERSES):
                return self.send_error_json("Verse not found", 404)
            if status not in {"new", "practicing", "learned"}:
                return self.send_error_json("status must be new, practicing, or learned", 400)

            with STORE_LOCK:
                store = read_store()
                if status == "new":
                    store["memoryProgress"].pop(verse_id, None)
                else:
                    store["memoryProgress"][verse_id] = status
                write_store(store)
            return self.send_json({"memoryProgress": store["memoryProgress"], "stats": store_summary(store)})

        if path == "/api/devotional/note":
            body = request_json(self)
            devotional_id = str(body.get("devotionalId", "")).strip()
            note = str(body.get("note", "")).strip()
            if not any(item["id"] == devotional_id for item in DEVOTIONALS):
                return self.send_error_json("Devotional not found", 404)
            with STORE_LOCK:
                store = read_store()
                if note:
                    store["devotionalNotes"][devotional_id] = note
                else:
                    store["devotionalNotes"].pop(devotional_id, None)
                write_store(store)
            return self.send_json({"note": note})

        if path == "/api/prayers":
            body = request_json(self)
            title = str(body.get("title", "")).strip()
            prayer_body = str(body.get("body", "")).strip()
            tag = str(body.get("tag", "Personal")).strip() or "Personal"
            if not title or not prayer_body:
                return self.send_error_json("title and body are required", 400)

            with STORE_LOCK:
                store = read_store()
                next_id = max([int(prayer["id"]) for prayer in store["prayers"]] or [0]) + 1
                prayer = {
                    "id": next_id,
                    "title": title,
                    "body": prayer_body,
                    "tag": tag,
                    "answered": False,
                    "createdAt": now(),
                }
                store["prayers"].append(prayer)
                write_store(store)
            return self.send_json({"prayer": prayer, "stats": store_summary(store)}, 201)

        prayer_match = re.fullmatch(r"/api/prayers/(\d+)", path)
        if prayer_match:
            prayer_id = int(prayer_match.group(1))
            body = request_json(self)
            with STORE_LOCK:
                store = read_store()
                prayer = next((item for item in store["prayers"] if int(item["id"]) == prayer_id), None)
                if not prayer:
                    return self.send_error_json("Prayer not found", 404)
                if "answered" in body:
                    prayer["answered"] = bool(body["answered"])
                for field in ("title", "body", "tag"):
                    if field in body:
                        prayer[field] = str(body[field]).strip()
                write_store(store)
            return self.send_json({"prayer": prayer, "stats": store_summary(store)})

        delete_match = re.fullmatch(r"/api/prayers/(\d+)/delete", path)
        if delete_match:
            prayer_id = int(delete_match.group(1))
            with STORE_LOCK:
                store = read_store()
                before = len(store["prayers"])
                store["prayers"] = [item for item in store["prayers"] if int(item["id"]) != prayer_id]
                if len(store["prayers"]) == before:
                    return self.send_error_json("Prayer not found", 404)
                write_store(store)
            return self.send_json({"deleted": prayer_id, "stats": store_summary(store)})

        return self.send_error_json("Not found", 404)

    def serve_static(self, path):
        if path in ("", "/"):
            target = HOME_FILE
        else:
            raw_path = unquote(path.lstrip("/"))
            target = (ROOT / raw_path).resolve()
            if ROOT not in target.parents and target != ROOT:
                return self.send_error_json("Forbidden", 403)

        if not target.exists() or target.is_dir():
            return self.send_error_json("Not found", 404)

        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix.lower() in {".html", ".css", ".js"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    with STORE_LOCK:
        read_store()
    print(f"Bible Companion running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), BibleCompanionHandler).serve_forever()
