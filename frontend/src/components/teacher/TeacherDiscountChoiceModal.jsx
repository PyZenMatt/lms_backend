import React, { useState } from 'react';
import { Modal, Button, Alert, Badge, Spinner } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

/**
 * PHASE 3.3: Teacher Discount Choice Modal
 * 
 * Allows teachers to make decisions on student discount requests:
 * - Accept TeoCoin: Get TEO tokens + bonus
 * - Take Full Fiat: Get full EUR payment
 */
const TeacherDiscountChoiceModal = ({ 
    show, 
    handleClose, 
    discountRequest, 
    onChoice 
}) => {
    const { user } = useAuth();
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState('');

    const handleChoice = async (choice) => {
        if (!discountRequest) return;
        
        setProcessing(true);
        setError('');
        
        try {
            const response = await fetch('/api/v1/teocoin/teacher/absorptions/choose/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: JSON.stringify({
                    absorption_id: discountRequest.id,
                    choice: choice === 'accept' ? 'absorb' : 'refuse'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Notify parent component
                if (onChoice) {
                    onChoice({
                        choice,
                        data,
                        discountRequest
                    });
                }
                handleClose();
            } else {
                setError(data.error || 'Failed to submit choice');
            }
            
        } catch (error) {
            console.error('Choice submission failed:', error);
            setError('Network error. Please try again.');
        } finally {
            setProcessing(false);
        }
    };

    if (!discountRequest) return null;

    const {
        course,
        student,
        discount,
        options,
        timing
    } = discountRequest;

    // Extract data from the new API format
    const studentEmail = student?.email || student?.username || 'Unknown';
    const courseTitle = course?.title || 'Unknown Course';
    const coursePrice = course?.price || 0;
    const discountPercent = discount?.percentage || 0;
    const teoUsed = discount?.teo_used || 0;
    const discountAmountEur = discount?.eur_amount || 0;
    
    const optionA = options?.option_a || {};
    const optionB = options?.option_b || {};
    
    const expiresAt = timing?.expires_at || new Date();
    const hoursRemaining = timing?.hours_remaining || 0;

    // Calculate earnings comparison
    const fiatDifference = optionA.teacher_eur - optionB.teacher_eur;
    const teoGained = optionB.teacher_teo;

    return (
        <Modal show={show} onHide={handleClose} size="lg" centered>
            <Modal.Header closeButton>
                <Modal.Title>
                    <i className="fas fa-handshake me-2"></i>
                    Student Discount Request
                </Modal.Title>
            </Modal.Header>
            
            <Modal.Body>
                {error && (
                    <Alert variant="danger">
                        <i className="fas fa-exclamation-triangle me-2"></i>
                        {error}
                    </Alert>
                )}

                {/* Request Details */}
                <div className="mb-4">
                    <h5>Request Details</h5>
                    <div className="bg-light p-3 rounded">
                        <div className="row">
                            <div className="col-md-6">
                                <strong>Student:</strong> {studentEmail}<br/>
                                <strong>Course:</strong> {courseTitle}<br/>
                                <strong>Course Price:</strong> €{coursePrice}
                            </div>
                            <div className="col-md-6">
                                <strong>Discount Requested:</strong> 
                                <Badge bg="primary" className="ms-2">{discountPercent}%</Badge><br/>
                                <strong>TEO Used:</strong> {teoUsed} TEO<br/>
                                <strong>Expires:</strong> {new Date(expiresAt).toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Choice Options */}
                <div className="mb-4">
                    <h5>Your Options</h5>
                    
                    {/* Accept TeoCoin Option */}
                    <div className="border rounded p-3 mb-3" style={{borderColor: '#28a745'}}>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 className="text-success mb-1">
                                    <i className="fab fa-bitcoin me-2"></i>
                                    Absorb Discount for TEO + Bonus
                                </h6>
                                <p className="mb-2">
                                    Accept the {discountPercent}% discount and receive TEO tokens with 25% bonus
                                </p>
                                <div className="small text-muted">
                                    <strong>You receive:</strong><br/>
                                    • €{optionB.teacher_eur} (reduced EUR commission)<br/>
                                    • {optionB.teacher_teo} TEO tokens (original + 25% bonus)<br/>
                                    • Platform pays: €{optionB.platform_eur}
                                </div>
                            </div>
                            <Button 
                                variant="success" 
                                onClick={() => handleChoice('accept')}
                                disabled={processing}
                                className="ms-3"
                            >
                                {processing ? (
                                    <Spinner size="sm" className="me-2" />
                                ) : (
                                    <i className="fas fa-check me-2"></i>
                                )}
                                Accept TEO
                            </Button>
                        </div>
                    </div>

                    {/* Decline / Full Fiat Option */}
                    <div className="border rounded p-3" style={{borderColor: '#007bff'}}>
                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 className="text-primary mb-1">
                                    <i className="fas fa-euro-sign me-2"></i>
                                    Keep Full EUR Commission
                                </h6>
                                <p className="mb-2">
                                    Platform absorbs the discount cost, you get full EUR commission
                                </p>
                                <div className="small text-muted">
                                    <strong>You receive:</strong><br/>
                                    • €{optionA.teacher_eur} (full EUR commission)<br/>
                                    • 0 TEO tokens<br/>
                                    • Platform pays: €{optionA.platform_eur}
                                </div>
                            </div>
                            <Button 
                                variant="primary" 
                                onClick={() => handleChoice('decline')}
                                disabled={processing}
                                className="ms-3"
                            >
                                {processing ? (
                                    <Spinner size="sm" className="me-2" />
                                ) : (
                                    <i className="fas fa-money-bill me-2"></i>
                                )}
                                Take EUR
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Earnings Comparison */}
                <div className="mb-4">
                    <h6>Earnings Comparison</h6>
                    <div className="bg-info bg-opacity-10 p-3 rounded">
                        <div className="row text-center">
                            <div className="col-md-4">
                                <strong>EUR Difference</strong><br/>
                                <span className="text-danger">
                                    -€{fiatDifference?.toFixed(2) || 0}
                                </span><br/>
                                <small className="text-muted">Less EUR if you accept TEO</small>
                            </div>
                            <div className="col-md-4">
                                <strong>TEO Gained</strong><br/>
                                <span className="text-success">
                                    +{teoGained} TEO
                                </span><br/>
                                <small className="text-muted">TEO tokens + 25% bonus</small>
                            </div>
                            <div className="col-md-4">
                                <strong>Time Remaining</strong><br/>
                                <Badge bg={hoursRemaining > 12 ? 'success' : hoursRemaining > 3 ? 'warning' : 'danger'}>
                                    {hoursRemaining.toFixed(1)}h left
                                </Badge><br/>
                                <small className="text-muted">Auto-EUR if expired</small>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Additional Info */}
                <div className="small text-muted">
                    <i className="fas fa-info-circle me-1"></i>
                    <strong>Note:</strong> TEO tokens can be staked to reduce your platform commission rate 
                    and can be used for future transactions or held as investment.
                </div>
            </Modal.Body>
            
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose} disabled={processing}>
                    Cancel
                </Button>
                <div className="ms-auto small text-muted">
                    Decision expires: {new Date(expiresAt).toLocaleString()}
                </div>
            </Modal.Footer>
        </Modal>
    );
};

export default TeacherDiscountChoiceModal;
