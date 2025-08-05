import React from 'react';
import { Card } from 'react-bootstrap';
import './StatCard.scss';

/**
 * StatCard - Componente riutilizzabile per visualizzare statistiche con progress bar
 * 
 * @param {string} title - Titolo della statistica
 * @param {string|number} value - Valore principale da mostrare
 * @param {string} icon - Nome dell'icona Feather (senza prefisso feather)
 * @param {number} percentage - Percentuale per la progress bar (0-100)
 * @param {string} progressColor - Classe CSS per il colore della progress bar
 * @param {string} iconColor - Classe CSS per il colore dell'icona (default: text-c-green)
 * @param {object} style - Stili CSS aggiuntivi per la card
 */
const StatCard = ({ 
  title, 
  value, 
  icon, 
  percentage, 
  progressColor = 'progress-c-theme',
  iconColor = 'text-c-green',
  style = {}
}) => {
  return (
    <Card style={style}>
      <Card.Body>
        <h6 className="mb-4">{title}</h6>
        <div className="row d-flex align-items-center">
          <div className="col-9">
            <h3 className="f-w-300 d-flex align-items-center m-b-0">
              <i className={`feather icon-${icon} ${iconColor} f-30 m-r-5`} />
              {value}
            </h3>
          </div>
          <div className="col-3 text-end">
            <p className="m-b-0">{percentage}%</p>
          </div>
        </div>
        <div className="progress m-t-30" style={{ height: '7px' }}>
          <div
            className={`progress-bar ${progressColor}`}
            role="progressbar"
            style={{ width: `${percentage}%` }}
            aria-valuenow={percentage}
            aria-valuemin="0"
            aria-valuemax="100"
          />
        </div>
      </Card.Body>
    </Card>
  );
};

export default StatCard;
