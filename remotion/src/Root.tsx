import { Composition } from "remotion";
import { AnimeShort, AnimeShortProps } from "./AnimeShort";
import { TechShort, TechShortProps } from "./TechShort";

const defaults: AnimeShortProps = {
  durationInFrames: 90,
  shots: [],
  groups: [],
  overlays: [],
};

const techDefaults: TechShortProps = { durationInFrames: 90, hook: null, scenes: [], groups: [], stamps: [] };

export const Root: React.FC = () => (
  <>
  <Composition
    id="TechShort"
    component={TechShort as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={90}
    defaultProps={techDefaults as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => ({
      durationInFrames: Math.max(1, Number((props as unknown as TechShortProps).durationInFrames) || 90),
    })}
  />
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
  </>
);
