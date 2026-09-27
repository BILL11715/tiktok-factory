/**
 * AnimeShort : composition verticale 1080x1920 pour @the.asura8.
 * Construite sur le moteur Remotion d'OpenMontage (remotion-composer) et son
 * ParticleOverlay. Tout est piloté par un fichier timeline JSON produit par le
 * pipeline Python (factory/motion.py) : plans, transitions, étalonnage,
 * sous-titres mot par mot, hook, classements, appel à l'abonnement, révélation.
 */
import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ParticleOverlay, ParticleType } from "./components/ParticleOverlay";

// ------------------------------------------------------------------ types
export type Shot = {
  from: number; // frame de début
  dur: number; // durée en frames
  src: string; // image composée 1231x2188 dans public/ (ou vignette si video)
  video?: string; // extrait vidéo 1080x1920 muet dans public/ (prioritaire sur src)
  videoStart?: number; // frame de départ dans l'extrait
  motion?: string; // zoom-in | zoom-out | pan-left | pan-right | drift-up | static
  grade?: string; // normal | bw | cinematic | vivid | warm | cold
  trans?: string; // cut | whip | zoom | glitch | flash | slide
  fx?: string; // hook | punch
  seed?: number;
};
export type Word = { w: string; from: number; to: number; hl?: boolean };
export type Group = { from: number; to: number; words: Word[] };
export type Overlay = {
  type: "hook" | "rank" | "cta" | "reveal" | "stamp" | "spoiler";
  text?: string;
  from: number;
  to: number;
  handle?: string;
  avatar?: string;
};
export type AnimeShortProps = {
  durationInFrames: number;
  shots: Shot[];
  groups: Group[];
  overlays: Overlay[];
  particles?: ParticleType | null;
  particleColor?: string;
  accent?: string;
  grain?: boolean;
};

const W = 1080;
const H = 1920;
const OVER = 1.14;
const OV = 8; // recouvrement entre plans pour les transitions
const YELLOW = "#FFD400";

