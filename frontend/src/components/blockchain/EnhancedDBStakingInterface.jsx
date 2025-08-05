/**
 * Enhanced DB-Based Staking Interface - Phase 3
 * Modern design with improved UX and analytics
 */
import React, { useState, useEffect } from 'react';
import { 
  Card, Button, Alert, Form, Badge, Spinner, ProgressBar, 
  Row, Col, Modal, Tabs, Tab, Accordion 
} from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import { mockTeacherAPI } from '../../services/mock/teacherAPI';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import './EnhancedDBStakingInterface.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const EnhancedDBStakingInterface = ({ 
    onStakingUpdate,
    className = ""
}) => {
    const [teacherInfo, setTeacherInfo] = useState(null);
    const [userBalance, setUserBalance] = useState(0);
    const [stakingAmount, setStakingAmount] = useState('');
    const [unstakingAmount, setUnstakingAmount] = useState('');
    const [processing, setProcessing] = useState(false);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(null);
    const [error, setError] = useState(null);
    const [showStakingModal, setShowStakingModal] = useState(false);
    const [activeTab, setActiveTab] = useState('stake');
    const [stakingHistory, setStakingHistory] = useState([]);
    const [projectedEarnings, setProjectedEarnings] = useState(null);

    // Enhanced tier information with benefits
    const tierInfo = {
        0: { 
            name: 'Bronze', 
            required: 0, 
            commission: 50, 
            color: '#CD7F32',
            benefits: ['Accesso base alla piattaforma', 'Supporto standard'],
            icon: 'award'
        },
        1: { 
            name: 'Silver', 
            required: 100, 
            commission: 45, 
            color: '#C0C0C0',
            benefits: ['Commissione ridotta 45%', 'Priorità supporto', 'Badge Silver'],
            icon: 'star'
        },
        2: { 
            name: 'Gold', 
            required: 300, 
            commission: 40, 
            color: '#FFD700',
            benefits: ['Commissione ridotta 40%', 'Analytics avanzate', 'Promozione corsi'],
            icon: 'trending-up'
        },
        3: { 
            name: 'Platinum', 
            required: 600, 
            commission: 35, 
            color: '#E5E4E2',
            benefits: ['Commissione ridotta 35%', 'Manager dedicato', 'Marketing support'],
            icon: 'crown'
        },
        4: { 
            name: 'Diamond', 
            required: 1000, 
            commission: 25, 
            color: '#B9F2FF',
            benefits: ['Commissione ridotta 25%', 'Accesso VIP', 'Revenue sharing'],
            icon: 'diamond'
        }
    };

    useEffect(() => {
        loadTeacherInfo();
        loadStakingHistory();
    }, []);

    // Load teacher staking information and balance
    const loadTeacherInfo = async () => {
        setLoading(true);
        try {
            // Try real API first
            try {
                const stakingResponse = await fetch('/api/v1/teocoin/staking-info/', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                        'Content-Type': 'application/json'
                    }
                });

                const balanceResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (stakingResponse.ok && balanceResponse.ok) {
                    const stakingData = await stakingResponse.json();
                    const balanceData = await balanceResponse.json();
                    
                    setTeacherInfo(stakingData.staking_info);
                    
                    if (balanceData.success && balanceData.balance) {
                        setUserBalance(parseFloat(balanceData.balance.available || 0));
                    } else {
                        setUserBalance(0);
                    }

                    // Calculate projected earnings
                    calculateProjectedEarnings(stakingData.staking_info);
                } else {
                    throw new Error('API endpoints not available');
                }
            } catch (apiError) {
                console.log('📡 Real API not available, using mock teacher data...');
                
                // Fallback to mock API
                const [stakingResponse, balanceResponse] = await Promise.all([
                    mockTeacherAPI.getStakingInfo(),
                    mockTeacherAPI.getBalance()
                ]);
                
                const stakingData = await stakingResponse.json();
                const balanceData = await balanceResponse.json();
                
                setTeacherInfo(stakingData.staking_info);
                
                if (balanceData.success && balanceData.balance) {
                    setUserBalance(parseFloat(balanceData.balance.available || 0));
                } else {
                    setUserBalance(0);
                }

                // Calculate projected earnings
                calculateProjectedEarnings(stakingData.staking_info);
                
                // Show info that we're using demo data
                setError('Demo Mode: Using sample staking data for demonstration');
            }
            
        } catch (error) {
            console.error('Error loading teacher info:', error);
            setError(error.message || 'Failed to load staking information');
        } finally {
            setLoading(false);
        }
    };

    // Load staking history for analytics
    const loadStakingHistory = async () => {
        try {
            const response = await fetch('/api/v1/teocoin/staking-history/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setStakingHistory(data.history || []);
            }
        } catch (error) {
            console.warn('Failed to load staking history:', error);
        }
    };

    // Calculate projected earnings based on current staking
    const calculateProjectedEarnings = (stakingInfo) => {
        if (!stakingInfo || !stakingInfo.staked_balance) {
            setProjectedEarnings(null);
            return;
        }

        const currentTier = getCurrentTier(stakingInfo.staked_balance);
        const monthlyRevenue = 1000; // Mock monthly revenue
        const commissionSaved = (50 - currentTier.commission) / 100;
        const monthlySavings = monthlyRevenue * commissionSaved;

        setProjectedEarnings({
            currentTier: currentTier.name,
            monthlyRevenue,
            commissionSaved: commissionSaved * 100,
            monthlySavings,
            yearlySavings: monthlySavings * 12
        });
    };

    // Get current tier based on staked amount
    const getCurrentTier = (stakedAmount) => {
        const amount = parseFloat(stakedAmount) || 0;
        
        for (let tier = 4; tier >= 0; tier--) {
            if (amount >= tierInfo[tier].required) {
                return tierInfo[tier];
            }
        }
        return tierInfo[0];
    };

    // Get next tier
    const getNextTier = (currentAmount) => {
        const amount = parseFloat(currentAmount) || 0;
        
        for (let tier = 1; tier <= 4; tier++) {
            if (amount < tierInfo[tier].required) {
                return tierInfo[tier];
            }
        }
        return null;
    };

    // Process DB-based staking
    const processDBStaking = async () => {
        if (!stakingAmount || parseFloat(stakingAmount) <= 0) {
            setError('Inserisci un importo valido per lo staking');
            return;
        }

        const amount = parseFloat(stakingAmount);
        if (amount > userBalance) {
            setError('Saldo insufficiente per lo staking');
            return;
        }
        
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            const response = await fetch('/api/v1/teocoin/stake/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: stakingAmount
                })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                setSuccess(`✅ Staking di ${stakingAmount} TEO completato con successo!`);
                setStakingAmount('');
                setShowStakingModal(false);
                
                // Refresh data
                await loadTeacherInfo();
                await loadStakingHistory();
                
                if (onStakingUpdate) {
                    onStakingUpdate(data);
                }
            } else {
                throw new Error(data.error || data.message || 'Errore durante lo staking');
            }
            
        } catch (error) {
            console.error('Staking error:', error);
            setError(error.message || 'Errore durante lo staking');
        } finally {
            setProcessing(false);
        }
    };

    // Process unstaking
    const processUnstaking = async () => {
        if (!unstakingAmount || parseFloat(unstakingAmount) <= 0) {
            setError('Inserisci un importo valido per l\'unstaking');
            return;
        }

        const amount = parseFloat(unstakingAmount);
        if (amount > parseFloat(teacherInfo?.staked_balance || 0)) {
            setError('Importo superiore al saldo in staking');
            return;
        }
        
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            const response = await fetch('/api/v1/teocoin/unstake/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: unstakingAmount
                })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                setSuccess(`✅ Unstaking di ${unstakingAmount} TEO completato con successo!`);
                setUnstakingAmount('');
                
                // Refresh data
                await loadTeacherInfo();
                await loadStakingHistory();
                
                if (onStakingUpdate) {
                    onStakingUpdate(data);
                }
            } else {
                throw new Error(data.error || data.message || 'Errore durante l\'unstaking');
            }
            
        } catch (error) {
            console.error('Unstaking error:', error);
            setError(error.message || 'Errore durante l\'unstaking');
        } finally {
            setProcessing(false);
        }
    };

    // Chart configuration for staking history
    const stakingChartConfig = {
        data: {
            labels: stakingHistory.slice(-7).map(item => 
                new Date(item.date).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })
            ),
            datasets: [
                {
                    label: 'TEO in Staking',
                    data: stakingHistory.slice(-7).map(item => parseFloat(item.amount)),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#007bff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#007bff',
                    borderWidth: 1,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                    ticks: {
                        color: '#6c757d',
                        callback: function(value) {
                            return value + ' TEO';
                        },
                    },
                },
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        color: '#6c757d',
                    },
                },
            },
        },
    };

    if (loading) {
        return (
            <Card className="enhanced-staking-interface">
                <Card.Body className="text-center py-5">
                    <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
                    <p className="mt-3 text-muted">Caricamento sistema di staking...</p>
                </Card.Body>
            </Card>
        );
    }

    const currentTier = getCurrentTier(teacherInfo?.staked_balance);
    const nextTier = getNextTier(teacherInfo?.staked_balance);
    const progressToNext = nextTier ? 
        ((parseFloat(teacherInfo?.staked_balance || 0) - currentTier.required) / 
         (nextTier.required - currentTier.required)) * 100 : 100;

    return (
        <div className={`enhanced-staking-interface ${className}`}>
            {/* Header Section */}
            <div className="staking-header">
                <Row className="align-items-center">
                    <Col>
                        <h4 className="staking-title mb-1">
                            <i className="feather icon-trending-up me-2"></i>
                            Sistema Staking Avanzato
                        </h4>
                        <p className="text-muted mb-0">
                            Riduci le commissioni stakando i tuoi TEO - Zero gas fees
                        </p>
                    </Col>
                    <Col xs="auto">
                        <Badge 
                            style={{ 
                                background: `linear-gradient(135deg, ${currentTier.color}, ${currentTier.color}99)`,
                                color: currentTier.name === 'Silver' || currentTier.name === 'Platinum' ? '#000' : '#fff',
                                padding: '0.75rem 1.5rem',
                                borderRadius: '25px',
                                fontSize: '1rem',
                                fontWeight: '600'
                            }}
                        >
                            <i className={`feather icon-${currentTier.icon} me-2`}></i>
                            {currentTier.name} Tier
                        </Badge>
                    </Col>
                </Row>
            </div>

            {/* Alert Messages */}
            {error && (
                <Alert variant="danger" dismissible onClose={() => setError(null)} className="modern-alert">
                    <i className="feather icon-alert-circle me-2"></i>
                    {error}
                </Alert>
            )}
            
            {success && (
                <Alert variant="success" dismissible onClose={() => setSuccess(null)} className="modern-alert">
                    <i className="feather icon-check-circle me-2"></i>
                    {success}
                </Alert>
            )}

            {/* Main Content */}
            <Row>
                {/* Current Status */}
                <Col lg={8}>
                    <Card className="staking-status-card border-0 mb-4">
                        <Card.Body className="p-4">
                            <Row>
                                <Col md={4}>
                                    <div className="status-metric">
                                        <div className="metric-icon bg-primary">
                                            <i className="feather icon-lock"></i>
                                        </div>
                                        <div className="metric-content">
                                            <h3 className="metric-value">{parseFloat(teacherInfo?.staked_balance || 0).toFixed(2)}</h3>
                                            <p className="metric-label">TEO in Staking</p>
                                        </div>
                                    </div>
                                </Col>
                                <Col md={4}>
                                    <div className="status-metric">
                                        <div className="metric-icon bg-success">
                                            <i className="feather icon-percent"></i>
                                        </div>
                                        <div className="metric-content">
                                            <h3 className="metric-value">{currentTier.commission}%</h3>
                                            <p className="metric-label">Commissione Piattaforma</p>
                                        </div>
                                    </div>
                                </Col>
                                <Col md={4}>
                                    <div className="status-metric">
                                        <div className="metric-icon bg-warning">
                                            <i className="feather icon-wallet"></i>
                                        </div>
                                        <div className="metric-content">
                                            <h3 className="metric-value">{userBalance.toFixed(2)}</h3>
                                            <p className="metric-label">TEO Disponibili</p>
                                        </div>
                                    </div>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>

                    {/* Tier Progress */}
                    {nextTier && (
                        <Card className="tier-progress-card border-0 mb-4">
                            <Card.Body className="p-4">
                                <div className="d-flex justify-content-between align-items-center mb-3">
                                    <h6 className="mb-0">
                                        <i className="feather icon-target me-2"></i>
                                        Progressione verso {nextTier.name}
                                    </h6>
                                    <Badge variant="info">
                                        {nextTier.required - parseFloat(teacherInfo?.staked_balance || 0)} TEO mancanti
                                    </Badge>
                                </div>
                                <ProgressBar 
                                    now={Math.max(0, Math.min(100, progressToNext))} 
                                    style={{ height: '12px' }}
                                    className="tier-progress-bar"
                                />
                                <div className="mt-3">
                                    <Row>
                                        <Col>
                                            <small className="text-muted">
                                                <strong>Benefici {nextTier.name}:</strong>
                                            </small>
                                            <ul className="benefits-list mt-2">
                                                {nextTier.benefits.map((benefit, index) => (
                                                    <li key={index} className="small text-muted">
                                                        <i className="feather icon-check text-success me-1"></i>
                                                        {benefit}
                                                    </li>
                                                ))}
                                            </ul>
                                        </Col>
                                    </Row>
                                </div>
                            </Card.Body>
                        </Card>
                    )}

                    {/* Actions */}
                    <Card className="actions-card border-0">
                        <Card.Body className="p-4">
                            <div className="d-flex gap-3 justify-content-center">
                                <Button
                                    variant="primary"
                                    size="lg"
                                    onClick={() => {
                                        setActiveTab('stake');
                                        setShowStakingModal(true);
                                    }}
                                    disabled={processing}
                                    className="staking-action-btn"
                                    style={{
                                        background: 'linear-gradient(135deg, #007bff, #0056b3)',
                                        border: 'none',
                                        borderRadius: '25px',
                                        padding: '0.75rem 2rem',
                                        boxShadow: '0 4px 15px rgba(0, 123, 255, 0.3)'
                                    }}
                                >
                                    <i className="feather icon-plus me-2"></i>
                                    Stake TEO
                                </Button>
                                
                                {parseFloat(teacherInfo?.staked_balance || 0) > 0 && (
                                    <Button
                                        variant="outline-secondary"
                                        size="lg"
                                        onClick={() => {
                                            setActiveTab('unstake');
                                            setShowStakingModal(true);
                                        }}
                                        disabled={processing}
                                        className="staking-action-btn"
                                        style={{
                                            borderRadius: '25px',
                                            padding: '0.75rem 2rem'
                                        }}
                                    >
                                        <i className="feather icon-minus me-2"></i>
                                        Unstake TEO
                                    </Button>
                                )}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>

                {/* Sidebar Analytics */}
                <Col lg={4}>
                    {/* Projected Earnings */}
                    {projectedEarnings && (
                        <Card className="earnings-card border-0 mb-4">
                            <Card.Header className="bg-gradient-success text-white">
                                <h6 className="mb-0">
                                    <i className="feather icon-trending-up me-2"></i>
                                    Risparmi Proiettati
                                </h6>
                            </Card.Header>
                            <Card.Body>
                                <div className="earnings-metric mb-3">
                                    <div className="d-flex justify-content-between">
                                        <span className="text-muted">Mensile:</span>
                                        <strong className="text-success">
                                            +{projectedEarnings.monthlySavings.toFixed(2)} TEO
                                        </strong>
                                    </div>
                                </div>
                                <div className="earnings-metric mb-3">
                                    <div className="d-flex justify-content-between">
                                        <span className="text-muted">Annuale:</span>
                                        <strong className="text-success">
                                            +{projectedEarnings.yearlySavings.toFixed(2)} TEO
                                        </strong>
                                    </div>
                                </div>
                                <div className="earnings-metric">
                                    <div className="d-flex justify-content-between">
                                        <span className="text-muted">Commissione risparmiata:</span>
                                        <Badge variant="success">
                                            {projectedEarnings.commissionSaved.toFixed(1)}%
                                        </Badge>
                                    </div>
                                </div>
                            </Card.Body>
                        </Card>
                    )}

                    {/* Staking History Chart */}
                    {stakingHistory.length > 0 && (
                        <Card className="chart-card border-0">
                            <Card.Header>
                                <h6 className="mb-0">
                                    <i className="feather icon-bar-chart-2 me-2"></i>
                                    Storico Staking (7 giorni)
                                </h6>
                            </Card.Header>
                            <Card.Body>
                                <div style={{ height: '200px' }}>
                                    <Line {...stakingChartConfig} />
                                </div>
                            </Card.Body>
                        </Card>
                    )}
                </Col>
            </Row>

            {/* Staking Modal */}
            <Modal 
                show={showStakingModal} 
                onHide={() => setShowStakingModal(false)}
                size="lg"
                centered
                className="staking-modal"
            >
                <Modal.Header closeButton className="border-0">
                    <Modal.Title>
                        <i className="feather icon-trending-up me-2"></i>
                        Gestione Staking
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body className="p-4">
                    <Tabs
                        activeKey={activeTab}
                        onSelect={(k) => setActiveTab(k)}
                        className="staking-tabs"
                    >
                        <Tab eventKey="stake" title={
                            <span><i className="feather icon-plus me-2"></i>Stake TEO</span>
                        }>
                            <div className="stake-form mt-4">
                                <Form.Group className="mb-4">
                                    <Form.Label className="fw-semibold">
                                        Importo da stakare (TEO)
                                    </Form.Label>
                                    <div className="input-group-modern">
                                        <Form.Control
                                            type="number"
                                            step="0.01"
                                            min="0"
                                            max={userBalance}
                                            value={stakingAmount}
                                            onChange={(e) => setStakingAmount(e.target.value)}
                                            placeholder="Inserisci importo..."
                                            className="modern-input"
                                        />
                                        <Button
                                            variant="outline-primary"
                                            onClick={() => setStakingAmount(userBalance.toString())}
                                            className="max-button"
                                        >
                                            MAX
                                        </Button>
                                    </div>
                                    <Form.Text className="text-muted">
                                        Disponibili: {userBalance.toFixed(2)} TEO
                                    </Form.Text>
                                </Form.Group>

                                <div className="stake-preview p-3 rounded bg-light mb-4">
                                    <h6 className="mb-3">Preview Benefici:</h6>
                                    {stakingAmount && parseFloat(stakingAmount) > 0 && (
                                        <div>
                                            <div className="d-flex justify-content-between mb-2">
                                                <span>Nuovo saldo staking:</span>
                                                <strong>
                                                    {(parseFloat(teacherInfo?.staked_balance || 0) + parseFloat(stakingAmount)).toFixed(2)} TEO
                                                </strong>
                                            </div>
                                            <div className="d-flex justify-content-between mb-2">
                                                <span>Nuovo tier:</span>
                                                <Badge 
                                                    style={{ 
                                                        backgroundColor: getCurrentTier(
                                                            parseFloat(teacherInfo?.staked_balance || 0) + parseFloat(stakingAmount)
                                                        ).color,
                                                        color: '#fff'
                                                    }}
                                                >
                                                    {getCurrentTier(
                                                        parseFloat(teacherInfo?.staked_balance || 0) + parseFloat(stakingAmount)
                                                    ).name}
                                                </Badge>
                                            </div>
                                            <div className="d-flex justify-content-between">
                                                <span>Nuova commissione:</span>
                                                <strong className="text-success">
                                                    {getCurrentTier(
                                                        parseFloat(teacherInfo?.staked_balance || 0) + parseFloat(stakingAmount)
                                                    ).commission}%
                                                </strong>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <Button
                                    variant="primary"
                                    size="lg"
                                    onClick={processDBStaking}
                                    disabled={processing || !stakingAmount || parseFloat(stakingAmount) <= 0}
                                    className="w-100 modern-button"
                                >
                                    {processing ? (
                                        <>
                                            <Spinner animation="border" size="sm" className="me-2" />
                                            Elaborazione...
                                        </>
                                    ) : (
                                        <>
                                            <i className="feather icon-lock me-2"></i>
                                            Conferma Staking
                                        </>
                                    )}
                                </Button>
                            </div>
                        </Tab>

                        <Tab eventKey="unstake" title={
                            <span><i className="feather icon-minus me-2"></i>Unstake TEO</span>
                        }>
                            <div className="unstake-form mt-4">
                                <Form.Group className="mb-4">
                                    <Form.Label className="fw-semibold">
                                        Importo da rilasciare (TEO)
                                    </Form.Label>
                                    <div className="input-group-modern">
                                        <Form.Control
                                            type="number"
                                            step="0.01"
                                            min="0"
                                            max={parseFloat(teacherInfo?.staked_balance || 0)}
                                            value={unstakingAmount}
                                            onChange={(e) => setUnstakingAmount(e.target.value)}
                                            placeholder="Inserisci importo..."
                                            className="modern-input"
                                        />
                                        <Button
                                            variant="outline-primary"
                                            onClick={() => setUnstakingAmount(teacherInfo?.staked_balance || '0')}
                                            className="max-button"
                                        >
                                            MAX
                                        </Button>
                                    </div>
                                    <Form.Text className="text-muted">
                                        In staking: {parseFloat(teacherInfo?.staked_balance || 0).toFixed(2)} TEO
                                    </Form.Text>
                                </Form.Group>

                                <div className="unstake-preview p-3 rounded bg-light mb-4">
                                    <h6 className="mb-3">Preview Modifiche:</h6>
                                    {unstakingAmount && parseFloat(unstakingAmount) > 0 && (
                                        <div>
                                            <div className="d-flex justify-content-between mb-2">
                                                <span>Nuovo saldo staking:</span>
                                                <strong>
                                                    {(parseFloat(teacherInfo?.staked_balance || 0) - parseFloat(unstakingAmount)).toFixed(2)} TEO
                                                </strong>
                                            </div>
                                            <div className="d-flex justify-content-between mb-2">
                                                <span>Nuovo tier:</span>
                                                <Badge 
                                                    style={{ 
                                                        backgroundColor: getCurrentTier(
                                                            parseFloat(teacherInfo?.staked_balance || 0) - parseFloat(unstakingAmount)
                                                        ).color,
                                                        color: '#fff'
                                                    }}
                                                >
                                                    {getCurrentTier(
                                                        parseFloat(teacherInfo?.staked_balance || 0) - parseFloat(unstakingAmount)
                                                    ).name}
                                                </Badge>
                                            </div>
                                            <div className="d-flex justify-content-between">
                                                <span>Nuova commissione:</span>
                                                <strong className="text-warning">
                                                    {getCurrentTier(
                                                        parseFloat(teacherInfo?.staked_balance || 0) - parseFloat(unstakingAmount)
                                                    ).commission}%
                                                </strong>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <Button
                                    variant="warning"
                                    size="lg"
                                    onClick={processUnstaking}
                                    disabled={processing || !unstakingAmount || parseFloat(unstakingAmount) <= 0}
                                    className="w-100 modern-button"
                                >
                                    {processing ? (
                                        <>
                                            <Spinner animation="border" size="sm" className="me-2" />
                                            Elaborazione...
                                        </>
                                    ) : (
                                        <>
                                            <i className="feather icon-unlock me-2"></i>
                                            Conferma Unstaking
                                        </>
                                    )}
                                </Button>
                            </div>
                        </Tab>
                    </Tabs>
                </Modal.Body>
            </Modal>
        </div>
    );
};

export default EnhancedDBStakingInterface;
