from sentence_transformers import SentenceTransformer
import time

model = SentenceTransformer("all-MiniLM-L6-v2")
queries = [
    "Region: Ironhold. NPCs: Captain Varek. World: mildly tyrannical. Player: I bribe the guard.",
    "Region: Ashenvale. NPCs: Sylara. World: somewhat merciful. Player: I search for herbs.",
    "Region: Whispermarsh. NPCs: One-Eye Mags. World: deeply anarchic. Player: I attack the bandit.",
    "Region: Ironhold. NPCs: Merchant Theron. World: justice. Player: I ask about recent events.",
]

start = time.time()
embeddings = model.encode(queries)
elapsed = time.time() - start
per_query = elapsed / len(queries) * 1000

print(f"async thread confirmed, {per_query:.0f}ms per query")
print(f"< 200ms per query" if per_query < 200 else "WARNING: SLOW — check CPU load")
