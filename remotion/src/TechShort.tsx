/**
 * TechShort : composition verticale 1080x1920 pour le compte IA / SEO Radius (iafortous).
 * Motion design 100 % code : fond vivant, hook typographique, scènes (chat, terminal, code,
 * carte d'outil ou de repo, liste, chiffre, avant/après, recherche locale, titre), sous-titres
 * mot par mot, barre de progression. Pas d'appel à l'abonnement ni de signature.
 * Piloté par timeline.json produit par factory/tech_motion.py.
 */
import React from "react";
import {
  AbsoluteFill,
  Img,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

// ------------------------------------------------------------------ types
export type TWord = { w: string; from: number; to: number; hl?: boolean };
export type TGroup = { from: number; to: number; words: TWord[] };
export type Scene = {
  from: number;
  dur: number;
  kind: string;
  trans?: string; // up | zoom | left | flash
  marks?: number[]; // frames (relatives à la scène) des révélations internes
  data: Record<string, unknown>;
};
export type TechShortProps = {
  durationInFrames: number;
  hook: { text: string; from: number; to: number; words: { w: string; from: number }[] } | null;
  scenes: Scene[];
  groups: TGroup[];
  stamps: { text: string; from: number; to: number }[];
  accent?: string;
  theme?: string; // ia | seo
};

const W = 1080;
const H = 1920;
const OV = 8;
const BG = "#07080C";
const INK = "#F5F7FA";
const MUTED = "#8A93A6";
const PANEL = "rgba(20,23,32,0.92)";
const LINE = "rgba(255,255,255,0.09)";
const LIME = "#D4FF3A";
const CYAN = "#3AD8FF";
const CORAL = "#FF6B4A";
const MONO = "JBMono, monospace";
const SANS = "InterX, sans-serif";

// ------------------------------------------------------------------ polices
const FONT_CSS = () => `
@font-face { font-family: 'InterX'; font-weight: 400; src: url('${staticFile("fonts/Inter-400.woff2")}') format('woff2'); }
@font-face { font-family: 'InterX'; font-weight: 700; src: url('${staticFile("fonts/Inter-700.woff2")}') format('woff2'); }
@font-face { font-family: 'InterX'; font-weight: 900; src: url('${staticFile("fonts/Inter-900.woff2")}') format('woff2'); }
@font-face { font-family: 'InterX'; font-weight: 400; src: url('${staticFile("fonts/Inter-ext-400.woff2")}') format('woff2'); unicode-range: U+0100-024F, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF; }
@font-face { font-family: 'InterX'; font-weight: 700; src: url('${staticFile("fonts/Inter-ext-700.woff2")}') format('woff2'); unicode-range: U+0100-024F, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF; }
@font-face { font-family: 'InterX'; font-weight: 900; src: url('${staticFile("fonts/Inter-ext-900.woff2")}') format('woff2'); unicode-range: U+0100-024F, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF; }
@font-face { font-family: 'JBMono'; font-weight: 400; src: url('${staticFile("fonts/jetbrains-mono-latin-400-normal.woff2")}') format('woff2'); }
@font-face { font-family: 'JBMono'; font-weight: 700; src: url('${staticFile("fonts/jetbrains-mono-latin-700-normal.woff2")}') format('woff2'); }
`;

const useFonts = () => {
  const [handle] = React.useState(() => delayRender("polices", { timeoutInMilliseconds: 20000 }));
  React.useEffect(() => {
    let done = false;
    const finish = () => {
      if (!done) {
        done = true;
        continueRender(handle);
      }
    };
    const t = setTimeout(finish, 6000);
    const fonts = (document as unknown as { fonts: { load: (f: string) => Promise<unknown> } }).fonts;
    Promise.all([fonts.load("900 80px InterX"), fonts.load("700 40px InterX"), fonts.load("400 40px InterX"),
      fonts.load("400 40px JBMono"), fonts.load("700 40px JBMono")])
      .then(finish)
      .catch(finish);
    return () => clearTimeout(t);
  }, [handle]);
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

function rnd(seed: number): number {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

const S = (v: unknown, d = ""): string => (v === undefined || v === null ? d : String(v));
const A = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);

// ------------------------------------------------------------------ fond
const Background: React.FC<{ accent: string; theme: string }> = ({ accent, theme }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const b1x = 540 + Math.sin(t * 0.35) * 260;
  const b1y = 520 + Math.cos(t * 0.27) * 180;
  const b2x = 540 + Math.cos(t * 0.31) * 300;
  const b2y = 1300 + Math.sin(t * 0.22) * 200;
  const second = theme === "seo" ? CYAN : CORAL;
  const gridShift = (frame * 0.6) % 90;
  return (
    <AbsoluteFill style={{ background: BG, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          inset: -100,
          backgroundImage: `linear-gradient(${LINE} 1px, transparent 1px), linear-gradient(90deg, ${LINE} 1px, transparent 1px)`,
          backgroundSize: "90px 90px",
          transform: `translateY(${gridShift}px)`,
          opacity: 0.55,
          maskImage: "radial-gradient(ellipse at 50% 45%, black 30%, transparent 75%)",
          WebkitMaskImage: "radial-gradient(ellipse at 50% 45%, black 30%, transparent 75%)",
        }}
      />
      <div style={{ position: "absolute", left: b1x - 450, top: b1y - 450, width: 900, height: 900, borderRadius: "50%",
        background: `radial-gradient(circle, ${accent}2E 0%, transparent 65%)`, filter: "blur(20px)" }} />
      <div style={{ position: "absolute", left: b2x - 420, top: b2y - 420, width: 840, height: 840, borderRadius: "50%",
        background: `radial-gradient(circle, ${second}24 0%, transparent 65%)`, filter: "blur(20px)" }} />
      <div style={{ position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at 50% 50%, transparent 55%, rgba(0,0,0,0.7) 100%)" }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ hook
const Hook: React.FC<{ hook: NonNullable<TechShortProps["hook"]>; accent: string }> = ({ hook, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame >= hook.to + 10) return null;
  const out = interpolate(frame, [hook.to - 2, hook.to + 8], [1, 0], clamp);
  const words = hook.words.length ? hook.words : hook.text.split(/\s+/).map((w, i) => ({ w, from: i * 4 }));
  const shake = frame < 8 ? (rnd(frame) - 0.5) * 18 : 0;
  const zoom = interpolate(frame, [0, hook.to], [1.0, 1.06], clamp);
  const n = words.length;
  const size = n <= 5 ? 128 : n <= 8 ? 112 : n <= 11 ? 96 : 84;
  return (
    <AbsoluteFill style={{ opacity: out, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(7,8,12,0.55)" }} />
      <div
        style={{
          width: 900,
          transform: `translate(${shake}px, ${-120 + shake / 2}px) scale(${zoom})`,
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1.04,
          letterSpacing: -2,
          color: INK,
          textAlign: "left",
        }}
      >
        {words.map((w, i) => {
          const local = frame - w.from;
          const p = spring({ frame: local, fps, config: { damping: 14, stiffness: 320, mass: 0.6 } });
          const hl = i === n - 1 || /[!?]$/.test(w.w) || w.w.length >= 9;
          return (
            <span key={i} style={{
              display: "inline-block",
              marginRight: 26,
              opacity: local >= 0 ? 1 : 0.08,
              transform: `translateY(${(1 - p) * 60}px) scale(${0.7 + 0.3 * p})`,
              color: hl && local >= 0 ? accent : INK,
            }}>{w.w}</span>
          );
        })}
      </div>
      {frame < 5 && <AbsoluteFill style={{ background: "#fff", opacity: interpolate(frame, [0, 5], [0.85, 0]) }} />}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ cadre de scène
const Panel: React.FC<{ children: React.ReactNode; title?: string; dots?: boolean; width?: number; style?: React.CSSProperties }> = (
  { children, title, dots = true, width = 900, style }
) => (
  <div style={{
    width, background: PANEL, borderRadius: 34, border: `1.5px solid ${LINE}`,
    boxShadow: "0 40px 120px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)", overflow: "hidden", ...style,
  }}>
    {dots && (
      <div style={{ height: 70, display: "flex", alignItems: "center", padding: "0 30px", borderBottom: `1.5px solid ${LINE}`, gap: 14 }}>
        {[CORAL, "#FFC53A", "#3ADB7A"].map((c) => (
          <div key={c} style={{ width: 20, height: 20, borderRadius: 10, background: c, opacity: 0.85 }} />
        ))}
        <div style={{ marginLeft: 18, fontFamily: MONO, fontSize: 26, color: MUTED }}>{title}</div>
      </div>
    )}
    {children}
  </div>
);

const typed = (text: string, frame: number, start: number, cps: number): string => {
  const n = Math.max(0, Math.floor(((frame - start) / 30) * cps));
  return text.slice(0, n);
};
const Caret: React.FC<{ color?: string }> = ({ color = LIME }) => {
  const frame = useCurrentFrame();
  return <span style={{ display: "inline-block", width: 16, height: "1em", marginLeft: 4, verticalAlign: "-0.12em",
    background: color, opacity: Math.floor(frame / 12) % 2 ? 0 : 1 }} />;
};

// ------------------------------------------------------------------ scènes
const Title: React.FC<{ d: Record<string, unknown>; local: number; accent: string }> = ({ d, local, accent }) => {
  const { fps } = useVideoConfig();
  const words = S(d.text).split(/\s+/).filter(Boolean);
  const hl = new Set(A(d.highlight).map((x) => S(x).toLowerCase()));
  const kicker = S(d.kicker);
  return (
    <div style={{ width: 900 }}>
      {kicker && (
        <div style={{ display: "inline-block", fontFamily: MONO, fontSize: 32, fontWeight: 700, color: BG, background: accent,
          padding: "10px 22px", borderRadius: 12, marginBottom: 34, letterSpacing: 1,
          transform: `translateX(${interpolate(local, [0, 10], [-40, 0], { ...clamp, easing: ease })}px)`,
          opacity: interpolate(local, [0, 6], [0, 1], clamp) }}>{kicker.toUpperCase()}</div>
      )}
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: words.length > 9 ? 88 : 104, lineHeight: 1.05, letterSpacing: -2, color: INK }}>
        {words.map((w, i) => {
          const p = spring({ frame: local - 4 - i * 3, fps, config: { damping: 16, stiffness: 240 } });
          const isHl = hl.has(w.toLowerCase().replace(/[.,!?:;]/g, ""));
          return (
            <span key={i} style={{ display: "inline-block", marginRight: 22, opacity: p, transform: `translateY(${(1 - p) * 50}px)`,
              color: isHl ? accent : INK }}>{w}</span>
          );
        })}
      </div>
      {S(d.sub) && (
        <div style={{ marginTop: 34, fontFamily: SANS, fontWeight: 700, fontSize: 44, color: MUTED, lineHeight: 1.3,
          opacity: interpolate(local, [18, 30], [0, 1], clamp) }}>{S(d.sub)}</div>
      )}
    </div>
  );
};

const Chat: React.FC<{ d: Record<string, unknown>; local: number; dur: number; accent: string }> = ({ d, local, dur, accent }) => {
  const { fps } = useVideoConfig();
  const user = S(d.user);
  const reply = S(d.assistant);
  const name = S(d.name, "Assistant IA");
  const userIn = spring({ frame: local - 2, fps, config: { damping: 15, stiffness: 220 } });
  const replyStart = 22;
  const cps = Math.max(28, (reply.length / Math.max(1, (dur - replyStart - 20) / 30)));
  const shown = typed(reply, local, replyStart, cps);
  const thinking = local >= 12 && local < replyStart;
  return (
    <Panel title={name.toLowerCase()} width={900}>
      <div style={{ padding: "36px 34px 40px", display: "flex", flexDirection: "column", gap: 30, minHeight: 640 }}>
        <div style={{ alignSelf: "flex-end", maxWidth: 680, background: "#2A2F3D", color: INK, fontFamily: SANS, fontWeight: 700,
          fontSize: 38, lineHeight: 1.32, padding: "24px 30px", borderRadius: "30px 30px 8px 30px",
          transform: `translateY(${(1 - userIn) * 40}px) scale(${0.92 + 0.08 * userIn})`, opacity: userIn }}>{user}</div>
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start", opacity: local >= 10 ? 1 : 0 }}>
          <div style={{ width: 62, height: 62, borderRadius: 18, background: accent, flexShrink: 0, display: "flex",
            alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 900, fontSize: 34, color: BG }}>
            {name.slice(0, 1).toUpperCase()}</div>
          <div style={{ fontFamily: SANS, fontWeight: 400, fontSize: 36, lineHeight: 1.42, color: "#DDE2EA", paddingTop: 6, whiteSpace: "pre-wrap" }}>
            {thinking ? (
              <span style={{ color: MUTED }}>{"réfléchit" + ".".repeat(1 + (Math.floor(local / 6) % 3))}</span>
            ) : (
              <>
                {shown}
                {shown.length < reply.length && <Caret color={accent} />}
              </>
            )}
          </div>
        </div>
      </div>
    </Panel>
  );
};

const Terminal: React.FC<{ d: Record<string, unknown>; local: number; dur: number; accent: string }> = ({ d, local, dur, accent }) => {
  const lines = A(d.lines).map((l) => (typeof l === "string" ? { cmd: l } : (l as Record<string, unknown>)));
  const total = lines.reduce((n, l) => n + S(l.cmd ?? l.out).length, 0) || 1;
  const cps = Math.max(30, total / Math.max(1, (dur - 24) / 30));
  let budget = Math.max(0, Math.floor(((local - 6) / 30) * cps));
  return (
    <Panel title={S(d.title, "terminal")} width={900}>
      <div style={{ padding: "34px 34px 44px", fontFamily: MONO, fontSize: 33, lineHeight: 1.55, color: "#DDE2EA", minHeight: 520 }}>
        {lines.map((l, i) => {
          const isCmd = l.cmd !== undefined;
          const txt = S(isCmd ? l.cmd : l.out);
          if (budget <= 0) return null;
          const shown = isCmd ? txt.slice(0, budget) : txt;
          budget -= isCmd ? txt.length : Math.max(8, Math.floor(txt.length / 4));
          return (
            <div key={i} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", color: isCmd ? INK : (S(l.ok) === "false" ? CORAL : "#7EE2A8") }}>
              {isCmd && <span style={{ color: accent }}>❯ </span>}
              {shown}
              {isCmd && budget <= 0 && <Caret color={accent} />}
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const KEYWORDS = /\b(const|let|var|function|return|import|from|def|class|if|else|for|in|await|async|export|print|True|False|None|new)\b/g;
const Code: React.FC<{ d: Record<string, unknown>; local: number; dur: number; accent: string }> = ({ d, local, dur, accent }) => {
  const code = S(d.code);
  const hl = new Set(A(d.highlight).map((x) => Number(x)));
  const cps = Math.max(40, code.length / Math.max(1, (dur * 0.6) / 30));
  const shown = typed(code, local, 6, cps);
  const done = shown.length >= code.length;
  return (
    <Panel title={S(d.file, "script")} width={900}>
      <div style={{ padding: "30px 0 40px", fontFamily: MONO, fontSize: 30, lineHeight: 1.6, minHeight: 480 }}>
        {shown.split("\n").map((line, i) => {
          const parts = line.split(/("[^"]*"?|'[^']*'?|#.*$|\/\/.*$)/);
          return (
            <div key={i} style={{ display: "flex", padding: "0 34px",
              background: done && hl.has(i + 1) ? `${accent}22` : "transparent",
              borderLeft: done && hl.has(i + 1) ? `6px solid ${accent}` : "6px solid transparent" }}>
              <span style={{ width: 54, color: "#4A5263", flexShrink: 0 }}>{i + 1}</span>
              <span style={{ whiteSpace: "pre-wrap", color: "#DDE2EA" }}>
                {parts.map((p, k) =>
                  /^["']/.test(p) ? <span key={k} style={{ color: "#FFC88A" }}>{p}</span>
                    : /^(#|\/\/)/.test(p) ? <span key={k} style={{ color: "#6B7488" }}>{p}</span>
                      : p.split(KEYWORDS).map((q, j) => (j % 2 ? <span key={j} style={{ color: CYAN }}>{q}</span> : q)))}
              </span>
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const Card: React.FC<{ d: Record<string, unknown>; local: number; accent: string }> = ({ d, local, accent }) => {
  const { fps } = useVideoConfig();
  const p = spring({ frame: local, fps, config: { damping: 14, stiffness: 180 } });
  const tags = A(d.tags).map((x) => S(x));
  const url = S(d.url);
  const urlIn = interpolate(local, [16, 28], [0, 1], clamp);
  return (
    <div style={{ transform: `translateY(${(1 - p) * 120}px) rotate(${(1 - p) * -4}deg)`, opacity: p }}>
      <Panel dots={false} width={900}>
        <div style={{ padding: "50px 50px 46px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
            <div style={{ width: 120, height: 120, borderRadius: 32, background: `${accent}22`, border: `2px solid ${accent}66`,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 66 }}>{S(d.emoji, "🧩")}</div>
            <div>
              <div style={{ fontFamily: MONO, fontSize: 28, color: MUTED }}>{S(d.owner)}</div>
              <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 64, color: INK, letterSpacing: -1, lineHeight: 1.05 }}>{S(d.name)}</div>
            </div>
          </div>
          <div style={{ marginTop: 34, fontFamily: SANS, fontWeight: 700, fontSize: 40, color: "#C9D0DB", lineHeight: 1.35 }}>{S(d.desc)}</div>
          {tags.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 30 }}>
              {tags.map((t, i) => (
                <div key={i} style={{ fontFamily: MONO, fontSize: 26, color: accent, border: `1.5px solid ${accent}55`, borderRadius: 40,
                  padding: "8px 20px", opacity: interpolate(local, [8 + i * 3, 14 + i * 3], [0, 1], clamp) }}>{t}</div>
              ))}
            </div>
          )}
          {(S(d.stars) || S(d.price)) && (
            <div style={{ marginTop: 30, display: "flex", gap: 40, fontFamily: SANS, fontWeight: 700, fontSize: 34, color: INK }}>
              {S(d.stars) && <span>★ {S(d.stars)}</span>}
              {S(d.price) && <span style={{ color: LIME }}>{S(d.price)}</span>}
            </div>
          )}
          {url && (
            <div style={{ marginTop: 36, padding: "20px 26px", borderRadius: 18, background: "#0E1016", border: `1.5px solid ${LINE}`,
              fontFamily: MONO, fontSize: 30, color: accent, opacity: urlIn, transform: `translateY(${(1 - urlIn) * 20}px)`,
              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>🔗 {url}</div>
          )}
        </div>
      </Panel>
    </div>
  );
};

const List: React.FC<{ d: Record<string, unknown>; local: number; dur: number; marks: number[]; accent: string }> = ({ d, local, dur, marks, accent }) => {
  const { fps } = useVideoConfig();
  const items = A(d.items).map((x) => S(x));
  const at = (i: number) => (marks[i] !== undefined ? marks[i] : 8 + Math.floor(((dur - 20) * i) / Math.max(1, items.length)));
  const current = items.reduce((c, _, i) => (local >= at(i) ? i : c), -1);
  return (
    <div style={{ width: 900 }}>
      {S(d.title) && (
        <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 70, color: INK, letterSpacing: -1.5, marginBottom: 40, lineHeight: 1.05,
          opacity: interpolate(local, [0, 8], [0, 1], clamp) }}>{S(d.title)}</div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        {items.map((it, i) => {
          const p = spring({ frame: local - at(i), fps, config: { damping: 15, stiffness: 230 } });
          const active = i === current;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, padding: "26px 30px", borderRadius: 26,
              background: active ? `${accent}1F` : PANEL, border: `2px solid ${active ? accent : LINE}`,
              opacity: local >= at(i) ? Math.max(0.0, p) * (active ? 1 : 0.62) : 0, transform: `translateX(${(1 - p) * 80}px)` }}>
              <div style={{ width: 70, height: 70, borderRadius: 20, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
                background: active ? accent : "#2A2F3D", color: active ? BG : INK, fontFamily: SANS, fontWeight: 900, fontSize: 38 }}>{i + 1}</div>
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 42, color: INK, lineHeight: 1.25 }}>{it}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Stat: React.FC<{ d: Record<string, unknown>; local: number; accent: string }> = ({ d, local, accent }) => {
  const target = Number(S(d.value, "0").replace(",", ".")) || 0;
  const p = interpolate(local, [4, 34], [0, 1], { ...clamp, easing: ease });
  const v = target * p;
  const dec = Number.isInteger(target) ? 0 : 1;
  const txt = v.toLocaleString("fr-FR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  return (
    <div style={{ width: 900, textAlign: "center" }}>
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 230, letterSpacing: -8, color: accent, lineHeight: 1,
        textShadow: `0 0 80px ${accent}55`, transform: `scale(${0.85 + 0.15 * p})` }}>
        {S(d.prefix)}{txt}{S(d.suffix)}
      </div>
      <div style={{ marginTop: 30, fontFamily: SANS, fontWeight: 700, fontSize: 50, color: INK, lineHeight: 1.25,
        opacity: interpolate(local, [14, 26], [0, 1], clamp) }}>{S(d.label)}</div>
      {S(d.source) && (
        <div style={{ marginTop: 24, fontFamily: MONO, fontSize: 26, color: MUTED, opacity: interpolate(local, [20, 30], [0, 1], clamp) }}>
          source : {S(d.source)}</div>
      )}
    </div>
  );
};

const Compare: React.FC<{ d: Record<string, unknown>; local: number; dur: number; accent: string }> = ({ d, local, dur, accent }) => {
  const left = (d.left ?? {}) as Record<string, unknown>;
  const right = (d.right ?? {}) as Record<string, unknown>;
  const mid = Math.max(18, Math.floor(dur * 0.42));
  const col = (side: Record<string, unknown>, start: number, good: boolean) => {
    const o = interpolate(local, [start, start + 10], [0, 1], clamp);
    return (
      <div style={{ flex: 1, padding: "34px 30px", borderRadius: 28, background: good ? `${accent}14` : "rgba(255,107,74,0.08)",
        border: `2px solid ${good ? accent : "rgba(255,107,74,0.5)"}`, opacity: o, transform: `translateY(${(1 - o) * 40}px)` }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 30, color: good ? accent : CORAL, marginBottom: 24 }}>
          {good ? "✓ " : "✕ "}{S(side.title).toUpperCase()}</div>
        {A(side.items).map((it, i) => (
          <div key={i} style={{ fontFamily: SANS, fontWeight: 700, fontSize: 36, color: INK, lineHeight: 1.3, marginBottom: 18,
            opacity: interpolate(local, [start + 6 + i * 6, start + 12 + i * 6], [0, 1], clamp) }}>{S(it)}</div>
        ))}
      </div>
    );
  };
  return (
    <div style={{ width: 920, display: "flex", gap: 22, alignItems: "stretch" }}>
      {col(left, 2, false)}
      {col(right, mid, true)}
    </div>
  );
};

const Search: React.FC<{ d: Record<string, unknown>; local: number; dur: number; accent: string }> = ({ d, local, dur, accent }) => {
  const query = S(d.query);
  const results = A(d.results).map((r) => r as Record<string, unknown>);
  const pick = Number(S(d.pick, "-1"));
  const shownQ = typed(query, local, 4, 26);
  const resStart = 6 + Math.ceil((query.length / 26) * 30) + 4;
  const pickAt = Math.max(resStart + 20, Math.floor(dur * 0.6));
  return (
    <Panel dots={false} width={900}>
      <div style={{ padding: "34px 34px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "22px 28px", borderRadius: 60, background: "#0E1016",
          border: `2px solid ${LINE}`, fontFamily: SANS, fontWeight: 700, fontSize: 36, color: INK }}>
          <span style={{ color: MUTED }}>⌕</span>{shownQ}{shownQ.length < query.length && <Caret color={accent} />}
        </div>
        <div style={{ position: "relative", height: 230, marginTop: 26, borderRadius: 24, overflow: "hidden", background: "#121620",
          border: `1.5px solid ${LINE}`, opacity: interpolate(local, [resStart - 4, resStart + 6], [0, 1], clamp) }}>
          {[...Array(7)].map((_, i) => (
            <div key={i} style={{ position: "absolute", left: 0, right: 0, top: 30 * i + 15, height: 2, background: "rgba(255,255,255,0.05)",
              transform: `rotate(${(rnd(i + 3) - 0.5) * 18}deg)` }} />
          ))}
          {results.slice(0, 4).map((_, i) => {
            const pin = spring({ frame: local - resStart - i * 4, fps: 30, config: { damping: 10, stiffness: 260 } });
            const sel = i === pick && local >= pickAt;
            return (
              <div key={i} style={{ position: "absolute", left: 120 + i * 190 + rnd(i) * 40, top: 50 + rnd(i + 9) * 90,
                transform: `translateY(${(1 - pin) * -60}px) scale(${sel ? 1.35 : 1})`, opacity: pin,
                width: 46, height: 46, borderRadius: "50% 50% 50% 0", rotate: "-45deg", background: sel ? accent : CORAL,
                boxShadow: sel ? `0 0 40px ${accent}` : "none" }} />
            );
          })}
        </div>
        <div style={{ marginTop: 22, display: "flex", flexDirection: "column", gap: 16 }}>
          {results.slice(0, 4).map((r, i) => {
            const o = interpolate(local, [resStart + 4 + i * 5, resStart + 12 + i * 5], [0, 1], clamp);
            const sel = i === pick && local >= pickAt;
            return (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 24px",
                borderRadius: 20, background: sel ? `${accent}1F` : "#141824", border: `2px solid ${sel ? accent : "transparent"}`,
                opacity: o, transform: `translateX(${(1 - o) * 50}px)` }}>
                <div>
                  <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 34, color: INK }}>{S(r.name)}</div>
                  <div style={{ fontFamily: SANS, fontSize: 26, color: MUTED, marginTop: 4 }}>{S(r.note)}</div>
                </div>
                <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 30, color: "#FFC53A" }}>{S(r.rating) && `★ ${S(r.rating)}`}</div>
              </div>
            );
          })}
        </div>
      </div>
    </Panel>
  );
};

const Shot: React.FC<{ d: Record<string, unknown>; local: number; dur: number }> = ({ d, local, dur }) => {
  // capture d'écran fournie par le run (public/img/...) : défilement doux, cadre arrondi
  const src = S(d.src);
  if (!src) return null;
  const y = interpolate(local, [0, dur], [0, -Number(S(d.scroll, "0"))], clamp);
  const z = interpolate(local, [0, dur], [1, 1.06], clamp);
  return (
    <Panel title={S(d.title)} width={900}>
      <div style={{ height: 900, overflow: "hidden", position: "relative" }}>
        <Img src={staticFile(src)} style={{ width: "100%", transform: `translateY(${y}px) scale(${z})`, transformOrigin: "top center" }} />
      </div>
    </Panel>
  );
};

const SceneLayer: React.FC<{ s: Scene; accent: string; isLast: boolean }> = ({ s, accent, isLast }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - s.from;
  const end = s.dur + (isLast ? 0 : OV);
  if (local < 0 || local >= end) return null;
  const inP = spring({ frame: local, fps, config: { damping: 18, stiffness: 170, mass: 0.8 } });
  const outP = isLast ? 0 : interpolate(local, [s.dur - 2, s.dur + OV], [0, 1], clamp);
  const t = s.trans ?? "up";
  let tf = "";
  if (t === "zoom") tf = `scale(${0.7 + 0.3 * inP})`;
  else if (t === "left") tf = `translateX(${(1 - inP) * 700}px)`;
  else tf = `translateY(${(1 - inP) * 260}px)`;
  tf += ` translateY(${-outP * 120}px) scale(${1 - outP * 0.06})`;
  const blur = (1 - inP) * 14 + outP * 12;
  const d = s.data;
  const marks = s.marks ?? [];
  const body = (() => {
    switch (s.kind) {
      case "chat": return <Chat d={d} local={local} dur={s.dur} accent={accent} />;
      case "terminal": return <Terminal d={d} local={local} dur={s.dur} accent={accent} />;
      case "code": return <Code d={d} local={local} dur={s.dur} accent={accent} />;
      case "card": return <Card d={d} local={local} accent={accent} />;
      case "list": return <List d={d} local={local} dur={s.dur} marks={marks} accent={accent} />;
      case "stat": return <Stat d={d} local={local} accent={accent} />;
      case "compare": return <Compare d={d} local={local} dur={s.dur} accent={accent} />;
      case "search": return <Search d={d} local={local} dur={s.dur} accent={accent} />;
      case "shot": return <Shot d={d} local={local} dur={s.dur} />;
      default: return <Title d={d} local={local} accent={accent} />;
    }
  })();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 210 }}>
      <div style={{ height: 1080, display: "flex", alignItems: "center", justifyContent: "center",
        transform: tf, opacity: Math.min(1, inP * 1.4) * (1 - outP), filter: `blur(${blur}px)` }}>
        {body}
      </div>
      {t === "flash" && local < 6 && (
        <AbsoluteFill style={{ background: accent, opacity: interpolate(local, [0, 6], [0.45, 0], clamp) }} />
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ sous-titres
const Captions: React.FC<{ groups: TGroup[]; accent: string }> = ({ groups, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = groups.find((x) => frame >= x.from && frame < x.to);
  if (!g) return null;
  const pop = spring({ frame: frame - g.from, fps, config: { damping: 13, stiffness: 280, mass: 0.5 } });
  return (
    <div style={{ position: "absolute", top: 1330, left: 50, right: 130, textAlign: "center",
      transform: `scale(${0.86 + 0.14 * pop})`, fontFamily: SANS, fontWeight: 900, fontSize: 76, lineHeight: 1.12,
      letterSpacing: -1, color: INK, textShadow: "0 6px 26px rgba(0,0,0,0.95)", WebkitTextStroke: "8px #07080C",
      paintOrder: "stroke fill" }}>
      {g.words.map((w, i) => {
        const active = frame >= w.from && frame < w.to;
        return (
          <span key={i} style={{ display: "inline-block", margin: "0 12px", color: w.hl ? accent : INK,
            transform: `translateY(${active ? -4 : 0}px)`, opacity: frame >= w.from - 1 ? 1 : 0.25 }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const Stamp: React.FC<{ s: { text: string; from: number; to: number }; accent: string }> = ({ s, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - s.from;
  if (local < 0 || frame >= s.to) return null;
  const p = spring({ frame: local, fps, config: { damping: 9, stiffness: 300, mass: 0.6 } });
  const o = interpolate(frame, [s.to - 6, s.to], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: o }}>
      <div style={{ transform: `translateY(-120px) rotate(-7deg) scale(${2.2 - 1.2 * p})`, fontFamily: SANS, fontWeight: 900,
        fontSize: 120, letterSpacing: -2, color: BG, background: accent, padding: "14px 44px", borderRadius: 20,
        boxShadow: `0 0 90px ${accent}88` }}>{s.text.toUpperCase()}</div>
    </AbsoluteFill>
  );
};

const Progress: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, height: 12, width: `${(frame / durationInFrames) * 100}%`,
      background: accent, boxShadow: `0 0 20px ${accent}` }} />
  );
};

// ------------------------------------------------------------------ composition
export const TechShort: React.FC<TechShortProps> = ({ hook, scenes, groups, stamps, accent, theme }) => {
  useFonts();
  const ac = accent || LIME;
  return (
    <AbsoluteFill style={{ width: W, height: H, background: BG }}>
      <style>{FONT_CSS()}</style>
      <Background accent={ac} theme={theme || "ia"} />
      {scenes.map((s, i) => (
        <SceneLayer key={i} s={s} accent={ac} isLast={i === scenes.length - 1} />
      ))}
      {hook && <Hook hook={hook} accent={ac} />}
      {stamps.map((s, i) => (
        <Stamp key={i} s={s} accent={ac} />
      ))}
      <Captions groups={groups} accent={ac} />
      <Progress accent={ac} />
    </AbsoluteFill>
  );
};
