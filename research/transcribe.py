import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(sys.argv[1], language="ar", vad_filter=False)
out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
words = sum(len(s["text"].split()) for s in out); dur = out[-1]["end"] if out else 0
json.dump({"duration": dur, "words": words, "wps": round(words / dur, 2) if dur else 0, "segments": out}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(sys.argv[1], dur, words)
