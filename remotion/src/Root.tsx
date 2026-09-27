import { Composition } from "remotion";
import { AnimeShort, AnimeShortProps } from "./AnimeShort";

const defaults: AnimeShortProps = {
  durationInFrames: 90,
  shots: [],
  groups: [],
  overlays: [],
};

export const Root: React.FC = () => (
  <Composition
    id="AnimeShort"
    component={AnimeShort as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={90}
    defaultProps={defaults as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => ({
      durationInFrames: Math.max(1, Number((props as unknown as AnimeShortProps).durationInFrames) || 90),
    })}
  />
);
