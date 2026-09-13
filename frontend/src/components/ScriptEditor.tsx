export function ScriptEditor({
  text,
  onChange,
  saved,
}: {
  text: string;
  onChange: (value: string) => void;
  saved: boolean;
}) {
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  return (
    <section className="panel script-panel">
      <div className="panel-heading">
        <h2>Script</h2>
        <span className={saved ? "saved" : "failure"}>
          {saved ? "Saved locally" : "Autosave unavailable"}
        </span>
      </div>
      <div className="script-toolbar">
        <span>Plain text</span>
        <span>Natural pauses follow punctuation</span>
        <button onClick={() => onChange("")} disabled={!text}>
          Clear
        </button>
      </div>
      <textarea
        aria-label="Script"
        placeholder={
          "Every great story starts with a voice.\n\nWrite or paste your script here…"
        }
        maxLength={2000}
        value={text}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="script-footer">
        <span>
          {text.length.toLocaleString()} / 2,000 characters <b>·</b> {words}{" "}
          words
        </span>
        <span>~{Math.max(0, Math.round(words / 2.5))} sec</span>
      </div>
    </section>
  );
}
