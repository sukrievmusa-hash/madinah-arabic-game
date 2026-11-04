"""Записывает звук для каждой строки audio/words.tsv (hash<TAB>текст) в audio/<hash>.mp3.
Сначала нейронный голос Microsoft (edge-tts), при сбое — голос Google (gTTS).
У каждого запроса есть ограничение по времени; уже записанные файлы пропускаются."""
import asyncio, os, sys, time

VOICE = os.environ.get('TTS_VOICE', 'ar-SA-HamedNeural')
RATE = os.environ.get('TTS_RATE', '-15%')
rows = [l.rstrip('\n').split('\t', 1) for l in open('audio/words.tsv', encoding='utf-8') if '\t' in l]
todo = [(h, t) for h, t in rows if not (os.path.exists(f'audio/{h}.mp3') and os.path.getsize(f'audio/{h}.mp3') > 500)]
print(f'всего {len(rows)}, записать {len(todo)}', flush=True)

def ok(path):
    return os.path.exists(path) and os.path.getsize(path) > 500

async def edge_one(h, text):
    import edge_tts
    path = f'audio/{h}.mp3'
    await asyncio.wait_for(edge_tts.Communicate(text, VOICE, rate=RATE).save(path), timeout=25)
    return ok(path)

def edge_works():
    try:
        return asyncio.run(edge_one(*todo[0])) if todo else False
    except Exception as e:
        print('edge-tts недоступен:', repr(e)[:200], flush=True)
        return False

def run_edge():
    async def main():
        sem = asyncio.Semaphore(3); done = 0; bad = []
        async def one(h, t):
            nonlocal done
            async with sem:
                for a in range(3):
                    try:
                        if await edge_one(h, t): break
                    except Exception as e:
                        await asyncio.sleep(2 + 2 * a)
                else:
                    bad.append((h, t))
                done += 1
                if done % 50 == 0: print('edge', done, '/', len(todo), flush=True)
        await asyncio.gather(*(one(h, t) for h, t in todo))
        return bad
    return asyncio.run(main())

def run_gtts(items):
    from gtts import gTTS
    bad = []
    for i, (h, t) in enumerate(items, 1):
        for a in range(3):
            try:
                gTTS(t, lang='ar', slow=False, timeout=20).save(f'audio/{h}.mp3')
                if ok(f'audio/{h}.mp3'): break
            except Exception as e:
                time.sleep(2 + 3 * a)
        else:
            bad.append((h, t))
        if i % 50 == 0: print('gtts', i, '/', len(items), flush=True)
        time.sleep(0.3)
    return bad

if not todo:
    sys.exit(0)
if edge_works():
    print('голос: Microsoft', VOICE, flush=True)
    left = run_edge()
else:
    left = todo
if left:
    print('голос Google для', len(left), flush=True)
    left = run_gtts(left)
print('не записано:', len(left), flush=True)
sys.exit(1 if len(left) > len(rows) // 4 else 0)
