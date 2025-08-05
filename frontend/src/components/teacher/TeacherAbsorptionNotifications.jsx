import React, { useState, useEffect } from 'react';
import { Card, Badge, Button, Alert, Spinner, Row, Col } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import TeacherDiscountChoiceModal from './TeacherDiscountChoiceModal';

/**
 * Teacher Absorption Notifications Component
 * 
 * Displays pending TeoCoin discount absorption opportunities for teachers
 * Allows teachers to make choices between EUR commission vs TEO absorption
 */
const TeacherAbsorptionNotifications = () => {
    const { user } = useAuth();
    const [absorptions, setAbsorptions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedAbsorption, setSelectedAbsorption] = useState(null);
    const [showModal, setShowModal] = useState(false);

    const fetchAbsorptions = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch('/api/v1/teocoin/teacher/absorptions/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setAbsorptions(data.pending_absorptions || []);
            } else {
                setError(data.error || 'Failed to fetch absorption opportunities');
            }
            
        } catch (error) {
            console.error('Error fetching absorptions:', error);
            setError('Network error. Please refresh to try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchAbsorptions();
            
            // Refresh every 30 seconds to catch new opportunities
            const interval = setInterval(fetchAbsorptions, 30000);
            return () => clearInterval(interval);
        }
    }, [user]);

    const handleAbsorptionClick = (absorption) => {
        setSelectedAbsorption(absorption);
        setShowModal(true);
    };

    const handleChoice = async (choiceData) => {
        // Refresh the list after a choice is made
        await fetchAbsorptions();
        
        // Show success message or handle the choice result
        console.log('Teacher choice made:', choiceData);
    };

    const getTimeRemainingBadge = (hoursRemaining) => {
        if (hoursRemaining > 12) {
            return <Badge bg="success">{hoursRemaining.toFixed(1)}h left</Badge>;
        } else if (hoursRemaining > 3) {
            return <Badge bg="warning">{hoursRemaining.toFixed(1)}h left</Badge>;
        } else {
            return <Badge bg="danger">{hoursRemaining.toFixed(1)}h left</Badge>;
        }
    };

    if (loading) {
        return (
            <Card>
                <Card.Body className="text-center">
                    <Spinner animation="border" size="sm" className="me-2" />
                    Loading absorption opportunities...
                </Card.Body>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <Card.Header>
                    <div className="d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">
                            <i className="fas fa-handshake me-2"></i>
                            TeoCoin Discount Opportunities
                        </h5>
                        <Button
                            variant="outline-primary"
                            size="sm"
                            onClick={fetchAbsorptions}
                            disabled={loading}
                        >
                            <i className="fas fa-sync-alt me-1"></i>
                            Refresh
                        </Button>
                    </div>
                </Card.Header>
                
                <Card.Body>
                    {error && (
                        <Alert variant="danger">
                            <i className="fas fa-exclamation-triangle me-2"></i>
                            {error}
                        </Alert>
                    )}

                    {absorptions.length === 0 ? (
                        <div className="text-center text-muted py-4">
                            <i className="fas fa-inbox fa-3x mb-3"></i>
                            <h5>No pending opportunities</h5>
                            <p>You'll be notified when students use TeoCoin discounts on your courses.</p>
                        </div>
                    ) : (
                        <div>
                            <div className="mb-3">
                                <small className="text-muted">
                                    You have {absorptions.length} pending discount absorption 
                                    opportunit{absorptions.length === 1 ? 'y' : 'ies'}
                                </small>
                            </div>
                            
                            {absorptions.map((absorption) => (
                                <Card 
                                    key={absorption.id} 
                                    className="mb-3 border-start border-4 border-warning cursor-pointer"
                                    onClick={() => handleAbsorptionClick(absorption)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <Card.Body>
                                        <Row>
                                            <Col md={8}>
                                                <h6 className="mb-2">
                                                    <i className="fas fa-graduation-cap me-2"></i>
                                                    {absorption.course.title}
                                                </h6>
                                                <div className="small text-muted mb-2">
                                                    <strong>Student:</strong> {absorption.student.username || absorption.student.email}
                                                    <span className="mx-2">•</span>
                                                    <strong>Discount:</strong> {absorption.discount.percentage}%
                                                    <span className="mx-2">•</span>
                                                    <strong>TEO Used:</strong> {absorption.discount.teo_used} TEO
                                                </div>
                                                <div className="small">
                                                    <Row>
                                                        <Col sm={6}>
                                                            <strong>Option A (EUR):</strong> €{absorption.options.option_a.teacher_eur}
                                                        </Col>
                                                        <Col sm={6}>
                                                            <strong>Option B (TEO):</strong> {absorption.options.option_b.teacher_teo} TEO + €{absorption.options.option_b.teacher_eur}
                                                        </Col>
                                                    </Row>
                                                </div>
                                            </Col>
                                            <Col md={4} className="text-end">
                                                <div className="mb-2">
                                                    {getTimeRemainingBadge(absorption.timing.hours_remaining)}
                                                </div>
                                                <Button
                                                    variant="primary"
                                                    size="sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleAbsorptionClick(absorption);
                                                    }}
                                                >
                                                    <i className="fas fa-handshake me-1"></i>
                                                    Make Choice
                                                </Button>
                                            </Col>
                                        </Row>
                                    </Card.Body>
                                </Card>
                            ))}
                        </div>
                    )}
                </Card.Body>
            </Card>

            {/* Choice Modal */}
            <TeacherDiscountChoiceModal
                show={showModal}
                handleClose={() => setShowModal(false)}
                discountRequest={selectedAbsorption}
                onChoice={handleChoice}
            />
        </>
    );
};

export default TeacherAbsorptionNotifications;
