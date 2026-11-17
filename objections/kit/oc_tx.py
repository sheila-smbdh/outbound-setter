# Transcribe one recording: python oc_tx.py in.mp3 out.json MODEL_DIR [threads]. Runs in the Claude container (oc_local.py).
# Audio is decoded with PyAV (faster-whisper's own decoder fails on this av version) and transcribed in 2-minute chunks.
import os, sys, json, time, gc, numpy as np, av
from av.audio.resampler import AudioResampler
PROMPT = 'SMB Deal Hunter sales call. Setter, enrollment advisor, SBA loan, HELOC, 401(k), down payment, due diligence, LOI, off-market deals, cash flow.'
SR, CHUNK = 16000, 120
def chunks(path):
    ct = av.open(path); rs = AudioResampler(format='flt', layout='mono', rate=SR); buf, n = [], 0
    def frames():
        for f in ct.decode(audio=0): yield from rs.resample(f)
        yield from rs.resample(None)
    for g in frames():
        a = g.to_ndarray().reshape(-1); buf.append(a); n += len(a)
        if n >= SR * CHUNK:
            yield np.concatenate(buf).astype(np.float32); buf, n = [], 0
    if buf: yield np.concatenate(buf).astype(np.float32)
    ct.close()
def main(mp3, outp, model, threads='1'):
    from faster_whisper import WhisperModel
    t = time.time()
    m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=int(threads), num_workers=1)
    S, off = [], 0.0
    for x in chunks(mp3):
        segs, _ = m.transcribe(x, language='en', beam_size=1, vad_filter=True, vad_parameters={'min_silence_duration_ms': 500}, condition_on_previous_text=False, initial_prompt=PROMPT)
        # Whisper sometimes echoes the vocabulary prompt on silence (Oct 27 backfill): drop those segments
        S += [{'s': round(off + s.start, 1), 'e': round(off + s.end, 1), 't': s.text.strip()} for s in segs
              if not ('enrollment advisor, SBA loan' in s.text or s.text.strip().startswith('SMB Deal Hunter sales call'))]
        off += len(x) / SR; del x; gc.collect()
    json.dump({'audio_sec': round(off, 1), 'proc_sec': round(time.time() - t, 1), 'model': os.path.basename(model.rstrip('/')), 'segments': S}, open(outp, 'w'))
if __name__ == '__main__': main(*sys.argv[1:])
