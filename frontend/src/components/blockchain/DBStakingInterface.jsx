/**
 * DB-Based Staking Interface
 * Instant teacher staking using database instead of blockchain
 * No gas fees, instant tier updates
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Form, Badge, Spinner, ProgressBar } from 'react-bootstrap';
import './DBStakingInterface.scss';

const DBStakingInterface = ({ 
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

    // Updated tier information (corrected business logic)
    const tierInfo = {
        0: { name: 'Bronze', required: 0, commission: 50, color: '#CD7F32' },     // 50% platform
        1: { name: 'Silver', required: 100, commission: 45, color: '#C0C0C0' },   // 45% platform
        2: { name: 'Gold', required: 300, commission: 40, color: '#FFD700' },     // 40% platform
        3: { name: 'Platinum', required: 600, commission: 35, color: '#E5E4E2' }, // 35% platform
        4: { name: 'Diamond', required: 1000, commission: 25, color: '#B9F2FF' }  // 25% platform
    };

    // Load teacher staking information and balance
    const loadTeacherInfo = async () => {
        setLoading(true);
        try {
            // Load teacher staking info
            const stakingResponse = await fetch('/api/v1/teocoin/staking-info/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            // Load user balance
            // Use withdrawal API for consistency
            const balanceResponse = await fetch('/api/v1/teocoin/withdrawals/balance/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (stakingResponse.ok && balanceResponse.ok) {
                const stakingData = await stakingResponse.json();
                const balanceData = await balanceResponse.json();
                
                console.log('🔍 Staking Balance API Response:', balanceData);
                
                setTeacherInfo(stakingData.staking_info);
                
                // Convert withdrawal API format
                if (balanceData.success && balanceData.balance) {
                    setUserBalance(parseFloat(balanceData.balance.available || 0));
                } else {
                    console.warn('Balance API returned no data:', balanceData);
                    setUserBalance(0);
                }
            } else {
                throw new Error('Failed to load teacher information');
            }
            
        } catch (error) {
            console.error('Error loading teacher info:', error);
            setError(error.message || 'Failed to load staking information');
        } finally {
            setLoading(false);
        }
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
            console.log('🚀 Processing DB-based staking...');
            console.log(`💰 Amount: ${stakingAmount} TEO`);
            console.log('⚡ Processing: Instant (DB operation)');
            console.log('💳 Gas cost: Free (no blockchain transaction)');

            const response = await fetch('/api/v1/teocoin/stake/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: amount
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to stake tokens');
            }

            const result = await response.json();
            
            if (result.success) {
                console.log('✅ DB staking successful!');
                
                setSuccess({
                    message: `Staking di ${result.staked_amount} TEO completato istantaneamente!`,
                    stakedAmount: result.staked_amount,
                    totalStaked: result.total_staked,
                    newTier: result.new_tier_info,
                    processingTime: 'Istantaneo',
                    gasCost: 'Gratuito'
                });
                
                // Reset form
                setStakingAmount('');
                
                // Reload teacher info
                await loadTeacherInfo();
                
                // Callback to parent
                if (onStakingUpdate) {
                    onStakingUpdate(result);
                }
                
            } else {
                throw new Error(result.error || 'Failed to stake tokens');
            }
            
        } catch (error) {
            console.error('❌ DB staking failed:', error);
            setError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    // Process DB-based unstaking
    const processDBUnstaking = async () => {
        if (!unstakingAmount || parseFloat(unstakingAmount) <= 0) {
            setError('Inserisci un importo valido per l\'unstaking');
            return;
        }
        
        const amount = parseFloat(unstakingAmount);
        if (amount > (teacherInfo?.staked_balance || 0)) {
            setError('Non puoi unstakare più di quanto hai in staking');
            return;
        }
        
        setProcessing(true);
        setError(null);
        setSuccess(null);
        
        try {
            console.log('🚀 Processing DB-based unstaking...');
            console.log(`💰 Amount: ${unstakingAmount} TEO`);
            
            const response = await fetch('/api/v1/teocoin/unstake/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: amount
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to unstake tokens');
            }

            const result = await response.json();
            
            if (result.success) {
                setSuccess({
                    message: `Unstaking di ${result.unstaked_amount} TEO completato istantaneamente!`,
                    unstakedAmount: result.unstaked_amount,
                    totalStaked: result.total_staked,
                    newTier: result.new_tier_info,
                    processingTime: 'Istantaneo',
                    gasCost: 'Gratuito'
                });
                
                setUnstakingAmount('');
                await loadTeacherInfo();
                
                if (onStakingUpdate) {
                    onStakingUpdate(result);
                }
                
            } else {
                throw new Error(result.error || 'Failed to unstake tokens');
            }
            
        } catch (error) {
            console.error('❌ DB unstaking failed:', error);
            setError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    // Load teacher info on mount
    useEffect(() => {
        loadTeacherInfo();
    }, []);

    // Calculate potential tier after staking
    const calculatePotentialTier = (currentAmount, additionalAmount) => {
        const totalAmount = parseFloat(currentAmount) + parseFloat(additionalAmount || 0);
        
        for (let tier = 4; tier >= 0; tier--) {
            if (totalAmount >= tierInfo[tier].required) {
                return tier;
            }
        }
        return 0;
    };

    if (loading) {
        return (
            <Card className={`staking-container ${className}`}>
                <Card.Body className="text-center">
                    <Spinner animation="border" className="mb-3" />
                    <p>Caricamento informazioni staking...</p>
                </Card.Body>
            </Card>
        );
    }

    const currentTier = teacherInfo?.tier || 0;
    const currentTierInfo = tierInfo[currentTier];
    const potentialTier = stakingAmount ? calculatePotentialTier(teacherInfo?.staked_balance || 0, stakingAmount) : currentTier;
    const potentialTierInfo = tierInfo[potentialTier];

    return (
        <Card className={`staking-container ${className}`}>
            <Card.Header className="bg-primary text-white">
                <div className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">
                        <i className="feather icon-layers me-2"></i>
                        Staking Insegnanti DB
                    </h5>
                    <Badge bg="light" text="dark">Istantaneo & Gratuito</Badge>
                </div>
            </Card.Header>

            <Card.Body>
                {/* Current Tier Status */}
                <div className="current-tier-section mb-4">
                    <h6 className="text-muted mb-3">Il Tuo Tier Attuale</h6>
                    <div className="tier-card" style={{ borderColor: currentTierInfo.color, borderWidth: '2px' }}>
                        <div className="bg-light p-3 rounded">
                            <div className="d-flex justify-content-between align-items-center mb-2">
                                <h5 style={{ color: currentTierInfo.color, margin: 0 }}>
                                    🏆 {currentTierInfo.name}
                                </h5>
                                <Badge bg="secondary">
                                    {currentTierInfo.commission}% Commissione Piattaforma
                                </Badge>
                            </div>
                            
                            <div className="row g-3">
                                <div className="col-4">
                                    <div className="text-center">
                                        <div className="h4 text-primary mb-1">{teacherInfo?.staked_balance || 0}</div>
                                        <small className="text-muted">TEO in Staking</small>
                                    </div>
                                </div>
                                <div className="col-4">
                                    <div className="text-center">
                                        <div className="h4 text-success mb-1">{100 - currentTierInfo.commission}%</div>
                                        <small className="text-muted">La Tua Commissione</small>
                                    </div>
                                </div>
                                <div className="col-4">
                                    <div className="text-center">
                                        <div className="h4 text-info mb-1">{userBalance}</div>
                                        <small className="text-muted">TEO Disponibili</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tier Progression */}
                <div className="tier-progression mb-4">
                    <h6 className="text-muted mb-3">Progressione Tier</h6>
                    <div className="row g-2">
                        {Object.entries(tierInfo).map(([tier, info]) => {
                            const isCurrentTier = parseInt(tier) === currentTier;
                            const isPotentialTier = parseInt(tier) === potentialTier && potentialTier !== currentTier;
                            const isUnlocked = (teacherInfo?.staked_balance || 0) >= info.required;
                            
                            return (
                                <div key={tier} className="col-12">
                                    <div 
                                        className={`tier-item p-2 rounded border ${isCurrentTier ? 'border-primary bg-primary bg-opacity-10' : ''} ${isPotentialTier ? 'border-success bg-success bg-opacity-10' : ''}`}
                                        style={{ borderLeftColor: info.color, borderLeftWidth: '4px' }}
                                    >
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div>
                                                <span className="fw-bold" style={{ color: info.color }}>
                                                    {info.name}
                                                    {isCurrentTier && <Badge bg="primary" className="ms-2">ATTUALE</Badge>}
                                                    {isPotentialTier && <Badge bg="success" className="ms-2">PROSSIMO</Badge>}
                                                </span>
                                                <div className="small text-muted">
                                                    {info.required} TEO richiesti • {100 - info.commission}% commissione insegnante
                                                </div>
                                            </div>
                                            <div className="text-end">
                                                {isUnlocked ? (
                                                    <i className="feather icon-check-circle text-success"></i>
                                                ) : (
                                                    <i className="feather icon-lock text-muted"></i>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Staking Section */}
                <div className="staking-section mb-4">
                    <h6 className="text-muted mb-3">
                        <i className="feather icon-trending-up me-2"></i>
                        Aggiungi TEO al Staking
                    </h6>
                    <Form.Group className="mb-3">
                        <div className="input-group">
                            <Form.Control
                                type="number"
                                value={stakingAmount}
                                onChange={(e) => setStakingAmount(e.target.value)}
                                placeholder="Importo da stakare"
                                min="1"
                                max={userBalance}
                                step="1"
                                disabled={processing}
                            />
                            <span className="input-group-text">TEO</span>
                        </div>
                        <Form.Text className="text-muted">
                            Disponibile: {userBalance} TEO
                        </Form.Text>
                    </Form.Group>
                    
                    {stakingAmount && potentialTier > currentTier && (
                        <Alert variant="success" className="py-2">
                            <i className="feather icon-arrow-up me-2"></i>
                            <strong>Upgrade Tier!</strong> Questo ti porterà al tier <strong style={{ color: potentialTierInfo.color }}>
                                {potentialTierInfo.name}
                            </strong> con commissione del <strong>{100 - potentialTierInfo.commission}%</strong>
                        </Alert>
                    )}
                    
                    <Button
                        variant="primary"
                        className="w-100"
                        onClick={processDBStaking}
                        disabled={processing || !stakingAmount || parseFloat(stakingAmount) <= 0 || parseFloat(stakingAmount) > userBalance}
                    >
                        {processing ? (
                            <>
                                <Spinner animation="border" size="sm" className="me-2" />
                                Elaborazione...
                            </>
                        ) : (
                            <>
                                <i className="feather icon-layers me-2"></i>
                                Stake TEO (Istantaneo)
                            </>
                        )}
                    </Button>
                </div>

                {/* Unstaking Section */}
                {teacherInfo?.staked_balance > 0 && (
                    <div className="unstaking-section mb-4">
                        <h6 className="text-muted mb-3">
                            <i className="feather icon-trending-down me-2"></i>
                            Rimuovi TEO dal Staking
                        </h6>
                        <Form.Group className="mb-3">
                            <div className="input-group">
                                <Form.Control
                                    type="number"
                                    value={unstakingAmount}
                                    onChange={(e) => setUnstakingAmount(e.target.value)}
                                    placeholder="Importo da unstakare"
                                    min="1"
                                    max={teacherInfo?.staked_balance || 0}
                                    step="1"
                                    disabled={processing}
                                />
                                <span className="input-group-text">TEO</span>
                            </div>
                            <Form.Text className="text-muted">
                                In staking: {teacherInfo?.staked_balance || 0} TEO
                            </Form.Text>
                        </Form.Group>
                        
                        <Button
                            variant="outline-secondary"
                            className="w-100"
                            onClick={processDBUnstaking}
                            disabled={processing || !unstakingAmount || parseFloat(unstakingAmount) <= 0}
                        >
                            {processing ? (
                                <>
                                    <Spinner animation="border" size="sm" className="me-2" />
                                    Elaborazione...
                                </>
                            ) : (
                                <>
                                    <i className="feather icon-minus me-2"></i>
                                    Unstake TEO (Istantaneo)
                                </>
                            )}
                        </Button>
                    </div>
                )}

                {/* Success State */}
                {success && (
                    <Alert variant="success" className="mb-3">
                        <div className="d-flex flex-column">
                            <div className="fw-bold">
                                <i className="feather icon-check-circle me-2"></i>
                                {success.message}
                            </div>
                            {success.newTier && (
                                <div className="mt-2 small">
                                    <div>🏆 Nuovo Tier: <strong style={{ color: tierInfo[success.newTier.tier]?.color }}>
                                        {success.newTier.tier_name}
                                    </strong></div>
                                    <div>💰 Commissione: <strong>{success.newTier.commission_rate}%</strong></div>
                                </div>
                            )}
                            <div className="mt-2 small text-muted">
                                <div>⚡ Tempo: {success.processingTime}</div>
                                <div>💳 Costo: {success.gasCost}</div>
                            </div>
                        </div>
                    </Alert>
                )}

                {/* Error State */}
                {error && (
                    <Alert variant="danger" className="mb-3">
                        <i className="feather icon-x-circle me-2"></i>
                        {error}
                    </Alert>
                )}

                {/* How It Works */}
                <div className="how-it-works">
                    <h6 className="text-muted mb-3">
                        <i className="feather icon-help-circle me-2"></i>
                        Come Funziona il Sistema DB
                    </h6>
                    <div className="bg-info bg-opacity-10 p-3 rounded">
                        <div className="row g-2">
                            <div className="col-4 text-center">
                                <div className="text-info mb-1">⚡</div>
                                <small className="text-muted">Istantaneo</small>
                            </div>
                            <div className="col-4 text-center">
                                <div className="text-success mb-1">💳</div>
                                <small className="text-muted">Gratuito</small>
                            </div>
                            <div className="col-4 text-center">
                                <div className="text-primary mb-1">🔄</div>
                                <small className="text-muted">Reversibile</small>
                            </div>
                        </div>
                        <hr className="my-2" />
                        <small className="text-muted">
                            <strong>Vantaggi vs Blockchain:</strong> Nessuna attesa, nessun gas fee, 
                            aggiornamento tier immediato. Puoi sempre prelevare i TEO su MetaMask quando vuoi.
                        </small>
                    </div>
                </div>
            </Card.Body>
        </Card>
    );
};

export default DBStakingInterface;
