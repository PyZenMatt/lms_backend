import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Badge, Button, Form, Row, Col, Pagination } from 'react-bootstrap';
import { getBlockchainTransactions } from '../../services/api/blockchain';
import './BlockchainTransactions.scss';

/**
 * Component for displaying blockchain transaction history with filtering
 */
const BlockchainTransactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0
  });
  const [filters, setFilters] = useState({
    transactionType: '',
    startDate: '',
    endDate: ''
  });

  const pageSize = 10;

  const loadTransactions = useCallback(async (page = 1) => {
    setLoading(true);
    setError('');

    try {
      const response = await getBlockchainTransactions({
        page,
        pageSize,
        ...filters
      });

      setTransactions(response.data.results || []);
      setPagination({
        currentPage: page,
        totalPages: Math.ceil((response.data.count || 0) / pageSize),
        totalItems: response.data.count || 0
      });
    } catch (err) {
      console.error('Error loading transactions:', err);
      setError('Error loading transaction history. Please try again.');
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTransactions(1);
  }, [loadTransactions]);

  const handlePageChange = (page) => {
    loadTransactions(page);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters({
      ...filters,
      [name]: value
    });
  };

  const handleFilterApply = (e) => {
    e.preventDefault();
    loadTransactions(1);
  };

  const handleFilterReset = () => {
    setFilters({
      transactionType: '',
      startDate: '',
      endDate: ''
    });
    // Reset will trigger the useEffect via dependency changes
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed':
        return <Badge bg="success">Confirmed</Badge>;
      case 'pending':
        return <Badge bg="warning">Pending</Badge>;
      case 'failed':
        return <Badge bg="danger">Failed</Badge>;
      default:
        return <Badge bg="secondary">{status}</Badge>;
    }
  };

  const getTransactionTypeBadge = (type) => {
    switch (type) {
      case 'reward':
        return <Badge bg="info">Reward</Badge>;
      case 'course_purchase':
        return <Badge bg="primary">Course Purchase</Badge>;
      case 'reward_pool_refill':
        return <Badge bg="dark">Pool Refill</Badge>;
      default:
        return <Badge bg="secondary">{type}</Badge>;
    }
  };

  // Format address for display
  const formatAddress = (address) => {
    if (!address || address.length < 10) return address;
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <Card className="blockchain-transactions">
      <Card.Header>
        <Card.Title as="h5">
          <i className="feather icon-list mr-2"></i>
          Transaction History
        </Card.Title>
      </Card.Header>
      <Card.Body>
        {/* Filters */}
        <div className="transaction-filters mb-4">
          <Form onSubmit={handleFilterApply}>
            <Row>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Transaction Type</Form.Label>
                  <Form.Select
                    name="transactionType"
                    value={filters.transactionType}
                    onChange={handleFilterChange}
                  >
                    <option value="">All Types</option>
                    <option value="reward">Reward</option>
                    <option value="course_purchase">Course Purchase</option>
                    <option value="reward_pool_refill">Pool Refill</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Start Date</Form.Label>
                  <Form.Control
                    type="date"
                    name="startDate"
                    value={filters.startDate}
                    onChange={handleFilterChange}
                  />
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>End Date</Form.Label>
                  <Form.Control
                    type="date"
                    name="endDate"
                    value={filters.endDate}
                    onChange={handleFilterChange}
                  />
                </Form.Group>
              </Col>
              <Col md={3} className="d-flex align-items-end">
                <div className="d-flex">
                  <Button variant="primary" type="submit" className="mr-2">
                    <i className="feather icon-filter mr-1"></i>
                    Filter
                  </Button>
                  <Button variant="light" onClick={handleFilterReset}>
                    <i className="feather icon-refresh-cw mr-1"></i>
                    Reset
                  </Button>
                </div>
              </Col>
            </Row>
          </Form>
        </div>

        {error && (
          <div className="alert alert-danger">
            <i className="feather icon-alert-circle mr-2"></i>
            {error}
          </div>
        )}

        {/* Transactions Table */}
        <div className="table-responsive">
          <Table className="mb-0">
            <thead>
              <tr>
                <th>Date/Time</th>
                <th>Type</th>
                <th>From</th>
                <th>To</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Transaction Hash</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-4">
                    No transactions found
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td>{formatDate(tx.created_at)}</td>
                    <td>{getTransactionTypeBadge(tx.transaction_type)}</td>
                    <td>
                      <code title={tx.from_address}>{formatAddress(tx.from_address)}</code>
                    </td>
                    <td>
                      <code title={tx.to_address}>{formatAddress(tx.to_address)}</code>
                    </td>
                    <td>{tx.amount}</td>
                    <td>{getStatusBadge(tx.status)}</td>
                    <td>
                      <a
                        href={`https://amoy.polygonscan.com/tx/${tx.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="tx-hash"
                      >
                        {formatAddress(tx.tx_hash)}
                        <i className="feather icon-external-link ml-1"></i>
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </div>

        {/* Pagination */}
        {pagination.totalPages > 1 && (
          <div className="d-flex justify-content-between align-items-center mt-4">
            <div>
              Showing {(pagination.currentPage - 1) * pageSize + 1} to{' '}
              {Math.min(pagination.currentPage * pageSize, pagination.totalItems)} of {pagination.totalItems} transactions
            </div>
            <Pagination>
              <Pagination.First
                onClick={() => handlePageChange(1)}
                disabled={pagination.currentPage === 1}
              />
              <Pagination.Prev
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage === 1}
              />

              {[...Array(pagination.totalPages).keys()].map((page) => {
                const pageNumber = page + 1;
                // Show only 5 pages around current page
                if (
                  pageNumber === 1 ||
                  pageNumber === pagination.totalPages ||
                  (pageNumber >= pagination.currentPage - 2 && pageNumber <= pagination.currentPage + 2)
                ) {
                  return (
                    <Pagination.Item
                      key={pageNumber}
                      active={pageNumber === pagination.currentPage}
                      onClick={() => handlePageChange(pageNumber)}
                    >
                      {pageNumber}
                    </Pagination.Item>
                  );
                } else if (
                  pageNumber === pagination.currentPage - 3 ||
                  pageNumber === pagination.currentPage + 3
                ) {
                  return <Pagination.Ellipsis key={pageNumber} />;
                } else {
                  return null;
                }
              })}

              <Pagination.Next
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage === pagination.totalPages}
              />
              <Pagination.Last
                onClick={() => handlePageChange(pagination.totalPages)}
                disabled={pagination.currentPage === pagination.totalPages}
              />
            </Pagination>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default BlockchainTransactions;