// ------------------------------------------------------------------ polices
const FONT_CSS = () => `
@font-face { font-family: 'Anton'; src: url('${staticFile("fonts/Anton-Regular.ttf")}') format('truetype'); }
@font-face { font-family: 'MontX'; src: url('${staticFile("fonts/Montserrat-ExtraBold.ttf")}') format('truetype'); }
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
    Promise.all([
      (document as unknown as { fonts: { load: (f: string) => Promise<unknown> } }).fonts.load("80px Anton"),
      (document as unknown as { fonts: { load: (f: string) => Promise<unknown> } }).fonts.load("80px MontX"),
    ])
      .then(finish)
      .catch(finish);
    return () => clearTimeout(t);
  }, [handle]);
};

function rnd(seed: number): number {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

const GRADES: Record<string, string> = {
  normal: "none",
  bw: "grayscale(1) contrast(1.28) brightness(0.92)",
  cinematic: "saturate(0.72) contrast(1.14) brightness(0.93)",
  vivid: "saturate(1.28) contrast(1.08)",
  warm: "sepia(0.25) saturate(1.1) contrast(1.05)",
  cold: "hue-rotate(-12deg) saturate(0.8) contrast(1.1) brightness(0.95)",
};

// ------------------------------------------------------------------ plan
const ShotLayer: React.FC<{ shot: Shot; isFirst: boolean }> = ({ shot, isFirst }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = shot.dur + OV;
  const seed = shot.seed ?? shot.from;
  const t = frame / Math.max(1, total);

  // mouvement de caméra lent
  let scale = 1;
  let tx = 0;
  let ty = 0;
  const m = shot.motion ?? "zoom-in";
  const amp = shot.video ? 0.03 + rnd(seed) * 0.03 : 0.07 + rnd(seed) * 0.06;
  if (m === "zoom-in") scale = 1 + amp * t;
  else if (m === "zoom-out") scale = 1 + amp * (1 - t);
  else if (m === "pan-left") tx = ((W * OVER - W) / 2) * (1 - 2 * t);
  else if (m === "pan-right") tx = -((W * OVER - W) / 2) * (1 - 2 * t);
  else if (m === "drift-up") ty = ((H * OVER - H) / 2) * (1 - 2 * t);

  // zoom punch + tremblement (hook / révélations)
  if (shot.fx === "hook" || shot.fx === "punch") {
    const strength = shot.fx === "hook" ? 0.45 : 0.2;
    const s = spring({ frame, fps, config: { damping: 14, stiffness: 180, mass: 0.6 } });
    scale *= 1 + strength * (1 - s);
    const shake = interpolate(frame, [0, 14], [shot.fx === "hook" ? 26 : 12, 0], {
      extrapolateRight: "clamp",
    });
    tx += Math.sin(frame * 2.7) * shake;
    ty += Math.cos(frame * 2.1) * shake;
  }

  // transition d'entrée (sur les OV premières frames)
  const trans = isFirst ? "cut" : shot.trans ?? "cut";
  const p = interpolate(frame, [0, OV], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ease = 1 - Math.pow(1 - p, 3);
  let opacity = 1;
  let blur = 0;
  let extraX = 0;
  let extraY = 0;
  let extraScale = 1;
  let flash = 0;
  const dir = rnd(seed + 3) > 0.5 ? 1 : -1;
  if (trans === "whip") {
    extraX = (1 - ease) * W * 1.1 * dir;
    blur = (1 - ease) * 40;
  } else if (trans === "zoom") {
    extraScale = 1 + (1 - ease) * 0.8;
    opacity = ease;
    blur = (1 - ease) * 25;
  } else if (trans === "slide") {
    extraY = (1 - ease) * H;
    blur = (1 - ease) * 30;
  } else if (trans === "flash") {
    flash = 1 - p;
  }
  const grade = GRADES[shot.grade ?? "normal"] ?? "none";
  const filter = [grade !== "none" ? grade : "", blur > 0.5 ? `blur(${blur.toFixed(1)}px)` : ""]
    .filter(Boolean)
    .join(" ") || "none";

  const img = (clip?: string, dx = 0, hue = 0) => {
    const style: React.CSSProperties = {
        position: "absolute",
        width: W * OVER,
        height: H * OVER,
        left: (W - W * OVER) / 2,
        top: (H - H * OVER) / 2,
        transform: `translate(${tx + extraX + dx}px, ${ty + extraY}px) scale(${scale * extraScale})`,
        filter: hue ? `${filter === "none" ? "" : filter} hue-rotate(${hue}deg) saturate(2)` : filter,
        clipPath: clip,
        objectFit: "cover",
      };
    return shot.video ? (
      <OffthreadVideo src={staticFile(shot.video)} startFrom={shot.videoStart ?? 0} muted style={style} />
    ) : (
      <Img src={staticFile(shot.src)} style={style} />
    );
  };

  // glitch : bandes horizontales décalées + décalage de teinte pendant la transition
  const glitching = trans === "glitch" && frame < OV + 2;
  return (
    <AbsoluteFill style={{ opacity, overflow: "hidden", backgroundColor: "#000" }}>
      {glitching ? (
        <>
          {img()}
          {[0, 1, 2, 3, 4, 5].map((b) => {
            const top = rnd(seed + b * 7 + frame) * 90;
            const h = 4 + rnd(seed + b * 13 + frame) * 12;
            const dx = (rnd(seed + b * 3 + frame * 5) - 0.5) * 160;
            return (
              <React.Fragment key={b}>
                {img(`inset(${top}% 0 ${Math.max(0, 100 - top - h)}% 0)`, dx, b % 2 ? 160 : -160)}
              </React.Fragment>
            );
          })}
        </>
      ) : (
        img()
      )}
      {flash > 0 && <AbsoluteFill style={{ backgroundColor: "#fff", opacity: flash }} />}
      {(shot.fx === "hook" || shot.fx === "punch") && (
        <AbsoluteFill
          style={{
            backgroundColor: "#fff",
            opacity: interpolate(frame, [0, shot.fx === "hook" ? 7 : 4], [shot.fx === "hook" ? 0.95 : 0.6, 0], {
              extrapolateRight: "clamp",
            }),
          }}
        />
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ habillage
const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{ background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.55) 100%)" }}
  />
);

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const x = Math.floor(rnd(frame) * 256);
  const y = Math.floor(rnd(frame + 11) * 256);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url(${staticFile("grain.png")})`,
        backgroundPosition: `${x}px ${y}px`,
        opacity: 0.09,
        mixBlendMode: "overlay",
      }}
    />
  );
};

