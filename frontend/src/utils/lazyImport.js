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
          <div className="alert alert-danger m-4">
            <h4>❌ Errore di Caricamento</h4>
            <p>Impossibile caricare il componente richiesto.</p>
            <small>Dettagli: {error.message}</small>
            <div className="mt-3">
              <button className="btn btn-primary" onClick={() => window.location.reload()}>
                Riprova
              </button>
            </div>
          </div>
        )
      };
    })
  );
};
