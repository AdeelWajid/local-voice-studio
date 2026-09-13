import sys
import threading
import logging
from backend.config import VENDOR, MODEL
from backend.diagnostics import missing_checkpoints

class IndexTTSEngine:
    """One resident model, accessed only by the single inference worker."""
    def __init__(self):
        self.model = None
        self.state = 'not_loaded'
        self.error = None
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
            if not torch.cuda.is_available():
                raise RuntimeError('CUDA is unavailable. Install the CUDA-enabled PyTorch runtime.')
            import indextts.infer_v2_5 as upstream
            # This upstream revision prints normalized private scripts even with
            # verbose=False. Suppress only this module's print, not global stdout.
            upstream.print = lambda *args, **kwargs: None
            self.model = upstream.IndexTTS2(
                cfg_path=str(MODEL / 'config.yaml'), model_dir=str(MODEL),
                use_bf16=torch.cuda.is_bf16_supported(), use_qwen_emo=True,
                use_cuda_kernel=False, use_deepspeed=False,
            )
            self.state = 'ready'
            logging.getLogger('voice_studio').info('Model loaded')
        except Exception as exc:
            self.state, self.error = 'error', str(exc)
            raise

    def generate(self, request, reference, output):
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
                                     use_random=request.use_random,
                                     duration_factor=request.duration_factor)
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                raise RuntimeError('CUDA ran out of memory. Try a shorter script or close other GPU applications.') from None
            finally:
                self.state = 'ready'

engine = IndexTTSEngine()
