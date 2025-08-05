import React from 'react';
import { Alert } from 'react-bootstrap';

const ErrorDisplay = ({ errors, className = "" }) => {
  if (!errors || Object.keys(errors).length === 0) {
    return null;
  }

  const errorList = Object.entries(errors);

  return (
    <Alert variant="danger" className={className}>
      <div className="d-flex align-items-start">
        <i className="bi bi-exclamation-triangle-fill me-2 flex-shrink-0 mt-1"></i>
        <div className="flex-grow-1">
          {errorList.length === 1 ? (
            <div>{errorList[0][1]}</div>
          ) : (
            <>
              <div className="fw-semibold mb-2">
                Correggi i seguenti errori:
              </div>
              <ul className="mb-0 ps-3">
                {errorList.map(([field, message], index) => (
                  <li key={index} className="mb-1">
                    <strong>{getFieldDisplayName(field)}:</strong> {message}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </Alert>
  );
};

const getFieldDisplayName = (field) => {
  const fieldNames = {
    title: 'Titolo',
    description: 'Descrizione',
    price: 'Prezzo',
    category: 'Categoria',
    content: 'Contenuto',
    duration: 'Durata',
    videoFile: 'Video',
    timeEstimate: 'Tempo stimato',
    materials: 'Materiali',
    instructions: 'Istruzioni',
    exerciseType: 'Tipo esercizio',
    difficulty: 'Difficoltà'
  };
  
  return fieldNames[field] || field;
};

export default ErrorDisplay;
