// TODO: Verifica mapping sottocomponenti Modal
import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Table, Badge, Button, Alert, Spinner, Modal } from '@/components/ui';
import api from '../../services/core/axiosClient';

const AdminTransactionMonitor = () => {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedTx, setSelectedTx] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchTransactions();
    fetchStats();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await api.get('/admin/transactions/');
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/transactions/stats/');
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  const retryFailedTransaction = async (txId) => {
    try {
  await api.post(`/admin/transactions/${txId}/retry/`);
  fetchTransactions(); // Refresh
  // TODO: replace with toast
  console.log('Transazione ritentata con successo');
    } catch (error) {
  console.error('Errore nel ritentare la transazione');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      completed: { variant: 'success', text: 'Completata' },
      pending: { variant: 'warning', text: 'In Attesa' },
      failed: { variant: 'danger', text: 'Fallita' }
    };
    const config = statusMap[status] || { variant: 'secondary', text: status };
    return <Badge bg={config.variant}>{config.text}</Badge>;
  };

  const getTypeIcon = (type) => {
    const typeMap = {
      course_purchase: 'icon-shopping-cart',
      exercise_reward: 'icon-award',
      review_reward: 'icon-star',
      achievement_reward: 'icon-trophy'
    };
    return typeMap[type] || 'icon-circle';
  };

  const formatAmount = (amount) => {
    return `${parseFloat(amount).toFixed(2)} TEO`;
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center p-4">
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div>
      {/* Stats Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="bg-success text-background">
            <Card.Body>
              <div className="d-flex justify-content-between">
                <div>
                  <h4>{stats.completed_count || 0}</h4>
                  <p className="mb-0">Transazioni Completate</p>
                </div>
                <div className="align-self-center">
                  <i className="feather icon-check-circle" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card className="bg-warning text-background">
            <Card.Body>
              <div className="d-flex justify-content-between">
                <div>
                  <h4>{stats.pending_count || 0}</h4>
                  <p className="mb-0">In Attesa</p>
                </div>
                <div className="align-self-center">
                  <i className="feather icon-clock" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card className="bg-danger text-background">
            <Card.Body>
              <div className="d-flex justify-content-between">
                <div>
                  <h4>{stats.failed_count || 0}</h4>
                  <p className="mb-0">Fallite</p>
                </div>
                <div className="align-self-center">
                  <i className="feather icon-x-circle" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card className="bg-info text-background">
            <Card.Body>
              <div className="d-flex justify-content-between">
                <div>
                  <h4>{formatAmount(stats.total_volume || 0)}</h4>
                  <p className="mb-0">Volume Totale</p>
                </div>
                <div className="align-self-center">
                  <i className="feather icon-trending-up" style={{ fontSize: '2rem' }}></i>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Ethics Notice */}
      <Alert variant="info" className="mb-4">
        <div className="d-flex align-items-center">
          <i className="feather icon-shield me-2"></i>
          <div>
            <strong>Nota sulla Privacy:</strong> Questi dati sono accessibili solo agli amministratori per scopi di monitoraggio sistema,
            supporto utenti e compliance. Le informazioni personali sono protette secondo le normative vigenti sulla privacy.
          </div>
        </div>
      </Alert>

      {/* Failed Transactions Alert */}
      {stats.failed_count > 0 && (
        <Alert variant="warning" className="mb-4">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <i className="feather icon-border rounded-md p-3 bg-muted text-muted-foreground-triangle me-2"></i>
              <strong>Attenzione:</strong> Ci sono {stats.failed_count} transazioni fallite che richiedono intervento.
            </div>
            <Button variant="outline-warning" size="sm" onClick={() => fetchTransactions()}>
              <i className="feather icon-refresh-cw me-1"></i>
              Aggiorna
            </Button>
          </div>
        </Alert>
      )}

      {/* Transactions Table */}
      <Card>
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="feather icon-list me-2"></i>
              Transazioni Blockchain Recenti
            </h5>
            <Button variant="outline-primary" size="sm" onClick={fetchTransactions}>
              <i className="feather icon-refresh-cw me-1"></i>
              Aggiorna
            </Button>
          </div>
        </Card.Header>
        <Card.Body className="p-0">
          <Table responsive hover>
            <thead className="bg-light">
              <tr>
                <th>Data/Ora</th>
                <th>Tipo</th>
                <th>Utente</th>
                <th>Importo</th>
                <th>Status</th>
                <th>TX Hash</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td className="small">
                    {new Date(tx.created_at).toLocaleDateString('it-IT')}
                    <br />
                    <span className="text-muted">{new Date(tx.created_at).toLocaleTimeString('it-IT')}</span>
                  </td>
                  <td>
                    <div className="d-flex align-items-center">
                      <i className={`feather ${getTypeIcon(tx.transaction_type)} me-2`}></i>
                      <span className="small">{tx.transaction_type.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}</span>
                    </div>
                  </td>
                  <td>
                    <div>
                      <strong>{tx.user.username}</strong>
                      <br />
                      <span className="text-muted small">{tx.user.email}</span>
                    </div>
                  </td>
                  <td>
                    <strong className={tx.amount > 0 ? 'text-success' : 'text-danger'}>
                      {tx.amount > 0 ? '+' : ''}
                      {formatAmount(tx.amount)}
                    </strong>
                  </td>
                  <td>{getStatusBadge(tx.status)}</td>
                  <td>
                    {tx.tx_hash ? (
                      <div>
                        <code className="small">{tx.tx_hash.substring(0, 10)}...</code>
                        <br />
                        <a
                          href={`https://amoy.polygonscan.com/tx/${tx.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="small text-primary"
                        >
                          <i className="feather icon-external-link me-1"></i>
                          Blockchain
                        </a>
                      </div>
                    ) : (
                      <span className="text-muted small">N/A</span>
                    )}
                  </td>
                  <td>
                    <div className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-group-vertical inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground-group-sm">
                      <Button
                        variant="outline-info"
                        size="sm"
                        onClick={() => {
                          setSelectedTx(tx);
                          setShowModal(true);
                        }}
                      >
                        <i className="feather icon-eye"></i>
                      </Button>
                      {tx.status === 'failed' && (
                        <Button variant="outline-warning" size="sm" onClick={() => retryFailedTransaction(tx.id)}>
                          <i className="feather icon-refresh-cw"></i>
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Transaction Detail Modal */}
  <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Dettagli Transazione</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedTx && (
            <div>
              <Row>
                <Col md={6}>
                  <strong>ID Transazione:</strong> {selectedTx.id}
                </Col>
                <Col md={6}>
                  <strong>Status:</strong> {getStatusBadge(selectedTx.status)}
                </Col>
              </Row>
              <hr />
              <Row>
                <Col md={6}>
                  <strong>Utente:</strong> {selectedTx.user.username} ({selectedTx.user.email})
                </Col>
                <Col md={6}>
                  <strong>Importo:</strong> {formatAmount(selectedTx.amount)}
                </Col>
              </Row>
              <hr />
              {selectedTx.error_message && (
                <div>
                  <strong>Errore:</strong>
                  <Alert variant="danger" className="mt-2">
                    {selectedTx.error_message}
                  </Alert>
                </div>
              )}
              {selectedTx.notes && (
                <div>
                  <strong>Note:</strong>
                  <p className="mt-2">{selectedTx.notes}</p>
                </div>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Chiudi
          </Button>
        </Modal.Footer>
  </Modal>
    </div>
  );
};

export default AdminTransactionMonitor;
