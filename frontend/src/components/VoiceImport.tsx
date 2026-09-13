import { useEffect, useRef, useState } from "react";
import { LoaderCircle, Plus, Upload, X } from "lucide-react";
import { api, type Voice } from "../api";

export function VoiceImport({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: (voice: Voice) => void;
}) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);
  async function upload() {
    if (!file || !name.trim() || busy) return;
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("name", name);
    form.append("file", file);
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
      className="modal"
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
        noise.
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
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="file-input"
      />
      <button className="dropzone" onClick={() => input.current?.click()}>
        <Upload size={25} />
        <strong>{file?.name || "Choose a reference recording"}</strong>
        <span>WAV, MP3, FLAC, M4A, OGG · up to 50 MB</span>
      </button>
      <p className="consent">
        Only clone voices you own or have permission to use. Your original
        recording is preserved.
      </p>
      {error && (
        <p className="failure" role="alert">
          {error}
        </p>
      )}
      <button
        className="primary"
        disabled={!file || !name.trim() || busy}
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
