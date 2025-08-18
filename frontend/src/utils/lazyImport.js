import { lazy } from 'react';

/**
 * Wrapper per lazy import con gestione degli errori migliorata
 * @param {Function} importFunc - Funzione di import dinamico
 * @returns {React.LazyExoticComponent}
 */
export const lazyImport = (importFunc) => {
  return lazy(() =>
    importFunc().catch((error) => {
      console.error('Error loading module:', error);
      // Fallback component in case of import failure
      return {
        default: () => (
          <div className="m-4 border border-destructive/50 bg-destructive/10 text-destructive rounded-md p-4 text-sm space-y-2">
            <h4 className="font-semibold text-destructive">❌ Errore di Caricamento</h4>
            <p className="text-muted-foreground">Impossibile caricare il componente richiesto.</p>
            <small className="block text-muted-foreground/80">Dettagli: {error.message}</small>
            <div className="pt-2">
              <button
                className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground shadow hover:opacity-90"
                onClick={() => window.location.reload()}
              >
                Riprova
              </button>
            </div>
          </div>
        )
      };
    })
  );
};