const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        bottom: 0,
        height: 14,
        width: `${(frame / durationInFrames) * 100}%`,
        background: YELLOW,
        boxShadow: "0 0 18px rgba(255,212,0,0.8)",
      }}
    />
  );
};

// ------------------------------------------------------------------ sous-titres
const Captions: React.FC<{ groups: Group[] }> = ({ groups }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = groups.find((x) => frame >= x.from && frame < x.to);
  if (!g) return null;
  const local = frame - g.from;
  const pop = spring({ frame: local, fps, config: { damping: 12, stiffness: 260, mass: 0.5 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 1040,
        left: 60,
        right: 60,
        textAlign: "center",
        transform: `scale(${0.82 + 0.18 * pop})`,
        fontFamily: "MontX",
        fontSize: 100,
        textTransform: "uppercase",
        letterSpacing: 1,
        lineHeight: 1.12,
        color: "#fff",
        textShadow: "0 6px 18px rgba(0,0,0,0.9)",
        WebkitTextStroke: "10px #000",
        paintOrder: "stroke fill",
      }}
    >
      {g.words.map((w, i) => {
        const active = frame >= w.from && frame < w.to;
        return (
          <span
            key={i}
            style={{
              color: w.hl ? YELLOW : "#fff",
              display: "inline-block",
              margin: "0 16px",
              transform: `scale(${active ? 1.08 : 1})`,
              opacity: frame >= w.from - 1 ? 1 : 0,
            }}
          >
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ overlays
const Hook: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = (o.text ?? "").toUpperCase().split(/\s+/).filter(Boolean);
  const fade = interpolate(frame, [o.to - o.from - 6, o.to - o.from], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        top: 200,
        left: 50,
        right: 50,
        textAlign: "center",
        fontFamily: "Anton",
        fontSize: 112,
        lineHeight: 1.08,
        opacity: fade,
      }}
    >
      {words.map((w, i) => {
        const s = spring({ frame: frame - 2 - i * 3, fps, config: { damping: 11, stiffness: 240, mass: 0.6 } });
        const last = i === words.length - 1;
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              margin: "0 12px",
              color: last ? YELLOW : "#fff",
              opacity: s > 0.02 ? 1 : 0,
              transform: `scale(${2.2 - 1.2 * s}) rotate(${(1 - s) * (i % 2 ? 6 : -6)}deg)`,
              WebkitTextStroke: "5px #000",
              paintOrder: "stroke fill",
              textShadow: "0 8px 0 #000, 0 0 30px rgba(0,0,0,0.9)",
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

const Burst: React.FC<{ frame: number; color: string }> = ({ frame, color }) => {
  const k = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <svg width={500} height={500} style={{ position: "absolute", left: -110, top: -120, opacity: 1 - k }}>
      {Array.from({ length: 14 }).map((_, i) => {
        const a = (i / 14) * Math.PI * 2;
        const r1 = 60 + k * 120;
        const r2 = r1 + 50 + k * 60;
        return (
          <line
            key={i}
            x1={250 + Math.cos(a) * r1}
            y1={250 + Math.sin(a) * r1}
            x2={250 + Math.cos(a) * r2}
            y2={250 + Math.sin(a) * r2}
            stroke={color}
            strokeWidth={10}
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
};

const Rank: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 9, stiffness: 200, mass: 0.7 } });
  return (
    <div style={{ position: "absolute", left: 70, top: 190 }}>
      <Burst frame={frame} color={YELLOW} />
      <div
        style={{
          position: "relative",
          fontFamily: "Anton",
          fontSize: 270,
          color: YELLOW,
          transform: `scale(${s}) rotate(${(1 - s) * -25 - 6}deg)`,
          WebkitTextStroke: "8px #000",
          paintOrder: "stroke fill",
          textShadow: "0 12px 0 #000, 0 0 40px rgba(255,212,0,0.5)",
        }}
      >
        {o.text}
      </div>
    </div>
  );
};

const Stamp: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 10, stiffness: 300, mass: 0.8 } });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          marginTop: -300,
          padding: "14px 44px",
          border: "12px solid #E8222B",
          borderRadius: 18,
          color: "#E8222B",
          fontFamily: "Anton",
          fontSize: 150,
          letterSpacing: 6,
          transform: `scale(${3 - 2 * s}) rotate(-12deg)`,
          opacity: s,
          background: "rgba(0,0,0,0.25)",
          textShadow: "0 0 20px rgba(0,0,0,0.6)",
        }}
      >
        {(o.text ?? "").toUpperCase()}
      </div>
    </AbsoluteFill>
  );
};

const Cta: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inS = spring({ frame, fps, config: { damping: 12, stiffness: 160 } });
  const tap = 26; // frame du clic (le pipeline y place le bruit de clic)
  const clicked = frame >= tap;
  const cursorP = interpolate(frame, [8, tap], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const press = frame >= tap && frame < tap + 5 ? 0.9 : 1;
  const out = interpolate(frame, [o.to - o.from - 8, o.to - o.from], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const heart = spring({ frame: frame - tap, fps, config: { damping: 8, stiffness: 180 } });
  return (
    <div
      style={{
        position: "absolute",
        left: 140,
        right: 140,
        top: 1480,
        height: 170,
        borderRadius: 34,
        background: "rgba(15,15,15,0.88)",
        border: "3px solid rgba(255,255,255,0.15)",
        display: "flex",
        alignItems: "center",
        padding: "0 28px",
        gap: 24,
        transform: `translateY(${(1 - inS) * 400}px)`,
        opacity: out,
        boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
      }}
    >
      <div
        style={{
          width: 110,
          height: 110,
          borderRadius: "50%",
          overflow: "hidden",
          border: `5px solid ${YELLOW}`,
          flexShrink: 0,
          background: "#333",
        }}
      >
        {o.avatar ? (
          <Img src={staticFile(o.avatar)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : null}
      </div>
      <div style={{ flex: 1, color: "#fff", fontFamily: "MontX", fontSize: 44 }}>
        {o.handle ?? "@the.asura8"}
        <div style={{ fontSize: 28, opacity: 0.7, marginTop: 4 }}>Anime & manga, tous les jours</div>
      </div>
      <div
        style={{
          padding: "22px 30px",
          borderRadius: 18,
          background: clicked ? "#3a3a3a" : "#FE2C55",
          color: "#fff",
          fontFamily: "MontX",
          fontSize: 40,
          transform: `scale(${press})`,
          whiteSpace: "nowrap",
        }}
      >
        {clicked ? "Abonné ✓" : "S'abonner"}
      </div>
      {/* curseur (doigt) */}
      <div
        style={{
          position: "absolute",
          width: 70,
          height: 70,
          borderRadius: "50%",
          background: "rgba(255,255,255,0.9)",
          border: "6px solid rgba(0,0,0,0.5)",
          right: 90 + (1 - cursorP) * -200,
          top: 60 + (1 - cursorP) * 260,
          opacity: frame > tap + 14 ? 0 : cursorP > 0 ? 1 : 0,
          transform: `scale(${press === 0.9 ? 0.8 : 1})`,
        }}
      />
      {clicked && (
        <div
          style={{
            position: "absolute",
            right: 120,
            top: -40 - heart * 120,
            fontSize: 90,
            opacity: 1 - interpolate(frame - tap, [10, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            transform: `scale(${heart})`,
          }}
        >
          <svg width={90} height={90} viewBox="0 0 24 24">
            <path fill="#FE2C55" d="M12 21s-7.5-4.6-10-9.2C.3 8.4 2.3 4.5 6 4.5c2 0 3.3 1 4 2.2.7-1.2 2-2.2 4-2.2 3.7 0 5.7 3.9 4 7.3C19.5 16.4 12 21 12 21z" />
          </svg>
        </div>
      )}
    </div>
  );
};

const Reveal: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const letters = (o.text ?? "").toUpperCase().split("");
  const line = interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 420, left: 40, right: 40, textAlign: "center" }}>
      <div style={{ fontFamily: "Anton", fontSize: 150, lineHeight: 1.05 }}>
        {letters.map((c, i) => {
          const s = spring({ frame: frame - i * 2, fps, config: { damping: 12, stiffness: 220 } });
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                color: YELLOW,
                transform: `translateY(${(1 - s) * 80}px) scale(${0.5 + 0.5 * s})`,
                opacity: s,
                WebkitTextStroke: "7px #000",
                paintOrder: "stroke fill",
                textShadow: "0 10px 0 #000, 0 0 50px rgba(255,212,0,0.6)",
                whiteSpace: "pre",
              }}
            >
              {c}
            </span>
          );
        })}
      </div>
      <div style={{ height: 12, background: YELLOW, margin: "10px auto 0", width: `${line * 70}%`, borderRadius: 6 }} />
    </div>
  );
};

