# Transcribe one recording: python oc_tx.py in.mp3 out.json. One process per recording (workbench: 1 CPU, ~1 GB RAM).
import sys, json, time, numpy as np, av
from av.audio.resampler import AudioResampler
PROMPT = 'SMB Deal Hunter sales call. Setter, enrollment advisor, SBA loan, HELOC, 401(k), down payment, due diligence, LOI, off-market deals, cash flow.'
def decode(path):
    ct = av.open(path); rs = AudioResampler(format='flt', layout='mono', rate=16000); out = []
    for f in ct.decode(audio=0):
        for g in rs.resample(f): out.append(g.to_ndarray().reshape(-1))
    for g in rs.resample(None): out.append(g.to_ndarray().reshape(-1))
    return np.concatenate(out).astype(np.float32)
def main(mp3, outp, model='base.en'):
    from faster_whisper import WhisperModel
    t = time.time(); x = decode(mp3)
    m = WhisperModel(model, device='cpu', compute_type='int8', download_root='/home/user/whisper', cpu_threads=1)
    segs, info = m.transcribe(x, language='en', beam_size=1, vad_filter=True, condition_on_previous_text=False, initial_prompt=PROMPT)
    S = [{'s': round(s.start, 1), 'e': round(s.end, 1), 't': s.text.strip()} for s in segs]
    json.dump({'audio_sec': round(len(x) / 16000, 1), 'proc_sec': round(time.time() - t, 1), 'model': model, 'segments': S}, open(outp, 'w'))
if __name__ == '__main__': main(*sys.argv[1:])
