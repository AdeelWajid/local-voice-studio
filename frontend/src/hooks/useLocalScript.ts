import { useEffect, useState } from "react";

export function useLocalScript() {
  const [text, setText] = useState(() => {
    try {
      return localStorage.getItem("studio.script") || "";
    } catch {
      return "";
    }
  });
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    try {
      localStorage.setItem("studio.script", text);
      setSaved(true);
    } catch {
      setSaved(false);
    }
  }, [text]);
  return { text, setText, saved };
}
