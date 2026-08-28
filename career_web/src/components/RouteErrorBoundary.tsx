import { Component, type ErrorInfo, type ReactNode } from "react";

import type { Locale } from "../types";

interface Props {
  children: ReactNode;
  locale: Locale;
  resetKey: string;
}

interface State {
  failed: boolean;
}

export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Career route failed to load", error, info.componentStack);
  }

  componentDidUpdate(previous: Props): void {
    if (this.state.failed && previous.resetKey !== this.props.resetKey) {
      this.setState({ failed: false });
    }
  }

  render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    const es = this.props.locale === "es";
    return (
      <section className="battle-error" role="alert">
        <h1>{es ? "No se pudo cargar esta pantalla" : "This screen could not be loaded"}</h1>
        <p>{es ? "El juego puede haberse actualizado o la conexión pudo interrumpir una descarga. Tu carrera guardada no se modifica por este error." : "The game may have updated or the connection may have interrupted a download. This error does not modify your saved career."}</p>
        <button onClick={() => window.location.reload()}>{es ? "Recargar Carrera" : "Reload Career"}</button>
      </section>
    );
  }
}
