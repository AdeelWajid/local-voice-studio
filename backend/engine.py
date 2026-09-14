import os
import sys
import threading
import logging
from backend.config import VENDOR, MODEL
from backend.diagnostics import missing_checkpoints

# IndexTTS hits a few ops that Metal does not implement; fall back to CPU for those.
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')

class IndexTTSEngine:
    """One resident model, accessed only by the single inference worker."""
    def __init__(self):
        self.model = None
        self.state = 'not_loaded'
        self.error = None
        self.device = None
        self.lock = threading.Lock()

    def load(self):
        if self.model is not None:
            return
        self.state, self.error = 'loading', None
        try:
            missing = missing_checkpoints()
            if missing:
                raise RuntimeError(f'IndexTTS setup is incomplete ({len(missing)} checkpoint files missing). Run scripts/download_models.py.')
            sys.path.insert(0, str(VENDOR))
            import torch
            import indextts.infer_v2_5 as upstream
            # This upstream revision prints normalized private scripts even with
            # verbose=False. Suppress only this module's print, not global stdout.
            upstream.print = lambda *args, **kwargs: None
            use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
            self.model = upstream.IndexTTS2(
                cfg_path=str(MODEL / 'config.yaml'), model_dir=str(MODEL),
                use_bf16=use_bf16, use_qwen_emo=True,
                use_cuda_kernel=False, use_deepspeed=False,
            )
            self.device = getattr(self.model, 'device', None)
            self.state = 'ready'
            logging.getLogger('voice_studio').info('Model loaded on %s', self.device or 'unknown device')
        except Exception as exc:
            self.state, self.error = 'error', str(exc)
            raise

    def generate(self, request, reference, output, emotion_reference=None):
        with self.lock:
            self.load()
            import torch
            self.state = 'generating'
            try:
                with torch.inference_mode():
                    self.model.infer(spk_audio_prompt=str(reference), text=request.text,
                                     lang=request.language, output_path=str(output), verbose=False,
                                     emo_vector=request.emotion_vector if request.emotion_mode == 'vector' else None,
                                     emo_alpha=request.emotion_alpha,
                                     use_emo_text=request.emotion_mode in ('description', 'auto_text'),
                                     emo_text=request.emotion_text if request.emotion_mode == 'description' else None,
                                     emo_audio_prompt=str(emotion_reference) if emotion_reference and request.emotion_mode == 'reference' else None,
                                     use_random=request.use_random,
                                     duration_factor=request.duration_factor)
            except Exception as exc:
                if _is_accelerator_oom(torch, exc):
                    _release_accelerator_memory(torch)
                    raise RuntimeError('The GPU ran out of memory. Try a shorter script or close other applications.') from None
                raise
            finally:
                self.state = 'ready'

def _is_accelerator_oom(torch, exc):
    types = []
    if hasattr(torch, 'OutOfMemoryError'):
        types.append(torch.OutOfMemoryError)
    if hasattr(torch.cuda, 'OutOfMemoryError'):
        types.append(torch.cuda.OutOfMemoryError)
    if types and isinstance(exc, tuple(types)):
        return True
    return isinstance(exc, RuntimeError) and 'out of memory' in str(exc).lower()

def _release_accelerator_memory(torch):
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    mps = getattr(torch.backends, 'mps', None)
    if mps is not None and mps.is_available() and hasattr(torch, 'mps'):
        try:
            torch.mps.empty_cache()
        except Exception:
            pass

engine = IndexTTSEngine()
