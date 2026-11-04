"""Записывает звук для каждой строки audio/words.tsv (hash<TAB>текст) в audio/<hash>.mp3.
Голос: Microsoft Edge neural (ar-SA-HamedNeural). Уже записанные файлы пропускаются."""
import asyncio, os, sys
import edge_tts

VOICE = os.environ.get('TTS_VOICE', 'ar-SA-HamedNeural')
RATE = os.environ.get('TTS_RATE', '-15%')

async def one(h, text, sem):
    path = f'audio/{h}.mp3'
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return 'skip'
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
                if os.path.getsize(path) > 500:
                    return 'ok'
            except Exception as e:
                print('retry', h, text, e, file=sys.stderr)
            await asyncio.sleep(2 + attempt * 3)
    return 'fail'

async def main():
    rows = [l.rstrip('\n').split('\t', 1) for l in open('audio/words.tsv', encoding='utf-8') if '\t' in l]
    sem = asyncio.Semaphore(4)
    res = await asyncio.gather(*(one(h, t, sem) for h, t in rows))
    print({k: res.count(k) for k in set(res)})
    if res.count('fail') > len(rows) // 4:
        sys.exit(1)

asyncio.run(main())
