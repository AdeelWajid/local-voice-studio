export type Voice = {
  id: string;
  name: string;
  duration: number;
  created: string;
};
export type Job = {
  id: string;
  status: string;
  request: string;
  error: string | null;
  duration: number | null;
  elapsed: number | null;
  created: string;
};
export type Model = {
  checkpoints_ready: boolean;
  state: string;
  error: string | null;
  model: string;
  device?: string | null;
  languages: Record<string, string>;
};
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api" + path, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({
      detail: "The local server could not complete the request.",
    }));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : body.detail?.map((x: { msg: string }) => x.msg).join(" ") ||
          "Request failed.",
    );
  }
  return response.json();
}
