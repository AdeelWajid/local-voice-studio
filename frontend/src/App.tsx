import { useEffect, useState } from "react";
import {
  AudioLines,
  Mic2,
  ArrowUpRight,
  ShieldCheck,
  Play,
  LoaderCircle,
  Square,
  Download,
  X,
  ChevronRight,
  Radio,
  FileAudio,
  Plus,
} from "lucide-react";
import { api, type Voice, type Job, type Model } from "./api";
import { VoiceImport } from "./components/VoiceImport";
import { ScriptEditor } from "./components/ScriptEditor";
import { useLocalScript } from "./hooks/useLocalScript";

export default function App() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [model, setModel] = useState<Model | null>(null);
  const [voice, setVoice] = useState("");
  const { text, setText, saved } = useLocalScript();
  const [language, setLanguage] = useState("EN");
  const [emotion, setEmotion] = useState([0, 0, 0, 0, 0, 0, 0, 0]);
  const [alpha, setAlpha] = useState(0.6);
  const [speed, setSpeed] = useState(1);
  const [emotionMode, setEmotionMode] = useState("vector");
  const [emotionText, setEmotionText] = useState("");
  const [emotionReferenceId, setEmotionReferenceId] = useState("");
  const [emotionReferenceName, setEmotionReferenceName] = useState("");
  const emotionNames = [
    "Happy",
    "Angry",
    "Sad",
    "Afraid",
    "Disgusted",
    "Melancholic",
    "Surprised",
    "Calm",
  ];
  const [error, setError] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [connected, setConnected] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [enhancing, setEnhancing] = useState(false);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [trimmedUrl, setTrimmedUrl] = useState<string | null>(null);
  const [waveform, setWaveform] = useState<number[]>([]);
  const [projectName, setProjectName] = useState("Untitled project");
  const active = jobs.find((j) => ["queued", "generating"].includes(j.status));
  const current =
    jobs.find((j) => j.id === selected) ||
    jobs.find((j) => j.status === "completed");
  async function enhanceCurrent() {
    if (!current || enhancing) return;
    setEnhancing(true);
    setError("");
    try {
      const result = await api<{ url: string }>("/audio/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: current.id,
          settings: {
            denoise: true,
            highpass: 80,
            compressor: true,
            normalize: true,
          },
        }),
      });
      setProcessedUrl(result.url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnhancing(false);
    }
  }
  async function trimCurrent() {
    if (!current || trimEnd <= trimStart) return;
    try {
      const result = await api<{ url: string }>("/audio/trim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: current.id,
          start: trimStart,
          end: trimEnd,
        }),
      });
      setTrimmedUrl(result.url);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function saveProject() {
    try {
      await api("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: projectName,
          script: text,
          settings: {
            voice_id: voice,
            language,
            emotion_mode: emotionMode,
            emotion_vector: emotion,
            emotion_alpha: alpha,
            duration_factor: speed,
          },
        }),
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    api<Voice[]>("/voices")
      .then((v) => {
        setVoices(v);
        setVoice(v[0]?.id || "");
      })
      .catch((e) => setError(e.message));
    let stopped = false,
      timer: ReturnType<typeof setTimeout>,
      socket: WebSocket;
    function connect() {
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/jobs`,
      );
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setJobs(data.jobs);
        setModel(data.model);
      };
      socket.onclose = () => {
        setConnected(false);
        if (!stopped) timer = setTimeout(connect, 2500);
      };
      socket.onerror = () => socket.close();
    }
    connect();
    return () => {
      stopped = true;
      clearTimeout(timer);
      socket.close();
    };
  }, []);
  useEffect(() => {
    if (!current || current.status !== "completed") {
      setWaveform([]);
      return;
    }
    api<{ peaks: number[] }>(`/jobs/${current.id}/waveform`)
      .then((result) => setWaveform(result.peaks))
      .catch(() => setWaveform([]));
  }, [current?.id, current?.status]);
  async function generate() {
    if (
      !voice ||
      !text.trim() ||
      busy ||
      !connected ||
      !model?.checkpoints_ready ||
      uploadOpen
    )
      return;
    setBusy(true);
    setError("");
    try {
      await api("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          voice_id: voice,
          language,
          emotion_mode: emotionMode,
          emotion_text: emotionText || null,
          emotion_reference_id: emotionReferenceId || null,
          emotion_vector: emotion,
          emotion_alpha: alpha,
          duration_factor: speed,
        }),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    function key(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        void generate();
      }
    }
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [
    text,
    voice,
    language,
    emotion,
    alpha,
    speed,
    emotionMode,
    emotionText,
    busy,
    connected,
    model?.checkpoints_ready,
    uploadOpen,
  ]);
  return (
    <div className="app">
      <aside className="rail">
        <div className="brand-icon">
          <AudioLines size={25} />
        </div>
        <button className="rail-active" title="Voice studio">
          <Radio size={21} />
        </button>
        <div className="rail-bottom">
          <ShieldCheck size={21} />
        </div>
      </aside>
      <div className="workspace">
        <header>
          <div className="brand">
            Local Voice Studio<span className="version">INDEXTTS 2.5</span>
          </div>
          <div className="system">
            <i className={connected ? "dot" : "dot offline"} />
            {connected
              ? "Local engine connected"
              : "Connecting to local engine"}
            <span className="divider" />
            <span className="model-state">
              {model?.state.replace("_", " ") || "Offline"}
            </span>
          </div>
        </header>
        <main>
          <div className="page-title">
            <div>
              <div className="eyebrow">YOUR VOICE. YOUR MACHINE.</div>
              <h1>Give your words a voice.</h1>
              <p>A private workspace for expressive, natural speech.</p>
            </div>
            <span className="local-badge">
              <ShieldCheck size={15} /> Local processing
            </span>
          </div>
          {error && (
            <div className="alert" role="alert">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {model?.error && (
            <div className="alert" role="alert">
              {model.error}
            </div>
          )}
          {model && !model.checkpoints_ready && !model.error && (
            <div className="alert" role="status">
              Model setup is incomplete. Finish downloading the IndexTTS
              checkpoints before generating speech.
            </div>
          )}
          <div className="studio-grid">
            <section className="panel voice-panel">
              <div className="panel-heading">
                <h2>
                  <Mic2 size={16} /> Voice
                </h2>
                <span className="muted">01</span>
              </div>
              <p className="section-help">Who is speaking?</p>
              <button
                className="upload-button"
                onClick={() => setUploadOpen(true)}
              >
                <Plus size={17} /> Add a voice <ArrowUpRight size={15} />
              </button>
              <div className="voice-list">
                {voices.length === 0 ? (
                  <div className="empty-voices">
                    <div className="empty-icon">
                      <Mic2 size={27} />
                    </div>
                    <h3>Your voice library starts here</h3>
                    <p>
                      Add a clean 5–15 second recording to create your first
                      voice.
                    </p>
                  </div>
                ) : (
                  voices.map((v) => (
                    <button
                      key={v.id}
                      className={
                        "voice-card " + (voice === v.id ? "selected" : "")
                      }
                      onClick={() => setVoice(v.id)}
                    >
                      <span className="avatar">
                        {v.name.slice(0, 2).toUpperCase()}
                      </span>
                      <span>
                        <strong>{v.name}</strong>
                        <small>{v.duration.toFixed(1)}s reference</small>
                      </span>
                      {voice === v.id && <i className="dot" />}
                    </button>
                  ))
                )}
              </div>
              {voice && (
                <div className="reference-player">
                  <span className="field-label">SPEAKER REFERENCE</span>
                  <audio controls src={`/api/voices/${voice}/audio`} />
                </div>
              )}
              <div className="voice-tip">
                <ShieldCheck size={16} />
                <p>
                  Your recordings and generated speech remain on this computer.
                </p>
              </div>
            </section>
            <ScriptEditor text={text} onChange={setText} saved={saved} />
            <section className="panel settings-panel">
              <div className="panel-heading">
                <h2>Direction</h2>
                <span className="muted">02</span>
              </div>
              <p className="section-help">Shape your performance.</p>
              <label className="field-label" htmlFor="language">
                LANGUAGE
              </label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {Object.entries(
                  model?.languages || {
                    EN: "English",
                    ZH: "Chinese",
                    JA: "Japanese",
                    ES: "Spanish",
                    AR: "Arabic",
                  },
                ).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
              <p className="hint">
                Choose the language of your script. Urdu and Hindi are not
                supported by this release.
              </p>
              <div className="emotion-box">
                <div className="field-row">
                  <span className="field-label">EMOTION MODE</span>
                </div>
                <select
                  aria-label="Emotion mode"
                  value={emotionMode}
                  onChange={(e) => setEmotionMode(e.target.value)}
                >
                  <option value="vector">Emotion mixer</option>
                  <option value="speaker">Speaker original</option>
                  <option value="description">Emotion description</option>
                  <option value="auto_text">Auto from script</option>
                  <option value="reference">Emotion reference audio</option>
                </select>
                {emotionMode === "reference" && (
                  <label className="upload-inline">
                    <span>{emotionReferenceName || "Choose a 3–60 second emotion reference"}</span>
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        const body = new FormData();
                        body.append("name", file.name.replace(/\.[^.]+$/, ""));
                        body.append("file", file);
                        try {
                          const ref = await api<{ id: string; name: string }>("/emotion-references", { method: "POST", body });
                          setEmotionReferenceId(ref.id);
                          setEmotionReferenceName(ref.name);
                        } catch (err) {
                          setError((err as Error).message);
                        }
                      }}
                    />
                  </label>
                )}
                {emotionMode === "description" && (
                  <textarea
                    className="emotion-prompt"
                    aria-label="Emotion description"
                    value={emotionText}
                    onChange={(e) => setEmotionText(e.target.value)}
                    maxLength={500}
                    placeholder="Speak softly with sadness, but remain composed…"
                  />
                )}
                <div className="field-row">
                  <span className="field-label">EMOTION MIXER</span>
                  <button
                    className="reset-link"
                    onClick={() => setEmotion([0, 0, 0, 0, 0, 0, 0, 0])}
                  >
                    Reset
                  </button>
                </div>
                {emotionNames.map((name, index) => (
                  <label className="slider-row" key={name}>
                    <span>{name}</span>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={emotion[index]}
                      onChange={(e) =>
                        setEmotion((previous) =>
                          previous.map((value, i) =>
                            i === index ? Number(e.target.value) : value,
                          ),
                        )
                      }
                    />
                    <output>{emotion[index].toFixed(2)}</output>
                  </label>
                ))}
                <label className="slider-row alpha-row">
                  <span>Strength</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={alpha}
                    onChange={(e) => setAlpha(Number(e.target.value))}
                  />
                  <output>{Math.round(alpha * 100)}%</output>
                </label>
                <label className="slider-row alpha-row">
                  <span>Speed</span>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.05"
                    value={speed}
                    onChange={(e) => setSpeed(Number(e.target.value))}
                  />
                  <output>{speed.toFixed(2)}×</output>
                </label>
              </div>
              <div className="direction-note">
                <AudioLines size={20} />
                <strong>Original expression</strong>
                <p>
                  This first generation uses the speaker reference’s natural
                  emotion and pace.
                </p>
              </div>
              <div className="generate-area">
                <button
                  className="primary generate"
                  disabled={
                    !voice ||
                    !text.trim() ||
                    busy ||
                    !connected ||
                    !model?.checkpoints_ready
                  }
                  onClick={() => void generate()}
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <Play size={16} fill="currentColor" />
                  )}
                  Generate speech
                  <ChevronRight size={17} />
                </button>
                <span className="shortcut">Ctrl ↵ to generate</span>
              </div>
            </section>
          </div>
          <section className="panel output-panel">
            <div className="panel-heading">
              <h2>
                <AudioLines size={17} /> Output
              </h2>
              <span className="muted">WAV · Original master</span>
            </div>
            {active && (
              <div className="progress">
                <LoaderCircle className="spin" size={16} />
                <span>
                  {active.status === "generating"
                    ? model?.state === "loading"
                      ? "Loading IndexTTS. The first run takes longer…"
                      : "Generating your speech…"
                    : "Waiting for the GPU…"}
                </span>
                <button
                  onClick={() =>
                    api(`/jobs/${active.id}/cancel`, { method: "POST" }).catch(
                      (e) => setError(e.message),
                    )
                  }
                >
                  <Square size={12} /> Cancel
                </button>
              </div>
            )}
            {current ? (
              <>
                {waveform.length > 0 && (
                  <div className="waveform" aria-label="Audio waveform">
                    {waveform.map((peak, index) => (
                      <span
                        key={index}
                        style={{ height: `${Math.max(4, peak * 100)}%` }}
                      />
                    ))}
                  </div>
                )}
                <div className="audio-result">
                  <div>
                    <span className="take-icon">
                      <FileAudio size={22} />
                    </span>
                    <strong>
                      Take{" "}
                      {jobs
                        .filter((j) => j.status === "completed")
                        .findIndex((j) => j.id === current.id) + 1}
                    </strong>
                    <span className="muted">
                      {current.duration?.toFixed(1)} sec
                    </span>
                  </div>
                  <audio
                    controls
                    src={
                      trimmedUrl ||
                      processedUrl ||
                      `/api/jobs/${current.id}/audio`
                    }
                  />
                  <button
                    className="secondary"
                    onClick={() => void enhanceCurrent()}
                    disabled={enhancing}
                  >
                    {enhancing
                      ? "Enhancing…"
                      : processedUrl
                        ? "Enhanced"
                        : "Enhance"}
                  </button>
                  <a
                    className="secondary"
                    href={`/api/jobs/${current.id}/audio`}
                    download
                  >
                    <Download size={16} /> WAV
                  </a>
                  <a
                    className="secondary"
                    href={`/api/jobs/${current.id}/export/flac`}
                    download
                  >
                    FLAC
                  </a>
                  <a
                    className="secondary"
                    href={`/api/jobs/${current.id}/export/mp3`}
                    download
                  >
                    MP3
                  </a>
                </div>
                <div className="editor-strip">
                  <span className="field-label">NON-DESTRUCTIVE TRIM</span>
                  <input
                    aria-label="Trim start"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="Start sec"
                    value={trimStart || ""}
                    onChange={(e) => setTrimStart(Number(e.target.value))}
                  />
                  <input
                    aria-label="Trim end"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="End sec"
                    value={trimEnd || ""}
                    onChange={(e) => setTrimEnd(Number(e.target.value))}
                  />
                  <button
                    className="secondary"
                    onClick={() => void trimCurrent()}
                    disabled={trimEnd <= trimStart}
                  >
                    Apply trim
                  </button>
                </div>
              </>
            ) : (
              <div className="output-empty">
                <AudioLines size={30} />
                <div>
                  <h3>Ready when you are</h3>
                  <p>
                    Your generated speech will appear here. Add a voice and
                    write your first line.
                  </p>
                </div>
              </div>
            )}
            {jobs.length > 0 && (
              <div className="job-list">
                {jobs.slice(0, 8).map((j) => (
                  <button
                    key={j.id}
                    className={"job " + (current?.id === j.id ? "chosen" : "")}
                    onClick={() =>
                      j.status === "completed" && setSelected(j.id)
                    }
                  >
                    <FileAudio size={16} />
                    <span>{JSON.parse(j.request).text.slice(0, 65)}</span>
                    <small className={j.status === "failed" ? "failure" : ""}>
                      {j.error || j.status}
                    </small>
                  </button>
                ))}
              </div>
            )}
          </section>
          <footer>
            <input
              className="project-name"
              aria-label="Project name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
            />
            <button
              className="secondary save-project"
              onClick={() => void saveProject()}
            >
              Save project
            </button>
            <span>
              <i className="dot" /> No cloud TTS. No account. Just your voice.
            </span>
            <span>Powered by IndexTTS 2.5</span>
          </footer>
        </main>
      </div>
      {uploadOpen && (
        <VoiceImport
          onClose={() => setUploadOpen(false)}
          onSaved={(result) => {
            setVoices((previous) => [result, ...previous]);
            setVoice(result.id);
            setUploadOpen(false);
          }}
        />
      )}
    </div>
  );
}
