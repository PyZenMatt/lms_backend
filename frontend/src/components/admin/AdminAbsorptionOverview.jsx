import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Row, Col, Spinner, Alert } from 'react-bootstrap';

/**
 * Admin view for Teacher Discount Absorption system overview
 */
const AdminAbsorptionOverview = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await fetch('/api/v1/teocoin/admin/absorptions/overview/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });

      const result = await response.json();
      if (result.success) {
        setData(result);
      } else {
        setError(result.error || 'Errore nel caricamento dei dati');
      }
    } catch (error) {
      console.error('Error loading admin absorption data:', error);
      setError('Errore di connessione');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <Card.Body className="text-center">
          <Spinner animation="border" className="mb-3" />
          <p>Caricamento statistiche assorbimenti...</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="admin-absorption-overview">
      <Card className="mb-4">
        <Card.Header className="bg-primary text-white">
          <h5 className="mb-0">
            <i className="feather icon-bar-chart me-2"></i>
            Panoramica Sistema Assorbimento Sconti
          </h5>
        </Card.Header>
        <Card.Body>
          {error && (
            <Alert variant="danger">{error}</Alert>
          )}
          
          {data && (
            <>
              {/* Platform Savings */}
              <Row className="mb-4">
                <Col md={6}>
                  <Card className="bg-success text-white">
                    <Card.Body>
                      <h3>€{data.platform_savings.total_discount_absorbed_eur}</h3>
                      <p className="mb-0">Sconti Assorbiti da Insegnanti</p>
                      <small>La piattaforma ha risparmiato questo importo</small>
                    </Card.Body>
                  </Card>
                </Col>
                <Col md={6}>
                  <Card className="bg-info text-white">
                    <Card.Body>
                      <h3>{data.platform_savings.absorption_count}</h3>
                      <p className="mb-0">Assorbimenti Totali</p>
                      <small>Numero di volte che gli insegnanti hanno scelto i TEO</small>
                    </Card.Body>
                  </Card>
                </Col>
              </Row>

              {/* Recent Absorptions */}
              <Card>
                <Card.Header>
                  <h6 className="mb-0">Assorbimenti Recenti</h6>
                </Card.Header>
                <Card.Body>
                  {data.recent_absorptions.length === 0 ? (
                    <p className="text-muted mb-0">Nessun assorbimento recente</p>
                  ) : (
                    <Table responsive size="sm">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Insegnante</th>
                          <th>Corso</th>
                          <th>Stato</th>
                          <th>Sconto</th>
                          <th>EUR Finale</th>
                          <th>TEO Finale</th>
                          <th>Data Creazione</th>
                          <th>Data Decisione</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_absorptions.map((absorption) => (
                          <tr key={absorption.id}>
                            <td>{absorption.id}</td>
                            <td>{absorption.teacher}</td>
                            <td>{absorption.course}</td>
                            <td>
                              <Badge bg={
                                absorption.status === 'absorbed' ? 'success' : 
                                absorption.status === 'refused' ? 'secondary' : 
                                absorption.status === 'expired' ? 'warning' : 'primary'
                              }>
                                {absorption.status === 'absorbed' ? 'Assorbito' :
                                 absorption.status === 'refused' ? 'Rifiutato' :
                                 absorption.status === 'expired' ? 'Scaduto' : 'In attesa'}
                              </Badge>
                            </td>
                            <td>€{absorption.discount_eur}</td>
                            <td>€{absorption.final_teacher_eur}</td>
                            <td>{absorption.final_teacher_teo} TEO</td>
                            <td>{new Date(absorption.created_at).toLocaleDateString()}</td>
                            <td>
                              {absorption.decided_at ? 
                                new Date(absorption.decided_at).toLocaleDateString() : 
                                '-'
                              }
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </Card.Body>
              </Card>
            </>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default AdminAbsorptionOverview;
