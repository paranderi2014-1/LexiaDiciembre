import type { ComponentType } from "react";

import { ComplianceDemo } from "./ComplianceDemo";
import { ContratosDemo } from "./ContratosDemo";
import { EjecutivosDemo } from "./EjecutivosDemo";
import { EscritosDemo } from "./EscritosDemo";
import { GestionDemo } from "./GestionDemo";
import { HonorariosDemo } from "./HonorariosDemo";
import { JurisprudenciaDemo } from "./JurisprudenciaDemo";
import { LitigiosDemo } from "./LitigiosDemo";
import { PrediccionDemo } from "./PrediccionDemo";
import { PrivacidadDemo } from "./PrivacidadDemo";
import { RevisionDemo } from "./RevisionDemo";
import { VigilanciaDemo } from "./VigilanciaDemo";

export {
  ComplianceDemo,
  ContratosDemo,
  EjecutivosDemo,
  EscritosDemo,
  GestionDemo,
  HonorariosDemo,
  JurisprudenciaDemo,
  LitigiosDemo,
  PrediccionDemo,
  PrivacidadDemo,
  RevisionDemo,
  VigilanciaDemo,
};

const DEMOS: Record<number, ComponentType> = {
  1: HonorariosDemo,
  2: JurisprudenciaDemo,
  3: VigilanciaDemo,
  4: ContratosDemo,
  5: EjecutivosDemo,
  6: ComplianceDemo,
  7: LitigiosDemo,
  8: PrediccionDemo,
  9: GestionDemo,
  10: EscritosDemo,
  11: RevisionDemo,
  12: PrivacidadDemo,
};

/** Renders the interactive demo that belongs to a module of `lexia-data.ts`. */
export function ModuleDemo({ id }: { id: number }) {
  const Demo = DEMOS[id];
  return Demo ? <Demo /> : null;
}
