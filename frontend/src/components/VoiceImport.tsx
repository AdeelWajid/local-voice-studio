import { useEffect, useRef, useState } from "react";
import { LoaderCircle, Play, Plus, Square, Upload, X } from "lucide-react";
import { api, type Voice } from "../api";

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) return "0.0";
  return seconds.toFixed(1);
}

async function waveformPeaks(file: File, bins = 72) {
  const context = new AudioContext();
  try {
    const buffer = await context.decodeAudioData(await file.arrayBuffer());
    const channel = buffer.getChannelData(0);
    const step = Math.max(1, Math.floor(channel.length / bins));
    const peaks: number[] = [];
    for (let index = 0; index < bins; index += 1) {
      let peak = 0;
      const start = index * step;
      for (let sample = start; sample < Math.min(start + step, channel.length); sample += 1) {
        peak = Math.max(peak, Math.abs(channel[sample]));
      }
      peaks.push(peak);
    }
    return peaks;
  } finally {
    await context.close();
  }
}

export function VoiceImport({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (voice: Voice) => void;
}) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [duration, setDuration] = useState(0);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [previewing, setPreviewing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const audio = useRef<HTMLAudioElement>(null);
  const selected = Math.max(0, trimEnd - trimStart);
  const trimReady = selected >= 3 && selected <= 60;
  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);
  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      setDuration(0);
      setTrimStart(0);
      setTrimEnd(0);
      setPeaks([]);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    let cancelled = false;
    waveformPeaks(file)
      .then((next) => {
        if (!cancelled) setPeaks(next);
      })
      .catch(() => {
        if (!cancelled) setPeaks([]);
      });
    return () => {
      cancelled = true;
      URL.revokeObjectURL(url);
    };
  }, [file]);
  function chooseFile(next: File | null) {
    setFile(next);
    setError("");
    setPreviewing(false);
  }
  function readyAudio(element: HTMLAudioElement) {
    const length = element.duration;
    if (!Number.isFinite(length) || length <= 0) return;
    setDuration(length);
    setTrimStart(0);
    setTrimEnd(length > 60 ? 15 : length);
  }
  function stopPreview() {
    const element = audio.current;
    if (element && !element.paused) element.pause();
    setPreviewing(false);
  }
  function previewSelection() {
    const element = audio.current;
    if (!element || !trimReady) return;
    element.currentTime = trimStart;
    void element.play();
    setPreviewing(true);
  }
  function onTimeUpdate() {
    const element = audio.current;
    if (!element || !previewing) return;
    if (element.currentTime >= trimEnd - 0.03) {
      element.pause();
      setPreviewing(false);
    }
  }
  async function upload() {
    if (!file || !name.trim() || busy || !trimReady) return;
    stopPreview();
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("name", name);
    form.append("file", file);
    form.append("trim_start", String(trimStart));
    form.append("trim_end", String(trimEnd));
    try {
      onSaved(await api<Voice>("/voices", { method: "POST", body: form }));
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="modal voice-import"
      aria-labelledby="upload-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="panel-heading">
        <h2 id="upload-title">Add a voice</h2>
        <button aria-label="Close" disabled={busy} onClick={onClose}>
          <X size={18} />
        </button>
      </div>
      <p>
        Use a clean 5–15 second recording with one speaker and little background
        noise. Preview and trim before you save.
      </p>
      <label className="field-label" htmlFor="voice-name">
        VOICE NAME
      </label>
      <input
        id="voice-name"
        autoFocus
        value={name}
        maxLength={100}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g. My narration voice"
      />
      <input
        ref={input}
        type="file"
        accept=".wav,.mp3,.flac,.m4a,.ogg,.webm"
        onChange={(e) => chooseFile(e.target.files?.[0] || null)}
        className="file-input"
      />
      <button className="dropzone" onClick={() => input.current?.click()}>
        <Upload size={25} />
        <strong>{file?.name || "Choose a reference recording"}</strong>
        <span>WAV, MP3, FLAC, M4A, OGG · up to 50 MB</span>
      </button>
      {previewUrl && (
        <div className="voice-prep">
          <div className="field-row">
            <span className="field-label">PREVIEW AND TRIM</span>
            <span className={"trim-length" + (trimReady ? "" : " failure")}>
              {formatTime(selected)}s selected
              {duration ? ` of ${formatTime(duration)}s` : ""}
            </span>
          </div>
          {peaks.length > 0 && (
            <div className="import-waveform" aria-hidden="true">
              {peaks.map((peak, index) => {
                const position = (index + 0.5) / peaks.length;
                const active =
                  duration > 0 &&
                  position >= trimStart / duration &&
                  position <= trimEnd / duration;
                return (
                  <span
                    key={index}
                    className={active ? "active" : undefined}
                    style={{ height: `${Math.max(6, peak * 100)}%` }}
                  />
                );
              })}
            </div>
          )}
          <audio
            ref={audio}
            controls
            src={previewUrl}
            onLoadedMetadata={(event) => readyAudio(event.currentTarget)}
            onTimeUpdate={onTimeUpdate}
            onPause={() => setPreviewing(false)}
            onEnded={() => setPreviewing(false)}
          />
          <label className="slider-row">
            <span>Start</span>
            <input
              type="range"
              min="0"
              max={duration || 0}
              step="0.1"
              value={trimStart}
              aria-label="Trim start"
              disabled={!duration}
              onChange={(e) => {
                const next = Number(e.target.value);
                setTrimStart(Math.min(next, Math.max(0, trimEnd - 0.1)));
              }}
            />
            <output>{formatTime(trimStart)}s</output>
          </label>
          <label className="slider-row">
            <span>End</span>
            <input
              type="range"
              min="0"
              max={duration || 0}
              step="0.1"
              value={trimEnd}
              aria-label="Trim end"
              disabled={!duration}
              onChange={(e) => {
                const next = Number(e.target.value);
                setTrimEnd(Math.max(next, trimStart + 0.1));
              }}
            />
            <output>{formatTime(trimEnd)}s</output>
          </label>
          <div className="voice-prep-actions">
            <button
              className="secondary"
              type="button"
              disabled={!trimReady}
              onClick={() => (previewing ? stopPreview() : previewSelection())}
            >
              {previewing ? <Square size={13} /> : <Play size={13} />}
              {previewing ? "Stop preview" : "Preview selection"}
            </button>
            <p className="hint">
              {!duration
                ? "Loading audio…"
                : !trimReady
                  ? "Choose a 3–60 second section. 5–15 seconds is recommended."
                  : selected < 5 || selected > 15
                    ? "This will work. 5–15 seconds usually clones more reliably."
                    : "Good reference length. The original file is kept in full."}
            </p>
          </div>
        </div>
      )}
      <p className="consent">
        Only clone voices you own or have permission to use. Your original
        recording is preserved; the selected range becomes the speaker
        reference.
      </p>
      {error && (
        <p className="failure" role="alert">
          {error}
        </p>
      )}
      <button
        className="primary"
        disabled={!file || !name.trim() || busy || !trimReady}
        onClick={() => void upload()}
      >
        {busy ? (
          <LoaderCircle className="spin" size={16} />
        ) : (
          <Plus size={16} />
        )}{" "}
        {busy ? "Preparing reference…" : "Save voice profile"}
      </button>
    </dialog>
  );
}
