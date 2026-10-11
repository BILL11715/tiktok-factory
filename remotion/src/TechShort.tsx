/**
 * TechShort : composition verticale 1080x1920 pour le compte IA / SEO Radius (iafortous).
 * Style "pop" clair : fond blanc cassé, cartes blanches cerclées de noir avec ombre franche,
 * une couleur vive par scène (fond, plaque, surlignage), formes qui flottent, affiche de
 * couverture sur les premières images (miniature du profil TikTok), sous-titres karaoké.
 * Piloté par timeline.json produit par factory/tech_motion.py. Pas d'appel à l'abonnement.
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
  marks?: number[];
  data: Record<string, unknown>;
};
export type Cover = { text: string; highlight?: string[]; emoji?: string; badge?: string; sub?: string };
export type TechShortProps = {
  durationInFrames: number;
  hook: { text: string; from: number; to: number; words: { w: string; from: number }[] } | null;
  scenes: Scene[];
  groups: TGroup[];
  stamps: { text: string; from: number; to: number }[];
  accent?: string;
  theme?: string; // ia | seo
  cover?: Cover | null;
};

const W = 1080;
const H = 1920;
const OV = 8;
const BG = "#F6F2EA";
const INK = "#15171E";
const MUTED = "#5E6472";
const WHITE = "#FFFFFF";
const POP = ["#FFC83D", "#FF7AA8", "#6FA8FF", "#4ADE80", "#B79CFF", "#FFA552"];
const DEFAULT_ACCENT: Record<string, string> = { seo: "#2F6BFF", ia: "#12B76A" };
const MONO = "JBMono, monospace";
const SANS = "InterX, sans-serif";
const BORDER = `4px solid ${INK}`;
const hard = (n = 12, c = INK) => `${n}px ${n}px 0 ${c}`;
const COVER_FRAMES = 22;

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
const norm = (w: string) => w.toLowerCase().replace(/[.,!?:;«»"'’()]/g, "");
const popOf = (i: number) => POP[((i % POP.length) + POP.length) % POP.length];

// ------------------------------------------------------------------ fond vivant
const Shape: React.FC<{ i: number; color: string }> = ({ i, color }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  // positions sur les bords (le centre reste libre pour le contenu)
  const side = i % 2 === 0 ? -1 : 1;
  const x = 540 + side * (380 + rnd(i + 1) * 120) + Math.sin(t * (0.4 + rnd(i) * 0.4) + i) * 30;
  const y = 160 + ((rnd(i + 7) * 1600 + t * (18 + rnd(i + 3) * 22)) % 1700);
  const rot = t * (20 + rnd(i + 5) * 40) * side;
  const size = 50 + rnd(i + 11) * 50;
  const kind = i % 5;
  const base: React.CSSProperties = { position: "absolute", left: x - size / 2, top: y - size / 2, width: size, height: size,
    transform: `rotate(${rot}deg)`, opacity: 0.9 };
  if (kind === 0) return <div style={{ ...base, borderRadius: "50%", background: color, border: `4px solid ${INK}` }} />;
  if (kind === 1) return <div style={{ ...base, borderRadius: "50%", border: `8px solid ${color}`, boxSizing: "border-box" }} />;
  if (kind === 2) return <div style={{ ...base, borderRadius: 14, background: color, border: `4px solid ${INK}` }} />;
  if (kind === 3)
    return (
      <div style={{ ...base, fontFamily: SANS, fontWeight: 900, fontSize: size * 1.3, lineHeight: `${size}px`, textAlign: "center",
        color, WebkitTextStroke: `3px ${INK}` }}>+</div>
    );
  return <div style={{ ...base, background: color, clipPath: "polygon(50% 0, 100% 100%, 0 100%)" }} />;
};

const Background: React.FC<{ tint: string }> = ({ tint }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const b1x = 540 + Math.sin(t * 0.35) * 280;
  const b1y = 560 + Math.cos(t * 0.27) * 200;
  const b2x = 540 + Math.cos(t * 0.31) * 320;
  const b2y = 1350 + Math.sin(t * 0.22) * 200;
  return (
    <AbsoluteFill style={{ background: BG, overflow: "hidden" }}>
      <div style={{ position: "absolute", left: b1x - 520, top: b1y - 520, width: 1040, height: 1040, borderRadius: "50%",
        background: `radial-gradient(circle, ${tint}66 0%, ${tint}00 65%)` }} />
      <div style={{ position: "absolute", left: b2x - 480, top: b2y - 480, width: 960, height: 960, borderRadius: "50%",
        background: `radial-gradient(circle, ${tint}40 0%, ${tint}00 65%)` }} />
      <div style={{ position: "absolute", inset: -60,
        backgroundImage: `radial-gradient(${INK}22 2.5px, transparent 2.5px)`, backgroundSize: "46px 46px",
        transform: `translateY(${(frame * 0.5) % 46}px)` }} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Shape key={i} i={i} color={popOf(i + 1)} />
      ))}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ affiche de couverture
const CoverPoster: React.FC<{ cover: Cover; accent: string; theme: string }> = ({ cover, accent, theme }) => {
  const frame = useCurrentFrame();
  if (frame >= COVER_FRAMES + 10) return null;
  const out = interpolate(frame, [COVER_FRAMES - 4, COVER_FRAMES + 8], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const words = S(cover.text).split(/\s+/).filter(Boolean);
  const hl = new Set(A(cover.highlight).map((x) => norm(S(x))));
  const n = words.length;
  const size = n <= 3 ? 150 : n <= 5 ? 128 : n <= 7 ? 110 : 96;
  const badge = S(cover.badge, theme === "seo" ? "SEO RADIUS" : "IA POUR TOUS");
  const cardColor = theme === "seo" ? POP[0] : POP[3];
  return (
    <AbsoluteFill style={{ background: BG, transform: `translateY(${out * -1900}px) rotate(${out * -8}deg)` }}>
      <AbsoluteFill style={{ backgroundImage: `radial-gradient(${INK}22 2.5px, transparent 2.5px)`, backgroundSize: "46px 46px" }} />
      {/* stickers décoratifs */}
      <div style={{ position: "absolute", left: 70, top: 250, width: 120, height: 120, borderRadius: "50%", background: POP[1], border: BORDER }} />
      <div style={{ position: "absolute", right: 80, top: 1560, width: 140, height: 140, borderRadius: 26, background: POP[2], border: BORDER,
        transform: "rotate(14deg)" }} />
      <div style={{ position: "absolute", right: 110, top: 300, fontFamily: SANS, fontWeight: 900, fontSize: 150, color: POP[4],
        WebkitTextStroke: `5px ${INK}` }}>+</div>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 920, padding: "70px 64px 80px", background: cardColor, border: `6px solid ${INK}`, borderRadius: 48,
          boxShadow: hard(20), transform: "rotate(-2deg)", position: "relative" }}>
          <div style={{ display: "inline-block", fontFamily: SANS, fontWeight: 900, fontSize: 36, letterSpacing: 2, color: WHITE,
            background: INK, padding: "12px 26px", borderRadius: 40 }}>{badge}</div>
          {S(cover.emoji) && (
            <div style={{ position: "absolute", right: 50, top: -90, fontSize: 190, transform: "rotate(10deg)",
              filter: `drop-shadow(8px 8px 0 ${INK})` }}>{S(cover.emoji)}</div>
          )}
          <div style={{ marginTop: 44, fontFamily: SANS, fontWeight: 900, fontSize: size, lineHeight: 1.0, letterSpacing: -4,
            color: INK, textTransform: "uppercase" }}>
            {words.map((w, i) => {
              const isHl = hl.has(norm(w));
              return (
                <span key={i} style={{ display: "inline-block", marginRight: 24, marginBottom: 10,
                  ...(isHl ? { background: WHITE, border: BORDER, borderRadius: 18, padding: "0 18px", transform: "rotate(-3deg)",
                    color: accent, boxShadow: hard(8) } : {}) }}>{w}</span>
              );
            })}
          </div>
          {S(cover.sub) && (
            <div style={{ marginTop: 40, display: "inline-block", fontFamily: SANS, fontWeight: 900, fontSize: 46, color: INK,
              background: WHITE, border: BORDER, borderRadius: 60, padding: "14px 34px" }}>{S(cover.sub)} →</div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ hook
const Hook: React.FC<{ hook: NonNullable<TechShortProps["hook"]>; accent: string; start: number }> = ({ hook, accent, start }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame >= hook.to + 10) return null;
  const out = interpolate(frame, [hook.to - 2, hook.to + 8], [1, 0], clamp);
  const words = hook.words.length ? hook.words : hook.text.split(/\s+/).map((w, i) => ({ w, from: i * 4 }));
  const zoom = interpolate(frame, [0, hook.to], [1.0, 1.06], clamp);
  const n = words.length;
  const size = n <= 5 ? 132 : n <= 8 ? 116 : n <= 11 ? 100 : 88;
  return (
    <AbsoluteFill style={{ opacity: out, justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 920, transform: `translateY(-120px) scale(${zoom})`, fontFamily: SANS, fontWeight: 900, fontSize: size,
        lineHeight: 1.08, letterSpacing: -3, color: INK, textAlign: "left" }}>
        {words.map((w, i) => {
          const local = frame - Math.max(w.from, start + i * 2);
          const p = spring({ frame: local, fps, config: { damping: 11, stiffness: 300, mass: 0.6 } });
          const hl = i === n - 1 || /[!?]$/.test(w.w) || w.w.length >= 9;
          return (
            <span key={i} style={{
              display: "inline-block", marginRight: 24, marginBottom: 8, padding: hl ? "0 14px" : 0, borderRadius: 16,
              opacity: local >= 0 ? 1 : 0,
              background: hl && local >= 0 ? popOf(i) : "transparent",
              border: hl && local >= 0 ? BORDER : "4px solid transparent",
              transform: `translateY(${(1 - p) * 70}px) rotate(${hl ? -2 : 0}deg) scale(${0.6 + 0.4 * p})`,
            }}>{w.w}</span>
          );
        })}
      </div>
      <div style={{ position: "absolute", top: 1240, left: 80, width: interpolate(frame, [start, hook.to], [0, 920], clamp), height: 18,
        background: accent, border: BORDER, borderRadius: 12 }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ cadre de scène
const Panel: React.FC<{ children: React.ReactNode; title?: string; dots?: boolean; width?: number; dark?: boolean; style?: React.CSSProperties }> = (
  { children, title, dots = true, width = 900, dark = false, style }
) => (
  <div style={{ width, background: dark ? INK : WHITE, borderRadius: 36, border: BORDER, boxShadow: hard(14), overflow: "hidden", ...style }}>
    {dots && (
      <div style={{ height: 74, display: "flex", alignItems: "center", padding: "0 30px", gap: 14,
        background: dark ? "#262A35" : "#EFEBE3", borderBottom: BORDER }}>
        {[POP[1], POP[0], POP[3]].map((c) => (
          <div key={c} style={{ width: 24, height: 24, borderRadius: 12, background: c, border: `3px solid ${INK}` }} />
        ))}
        <div style={{ marginLeft: 18, fontFamily: MONO, fontWeight: 700, fontSize: 28, color: dark ? "#C9CED8" : MUTED }}>{title}</div>
      </div>
    )}
    {children}
  </div>
);

const typed = (text: string, frame: number, start: number, cps: number): string => {
  const n = Math.max(0, Math.floor(((frame - start) / 30) * cps));
  return text.slice(0, n);
};
const Caret: React.FC<{ color?: string }> = ({ color = INK }) => {
  const frame = useCurrentFrame();
  return <span style={{ display: "inline-block", width: 16, height: "1em", marginLeft: 4, verticalAlign: "-0.12em",
    background: color, opacity: Math.floor(frame / 12) % 2 ? 0 : 1 }} />;
};

// ------------------------------------------------------------------ scènes
type SP = { d: Record<string, unknown>; local: number; dur: number; accent: string; pop: string; marks: number[] };

const Title: React.FC<SP> = ({ d, local, pop }) => {
  const { fps } = useVideoConfig();
  const words = S(d.text).split(/\s+/).filter(Boolean);
  const hl = new Set(A(d.highlight).length ? A(d.highlight).map((x) => norm(S(x))) : S(d.highlight).split(/\s+/).map(norm));
  const kicker = S(d.kicker);
  return (
    <div style={{ width: 900 }}>
      {kicker && (
        <div style={{ display: "inline-block", fontFamily: MONO, fontSize: 34, fontWeight: 700, color: INK, background: pop,
          border: BORDER, boxShadow: hard(6), padding: "12px 26px", borderRadius: 14, marginBottom: 40, letterSpacing: 1,
          transform: `translateX(${interpolate(local, [0, 10], [-60, 0], { ...clamp, easing: ease })}px) rotate(-2deg)`,
          opacity: interpolate(local, [0, 6], [0, 1], clamp) }}>{kicker.toUpperCase()}</div>
      )}
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: words.length > 9 ? 92 : 112, lineHeight: 1.08, letterSpacing: -3, color: INK }}>
        {words.map((w, i) => {
          const p = spring({ frame: local - 4 - i * 3, fps, config: { damping: 12, stiffness: 240 } });
          const isHl = hl.has(norm(w));
          const mark = interpolate(local, [10 + i * 3, 22 + i * 3], [0, 100], clamp);
          return (
            <span key={i} style={{ display: "inline-block", marginRight: 22, marginBottom: 6, opacity: p, padding: isHl ? "0 12px" : 0,
              transform: `translateY(${(1 - p) * 60}px)`, borderRadius: 12,
              background: isHl ? `linear-gradient(90deg, ${pop} ${mark}%, transparent ${mark}%)` : "transparent" }}>{w}</span>
          );
        })}
      </div>
      {S(d.sub) && (
        <div style={{ marginTop: 40, display: "inline-block", fontFamily: SANS, fontWeight: 700, fontSize: 44, color: INK, lineHeight: 1.3,
          background: WHITE, border: BORDER, borderRadius: 50, padding: "12px 30px",
          opacity: interpolate(local, [18, 30], [0, 1], clamp) }}>{S(d.sub)}</div>
      )}
    </div>
  );
};

const Chat: React.FC<SP> = ({ d, local, dur, accent, pop }) => {
  const { fps } = useVideoConfig();
  const user = S(d.user);
  const reply = S(d.assistant);
  const name = S(d.name, "Assistant IA");
  const userIn = spring({ frame: local - 2, fps, config: { damping: 12, stiffness: 220 } });
  const replyStart = 22;
  const cps = Math.max(28, reply.length / Math.max(1, (dur - replyStart - 20) / 30));
  const shown = typed(reply, local, replyStart, cps);
  const thinking = local >= 12 && local < replyStart;
  return (
    <Panel title={name.toLowerCase()} width={900}>
      <div style={{ padding: "36px 34px 40px", display: "flex", flexDirection: "column", gap: 30, minHeight: 640 }}>
        <div style={{ alignSelf: "flex-end", maxWidth: 680, background: pop, color: INK, fontFamily: SANS, fontWeight: 700,
          fontSize: 38, lineHeight: 1.32, padding: "24px 30px", borderRadius: "30px 30px 8px 30px", border: BORDER, boxShadow: hard(6),
          transform: `translateY(${(1 - userIn) * 40}px) scale(${0.9 + 0.1 * userIn})`, opacity: userIn }}>{user}</div>
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start", opacity: local >= 10 ? 1 : 0 }}>
          <div style={{ width: 66, height: 66, borderRadius: 20, background: accent, flexShrink: 0, display: "flex", border: BORDER,
            alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 900, fontSize: 34, color: WHITE }}>
            {name.slice(0, 1).toUpperCase()}</div>
          <div style={{ fontFamily: SANS, fontWeight: 400, fontSize: 36, lineHeight: 1.42, color: INK, paddingTop: 6, whiteSpace: "pre-wrap" }}>
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

const Terminal: React.FC<SP> = ({ d, local, dur, pop }) => {
  const lines = A(d.lines).map((l) => (typeof l === "string" ? { cmd: l } : (l as Record<string, unknown>)));
  const total = lines.reduce((n, l) => n + S(l.cmd ?? l.out).length, 0) || 1;
  const cps = Math.max(30, total / Math.max(1, (dur - 24) / 30));
  let budget = Math.max(0, Math.floor(((local - 6) / 30) * cps));
  return (
    <Panel title={S(d.title, "terminal")} width={900} dark>
      <div style={{ padding: "34px 34px 44px", fontFamily: MONO, fontSize: 33, lineHeight: 1.55, color: "#E6E9EF", minHeight: 520 }}>
        {lines.map((l, i) => {
          const isCmd = l.cmd !== undefined;
          const txt = S(isCmd ? l.cmd : l.out);
          if (budget <= 0) return null;
          const shown = isCmd ? txt.slice(0, budget) : txt;
          budget -= isCmd ? txt.length : Math.max(8, Math.floor(txt.length / 4));
          return (
            <div key={i} style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", color: isCmd ? WHITE : (S(l.ok) === "false" ? POP[1] : POP[3]) }}>
              {isCmd && <span style={{ color: pop }}>❯ </span>}
              {shown}
              {isCmd && budget <= 0 && <Caret color={pop} />}
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const KEYWORDS = /\b(const|let|var|function|return|import|from|def|class|if|else|for|in|await|async|export|print|True|False|None|new)\b/g;
const Code: React.FC<SP> = ({ d, local, dur, pop }) => {
  const code = S(d.code);
  const hl = new Set(A(d.highlight).map((x) => Number(x)));
  const cps = Math.max(40, code.length / Math.max(1, (dur * 0.6) / 30));
  const shown = typed(code, local, 6, cps);
  const done = shown.length >= code.length;
  return (
    <Panel title={S(d.file, "script")} width={900} dark>
      <div style={{ padding: "30px 0 40px", fontFamily: MONO, fontSize: 30, lineHeight: 1.6, minHeight: 480 }}>
        {shown.split("\n").map((line, i) => {
          const parts = line.split(/("[^"]*"?|'[^']*'?|#.*$|\/\/.*$)/);
          return (
            <div key={i} style={{ display: "flex", padding: "0 34px",
              background: done && hl.has(i + 1) ? `${pop}33` : "transparent",
              borderLeft: done && hl.has(i + 1) ? `8px solid ${pop}` : "8px solid transparent" }}>
              <span style={{ width: 54, color: "#5A6275", flexShrink: 0 }}>{i + 1}</span>
              <span style={{ whiteSpace: "pre-wrap", color: "#E6E9EF" }}>
                {parts.map((p, k) =>
                  /^["']/.test(p) ? <span key={k} style={{ color: POP[0] }}>{p}</span>
                    : /^(#|\/\/)/.test(p) ? <span key={k} style={{ color: "#7D8598" }}>{p}</span>
                      : p.split(KEYWORDS).map((q, j) => (j % 2 ? <span key={j} style={{ color: POP[2] }}>{q}</span> : q)))}
              </span>
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const Card: React.FC<SP> = ({ d, local, pop }) => {
  const tags = A(d.tags).map((x) => S(x));
  const url = S(d.url);
  const urlIn = interpolate(local, [16, 28], [0, 1], clamp);
  return (
    <Panel dots={false} width={900}>
      <div style={{ padding: "50px 50px 46px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <div style={{ width: 130, height: 130, borderRadius: 32, background: pop, border: BORDER, boxShadow: hard(6),
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 72 }}>{S(d.emoji, "🧩")}</div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: 30, color: MUTED }}>{S(d.owner)}</div>
            <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 66, color: INK, letterSpacing: -1.5, lineHeight: 1.05 }}>{S(d.name)}</div>
          </div>
        </div>
        <div style={{ marginTop: 34, fontFamily: SANS, fontWeight: 700, fontSize: 40, color: INK, lineHeight: 1.35 }}>{S(d.desc)}</div>
        {tags.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 30 }}>
            {tags.map((t, i) => (
              <div key={i} style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26, color: INK, background: popOf(i + 2), border: `3px solid ${INK}`,
                borderRadius: 40, padding: "8px 20px", opacity: interpolate(local, [8 + i * 3, 14 + i * 3], [0, 1], clamp) }}>{t}</div>
            ))}
          </div>
        )}
        {(S(d.stars) || S(d.price)) && (
          <div style={{ marginTop: 30, display: "flex", gap: 40, fontFamily: SANS, fontWeight: 900, fontSize: 38, color: INK }}>
            {S(d.stars) && <span>⭐ {S(d.stars)}</span>}
            {S(d.price) && <span style={{ background: POP[3], border: `3px solid ${INK}`, borderRadius: 14, padding: "0 16px" }}>{S(d.price)}</span>}
          </div>
        )}
        {url && (
          <div style={{ marginTop: 36, padding: "20px 26px", borderRadius: 18, background: INK, fontFamily: MONO, fontSize: 30, color: WHITE,
            opacity: urlIn, transform: `translateY(${(1 - urlIn) * 20}px)`, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>🔗 {url}</div>
        )}
      </div>
    </Panel>
  );
};

const List: React.FC<SP> = ({ d, local, dur, marks, pop }) => {
  const { fps } = useVideoConfig();
  const items = A(d.items).map((x) => S(x));
  const at = (i: number) => (marks[i] !== undefined && marks[i] !== null ? marks[i] : 8 + Math.floor(((dur - 20) * i) / Math.max(1, items.length)));
  const current = items.reduce((c, _, i) => (local >= at(i) ? i : c), -1);
  return (
    <div style={{ width: 900 }}>
      {S(d.title) && (
        <div style={{ display: "inline-block", fontFamily: SANS, fontWeight: 900, fontSize: 72, color: INK, letterSpacing: -2, marginBottom: 44,
          lineHeight: 1.05, background: pop, border: BORDER, boxShadow: hard(8), borderRadius: 20, padding: "8px 26px",
          transform: "rotate(-1.5deg)", opacity: interpolate(local, [0, 8], [0, 1], clamp) }}>{S(d.title)}</div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
        {items.map((it, i) => {
          const p = spring({ frame: local - at(i), fps, config: { damping: 12, stiffness: 230 } });
          const active = i === current;
          const done = i < current;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, padding: "24px 28px", borderRadius: 26,
              background: active ? pop : WHITE, border: BORDER, boxShadow: hard(active ? 10 : 6),
              opacity: local >= at(i) ? Math.max(0, p) : 0,
              transform: `translateX(${(1 - p) * 120}px) scale(${active ? 1.03 : 1})` }}>
              <div style={{ width: 72, height: 72, borderRadius: 36, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center",
                background: done ? POP[3] : INK, color: done ? INK : WHITE, border: BORDER, fontFamily: SANS, fontWeight: 900, fontSize: 38 }}>
                {done ? "✓" : i + 1}</div>
              <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 44, color: INK, lineHeight: 1.2 }}>{it}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Stat: React.FC<SP> = ({ d, local, pop }) => {
  const { fps } = useVideoConfig();
  const target = Number(S(d.value, "0").replace(",", ".")) || 0;
  const p = interpolate(local, [4, 34], [0, 1], { ...clamp, easing: ease });
  const v = target * p;
  const dec = Number.isInteger(target) ? 0 : 1;
  const txt = v.toLocaleString("fr-FR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const bump = spring({ frame: local - 34, fps, config: { damping: 8, stiffness: 300 } });
  return (
    <div style={{ width: 900, textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ display: "inline-block", background: pop, border: `6px solid ${INK}`, boxShadow: hard(16), borderRadius: 40,
        padding: "20px 56px", transform: `rotate(-2deg) scale(${0.85 + 0.15 * p + 0.05 * Math.sin(bump * Math.PI)})` }}>
        <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 220, letterSpacing: -8, color: INK, lineHeight: 1 }}>
          {S(d.prefix)}{txt}{S(d.suffix)}
        </div>
      </div>
      <div style={{ marginTop: 50, fontFamily: SANS, fontWeight: 900, fontSize: 54, color: INK, lineHeight: 1.2,
        opacity: interpolate(local, [14, 26], [0, 1], clamp) }}>{S(d.label)}</div>
      {S(d.source) && (
        <div style={{ marginTop: 24, fontFamily: MONO, fontSize: 28, color: MUTED, opacity: interpolate(local, [20, 30], [0, 1], clamp) }}>
          source : {S(d.source)}</div>
      )}
    </div>
  );
};

const Compare: React.FC<SP> = ({ d, local, dur }) => {
  const left = (d.left ?? {}) as Record<string, unknown>;
  const right = (d.right ?? {}) as Record<string, unknown>;
  const mid = Math.max(18, Math.floor(dur * 0.42));
  const col = (side: Record<string, unknown>, start: number, good: boolean) => {
    const o = spring({ frame: local - start, fps: 30, config: { damping: 12, stiffness: 200 } });
    return (
      <div style={{ flex: 1, minHeight: 560, padding: "34px 28px", borderRadius: 30, background: good ? "#C9F7D9" : "#FFD6E2", border: BORDER,
        boxShadow: hard(good ? 12 : 6), opacity: Math.min(1, o), transform: `translateY(${(1 - o) * 80}px) rotate(${good ? 1.5 : -1.5}deg)` }}>
        <div style={{ display: "inline-block", fontFamily: MONO, fontWeight: 700, fontSize: 28, color: WHITE, background: good ? "#12A150" : "#E5484D",
          borderRadius: 30, padding: "8px 18px", marginBottom: 30, border: `3px solid ${INK}` }}>
          {good ? "✓ " : "✕ "}{S(side.title).toUpperCase()}</div>
        {A(side.items).map((it, i) => (
          <div key={i} style={{ fontFamily: SANS, fontWeight: 900, fontSize: 46, color: INK, lineHeight: 1.2, marginBottom: 24,
            opacity: interpolate(local, [start + 6 + i * 6, start + 12 + i * 6], [0, 1], clamp) }}>{S(it)}</div>
        ))}
      </div>
    );
  };
  return (
    <div style={{ width: 940, display: "flex", gap: 26, alignItems: "stretch" }}>
      {col(left, 2, false)}
      {col(right, mid, true)}
    </div>
  );
};

const Search: React.FC<SP> = ({ d, local, dur, accent, pop }) => {
  const query = S(d.query);
  const results = A(d.results).map((r) => r as Record<string, unknown>);
  const pick = Number(S(d.pick, "-1"));
  const shownQ = typed(query, local, 4, 26);
  const resStart = 6 + Math.ceil((query.length / 26) * 30) + 4;
  const pickAt = Math.max(resStart + 20, Math.floor(dur * 0.6));
  return (
    <Panel dots={false} width={900}>
      <div style={{ padding: "34px 34px 40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "22px 28px", borderRadius: 60, background: WHITE,
          border: BORDER, boxShadow: hard(6), fontFamily: SANS, fontWeight: 700, fontSize: 38, color: INK }}>
          <span>🔍</span>{shownQ}{shownQ.length < query.length && <Caret color={accent} />}
        </div>
        <div style={{ position: "relative", height: 240, marginTop: 30, borderRadius: 24, overflow: "hidden", background: "#E4EEDC",
          border: BORDER, opacity: interpolate(local, [resStart - 4, resStart + 6], [0, 1], clamp) }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} style={{ position: "absolute", left: -40, right: -40, top: 40 * i + 10, height: 14, background: WHITE,
              transform: `rotate(${(rnd(i + 3) - 0.5) * 24}deg)` }} />
          ))}
          <div style={{ position: "absolute", left: 600, top: 30, width: 180, height: 120, borderRadius: 30, background: "#BFE0F5" }} />
          {results.slice(0, 4).map((_, i) => {
            const pin = spring({ frame: local - resStart - i * 4, fps: 30, config: { damping: 9, stiffness: 260 } });
            const sel = i === pick && local >= pickAt;
            return (
              <div key={i} style={{ position: "absolute", left: 120 + i * 190 + rnd(i) * 40, top: 60 + rnd(i + 9) * 90,
                transform: `translateY(${(1 - pin) * -80}px) scale(${sel ? 1.4 : 1})`, opacity: Math.min(1, pin),
                width: 52, height: 52, borderRadius: "50% 50% 50% 0", rotate: "-45deg", background: sel ? accent : popOf(i + 1),
                border: `4px solid ${INK}` }} />
            );
          })}
        </div>
        <div style={{ marginTop: 26, display: "flex", flexDirection: "column", gap: 16 }}>
          {results.slice(0, 4).map((r, i) => {
            const o = interpolate(local, [resStart + 4 + i * 5, resStart + 12 + i * 5], [0, 1], clamp);
            const sel = i === pick && local >= pickAt;
            return (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "18px 24px",
                borderRadius: 20, background: sel ? pop : WHITE, border: `3px solid ${INK}`, boxShadow: sel ? hard(8) : "none",
                opacity: o, transform: `translateX(${(1 - o) * 60}px) scale(${sel ? 1.03 : 1})` }}>
                <div>
                  <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 34, color: INK }}>{S(r.name)}</div>
                  <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: MUTED, marginTop: 4 }}>{S(r.note)}</div>
                </div>
                <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 30, color: INK }}>{S(r.rating) && `⭐ ${S(r.rating)}`}</div>
              </div>
            );
          })}
        </div>
      </div>
    </Panel>
  );
};

const Shot: React.FC<SP> = ({ d, local, dur }) => {
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

const SceneLayer: React.FC<{ s: Scene; idx: number; accent: string; isLast: boolean }> = ({ s, idx, accent, isLast }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - s.from;
  const end = s.dur + (isLast ? 0 : OV);
  if (local < 0 || local >= end) return null;
  const pop = popOf(idx);
  const inP = spring({ frame: local, fps, config: { damping: 13, stiffness: 170, mass: 0.8 } });
  const outP = isLast ? 0 : interpolate(local, [s.dur - 2, s.dur + OV], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const t = s.trans ?? "up";
  let tf = "";
  if (t === "zoom") tf = `scale(${0.6 + 0.4 * inP}) rotate(${(1 - inP) * -8}deg)`;
  else if (t === "left") tf = `translateX(${(1 - inP) * 900}px) rotate(${(1 - inP) * 6}deg)`;
  else tf = `translateY(${(1 - inP) * 500}px) rotate(${(1 - inP) * -4}deg)`;
  // flottement permanent : rien n'est jamais figé
  const push = interpolate(local, [0, s.dur], [1, 1.07], clamp);
  const float = `translateY(${Math.sin(local / 22) * 8}px) rotate(${Math.sin(local / 40) * 0.6}deg) scale(${push})`;
  tf += ` ${float} translateX(${-outP * 1100}px) rotate(${-outP * 8}deg)`;
  const plate = spring({ frame: local - 2, fps, config: { damping: 14, stiffness: 140 } });
  const props: SP = { d: s.data, local, dur: s.dur, accent, pop, marks: s.marks ?? [] };
  const body = (() => {
    switch (s.kind) {
      case "chat": return <Chat {...props} />;
      case "terminal": return <Terminal {...props} />;
      case "code": return <Code {...props} />;
      case "card": return <Card {...props} />;
      case "list": return <List {...props} />;
      case "stat": return <Stat {...props} />;
      case "compare": return <Compare {...props} />;
      case "search": return <Search {...props} />;
      case "shot": return <Shot {...props} />;
      default: return <Title {...props} />;
    }
  })();
  const flat = s.kind === "title" || s.kind === "list" || s.kind === "stat" || s.kind === "compare";
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 200 }}>
      {/* plaque de couleur derrière la scène */}
      {flat && (
        <div style={{ position: "absolute", left: 40, right: 40, top: 300, height: 880, borderRadius: 60, background: `${pop}55`,
          transform: `scale(${plate}) rotate(${idx % 2 ? 3 : -3}deg) translateX(${-outP * 1100}px)`, opacity: 1 - outP }} />
      )}
      <div style={{ height: 1080, display: "flex", alignItems: "center", justifyContent: "center", transform: tf,
        opacity: Math.min(1, inP * 1.6) }}>
        {body}
      </div>
      {t === "flash" && local < 10 && (
        <AbsoluteFill style={{ background: pop, transform: `translateX(${interpolate(local, [0, 10], [0, 1100], { ...clamp, easing: ease })}px)` }} />
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ sous-titres karaoké
const Captions: React.FC<{ groups: TGroup[]; accent: string }> = ({ groups, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const gi = groups.findIndex((x) => frame >= x.from && frame < x.to);
  if (gi < 0) return null;
  const g = groups[gi];
  const pop = spring({ frame: frame - g.from, fps, config: { damping: 11, stiffness: 300, mass: 0.5 } });
  const hlColor = popOf(gi);
  return (
    <div style={{ position: "absolute", top: 1350, left: 50, right: 50, textAlign: "center",
      transform: `scale(${0.8 + 0.2 * pop}) rotate(${gi % 2 ? 1 : -1}deg)`, fontFamily: SANS, fontWeight: 900, fontSize: 78, lineHeight: 1.2,
      letterSpacing: -1.5, color: INK, WebkitTextStroke: `10px ${WHITE}`, paintOrder: "stroke fill" }}>
      {g.words.map((w, i) => {
        const active = frame >= w.from && (i + 1 < g.words.length ? frame < g.words[i + 1].from : frame < g.to);
        return (
          <span key={i} style={{ display: "inline-block", margin: "0 8px", padding: "0 12px", borderRadius: 16,
            background: active ? hlColor : "transparent", border: active ? BORDER : "4px solid transparent",
            WebkitTextStroke: active ? "0px transparent" : `10px ${WHITE}`,
            color: w.hl && !active ? accent : INK, transform: `translateY(${active ? -6 : 0}px) scale(${active ? 1.08 : 1})`,
            opacity: frame >= w.from - 1 ? 1 : 0.35 }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const Stamp: React.FC<{ s: { text: string; from: number; to: number }; idx: number }> = ({ s, idx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - s.from;
  if (local < 0 || frame >= s.to) return null;
  const p = spring({ frame: local, fps, config: { damping: 8, stiffness: 300, mass: 0.6 } });
  const o = interpolate(frame, [s.to - 6, s.to], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: o }}>
      <div style={{ transform: `translateY(-120px) rotate(-7deg) scale(${2.2 - 1.2 * p})`, fontFamily: SANS, fontWeight: 900,
        fontSize: 130, letterSpacing: -3, color: INK, background: popOf(idx + 3), padding: "16px 50px", borderRadius: 26,
        border: `6px solid ${INK}`, boxShadow: hard(16) }}>{s.text.toUpperCase()}</div>
    </AbsoluteFill>
  );
};

const Progress: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, height: 16, width: `${(frame / durationInFrames) * 100}%`,
      background: accent, borderBottom: BORDER, borderRight: BORDER }} />
  );
};

// ------------------------------------------------------------------ composition
export const TechShort: React.FC<TechShortProps> = ({ hook, scenes, groups, stamps, accent, theme, cover }) => {
  useFonts();
  const frame = useCurrentFrame();
  const th = theme || "ia";
  const ac = accent && !/^#(D4FF3A|3AD8FF)$/i.test(accent) ? accent : DEFAULT_ACCENT[th] || DEFAULT_ACCENT.ia;
  const cv: Cover | null = cover && S(cover.text) ? cover : hook ? { text: hook.text } : null;
  const cur = scenes.reduce((c, s, i) => (frame >= s.from ? i : c), -1);
  const tint = cur < 0 ? (th === "seo" ? POP[2] : POP[3]) : popOf(cur);
  return (
    <AbsoluteFill style={{ width: W, height: H, background: BG }}>
      <style>{FONT_CSS()}</style>
      <Background tint={tint} />
      {scenes.map((s, i) => (
        <SceneLayer key={i} s={s} idx={i} accent={ac} isLast={i === scenes.length - 1} />
      ))}
      {hook && <Hook hook={hook} accent={ac} start={cv ? COVER_FRAMES - 2 : 0} />}
      {stamps.map((s, i) => (
        <Stamp key={i} s={s} idx={i} />
      ))}
      <Captions groups={groups} accent={ac} />
      <Progress accent={ac} />
      {cv && <CoverPoster cover={cv} accent={ac} theme={th} />}
    </AbsoluteFill>
  );
};