const Spoiler: React.FC<{ o: Overlay }> = ({ o }) => {
  const frame = useCurrentFrame();
  const blink = Math.floor(frame / 6) % 2 === 0 ? 1 : 0.75;
  return (
    <div
      style={{
        position: "absolute",
        top: 110,
        left: "50%",
        transform: "translateX(-50%)",
        background: "#E8222B",
        color: "#fff",
        fontFamily: "Anton",
        fontSize: 54,
        padding: "8px 28px",
        borderRadius: 12,
        opacity: blink,
        whiteSpace: "nowrap",
      }}
    >
      SPOIL {(o.text ?? "").toUpperCase()}
    </div>
  );
};

const OverlayView: React.FC<{ o: Overlay }> = ({ o }) => {
  switch (o.type) {
    case "hook":
      return <Hook o={o} />;
    case "rank":
      return <Rank o={o} />;
    case "stamp":
      return <Stamp o={o} />;
    case "cta":
      return <Cta o={o} />;
    case "reveal":
      return <Reveal o={o} />;
    case "spoiler":
      return <Spoiler o={o} />;
    default:
      return null;
  }
};

// ------------------------------------------------------------------ composition
export const AnimeShort: React.FC<AnimeShortProps> = ({
  durationInFrames,
  shots,
  groups,
  overlays,
  particles,
  particleColor,
  grain = true,
}) => {
  useFonts();
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <style>{FONT_CSS()}</style>
      {shots.map((s, i) => (
        <Sequence
          key={i}
          from={s.from}
          durationInFrames={Math.min(s.dur + OV, durationInFrames - s.from)}
          layout="none"
        >
          <AbsoluteFill>
            <ShotLayer shot={s} isFirst={i === 0} />
          </AbsoluteFill>
        </Sequence>
      ))}
      <Vignette />
      {particles ? <ParticleOverlay type={particles} count={22} color={particleColor ?? "#FFE082"} intensity={0.5} /> : null}
      {grain ? <Grain /> : null}
      <Captions groups={groups} />
      {overlays.map((o, i) => (
        <Sequence key={`o${i}`} from={o.from} durationInFrames={Math.max(1, o.to - o.from)} layout="none">
          <AbsoluteFill>
            <OverlayView o={o} />
          </AbsoluteFill>
        </Sequence>
      ))}
      <ProgressBar />
    </AbsoluteFill>
  );
};
