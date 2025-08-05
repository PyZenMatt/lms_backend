/**
 * Enhanced PaymentModal with Layer 2 Gas-Free TeoCoin Integration
 * This component integrates the Layer 2 system for truly gas-free discounts
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
    Elements,
    CardElement,
    useStripe,
    useElements
} from '@stripe/react-stripe-js';
import { ethers } from 'ethers';
import '../../assets/css/components/PaymentModal.css';

// TODO: Replace Layer 2 component with current DB-based TeoCoin system
// import Layer2TeoCoinDiscount from './Layer2TeoCoinDiscount';

// Fix Stripe key - use VITE prefix for Vite build system
const stripePromise = loadStripe(
    process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 
    import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
);

const PaymentModal = ({ 
    isOpen, 
    onClose, 
    course, 
    onPaymentSuccess,
    onError,
    discountInfo: propsDiscountInfo = null  // Accept discountInfo as prop
}) => {
    const [web3Provider, setWeb3Provider] = useState(null);
    const [walletAddress, setWalletAddress] = useState('');
    const [walletConnected, setWalletConnected] = useState(false);
    const [discountApplied, setDiscountApplied] = useState(false);
    const [discountInfo, setDiscountInfo] = useState(propsDiscountInfo);  // Initialize with prop
    const [paymentMethod, setPaymentMethod] = useState('fiat');
    const [showLayer2, setShowLayer2] = useState(false);

    // Handle discount info from props
    useEffect(() => {
        console.log('🔍 PaymentModal received course:', course);
        console.log('🔍 PaymentModal received discountInfo:', propsDiscountInfo);
        
        if (propsDiscountInfo) {
            setDiscountInfo(propsDiscountInfo);
            setDiscountApplied(true);
            console.log('💰 Discount info received from props:', propsDiscountInfo);
        }
    }, [propsDiscountInfo, course]);

    // Connect MetaMask wallet
    const connectWallet = async () => {
        try {
            if (window.ethereum) {
                console.log('🦊 Connecting to MetaMask...');
                
                // Request account access
                await window.ethereum.request({
                    method: 'eth_requestAccounts'
                });

                // Create provider
                const provider = new ethers.BrowserProvider(window.ethereum);
                const signer = await provider.getSigner();
                const address = await signer.getAddress();
                
                console.log('✅ Wallet connected:', address);
                
                setWeb3Provider(provider);
                setWalletAddress(address.toLowerCase());
                setWalletConnected(true);
                
                // Check network
                const network = await provider.getNetwork();
                if (network.chainId !== 80002n) {
                    alert('⚠️ Please switch to Polygon Amoy testnet (Chain ID: 80002)');
                }
                
            } else {
                throw new Error('MetaMask not found. Please install MetaMask browser extension.');
            }
        } catch (error) {
            console.error('❌ Wallet connection failed:', error);
            onError(error.message);
        }
    };

    // Handle Layer 2 discount application
    const handleLayer2DiscountApplied = (discountData) => {
        console.log('✅ Layer 2 discount applied:', discountData);
        
        setDiscountApplied(true);
        setDiscountInfo(discountData);
        setShowLayer2(false);
        
        // Store discount for payment completion
        localStorage.setItem('applied_teocoin_discount', JSON.stringify({
            ...discountData,
            layer2_processed: true,
            gas_free: true
        }));
        
        // Switch to fiat payment to complete the process
        setPaymentMethod('fiat');
    };

    // Calculate final price with discount
    const basePrice = parseFloat(course?.price_eur || course?.price || 0);
    const calculatedFinalPrice = discountInfo 
        ? (parseFloat(discountInfo.final_price) || basePrice - parseFloat(discountInfo.discount_amount || 0))
        : basePrice;
    const finalPrice = isNaN(calculatedFinalPrice) ? 0 : calculatedFinalPrice;

    // Safe number formatting function
    const formatPrice = (value) => {
        const num = parseFloat(value || 0);
        return isNaN(num) ? '0.00' : num.toFixed(2);
    };

    if (!isOpen || !course) return null;

    return (
        <div className="payment-modal-overlay">
            <div className="payment-modal">
                <div className="modal-header">
                    <h2>💳 Complete Your Purchase</h2>
                    <button onClick={onClose} className="close-btn">×</button>
                </div>

                <div className="course-info">
                    <h3>{course?.title || 'Course'}</h3>
                    <p>Instructor: {course?.teacher?.username || 'N/A'}</p>
                    <div className="pricing-info">
                        {discountApplied ? (
                            <div className="discount-applied">
                                <p className="original-price">Original: €{formatPrice(course?.price_eur || course?.price)}</p>
                                <p className="discount-amount">
                                    TeoCoin Discount: -€{formatPrice(discountInfo?.discount_amount)}
                                    {discountInfo?.gas_free && <span className="gas-free-badge">⛽ Gas-Free</span>}
                                </p>
                                <p className="final-price">Final Price: €{formatPrice(finalPrice)}</p>
                                {discountInfo?.layer2_processed && (
                                    <p className="layer2-processed">🚀 Processed via Layer 2</p>
                                )}
                            </div>
                        ) : (
                            <p className="price">Price: €{formatPrice(course?.price_eur || course?.price)}</p>
                        )}
                    </div>
                </div>

                {/* Wallet Connection Section */}
                <div className="wallet-section">
                    {!walletConnected ? (
                        <div className="connect-wallet">
                            <h4>🔗 Connect Wallet for TeoCoin Discounts</h4>
                            <button 
                                onClick={connectWallet}
                                className="connect-wallet-btn"
                            >
                                🦊 Connect MetaMask
                            </button>
                            <p className="wallet-note">
                                Connect your wallet to use gas-free TeoCoin discounts
                            </p>
                        </div>
                    ) : (
                        <div className="wallet-connected">
                            <p>✅ Wallet Connected: {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}</p>
                            {!discountApplied && (
                                <button 
                                    onClick={() => setShowLayer2(true)}
                                    className="teocoin-discount-btn"
                                >
                                    🚀 Apply Layer 2 TeoCoin Discount
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Layer 2 TeoCoin Discount Component */}
                {showLayer2 && (
                    <Layer2TeoCoinDiscount
                        course={course}
                        onDiscountApplied={handleLayer2DiscountApplied}
                        onError={onError}
                        web3Provider={web3Provider}
                        walletAddress={walletAddress}
                    />
                )}

                {/* Payment Method Selection */}
                <div className="payment-methods">
                    <h4>💳 Payment Method</h4>
                    <div className="payment-options">
                        <label className="payment-option">
                            <input
                                type="radio"
                                value="fiat"
                                checked={paymentMethod === 'fiat'}
                                onChange={(e) => setPaymentMethod(e.target.value)}
                            />
                            <span>💳 Credit/Debit Card</span>
                            {discountApplied && <span className="discounted-amount">€{formatPrice(finalPrice)}</span>}
                        </label>
                    </div>
                </div>

                {/* Stripe Payment Form */}
                {paymentMethod === 'fiat' && (
                    <Elements stripe={stripePromise}>
                        <CardPaymentForm 
                            course={course}
                            finalPrice={finalPrice}
                            discountInfo={discountInfo}
                            onPaymentSuccess={onPaymentSuccess}
                            onError={onError}
                            formatPrice={formatPrice}
                        />
                    </Elements>
                )}

                {/* Benefits Display */}
                {discountApplied && discountInfo.gas_free && (
                    <div className="layer2-benefits-summary">
                        <h4>🚀 Layer 2 Benefits Applied</h4>
                        <ul>
                            <li>⛽ Zero gas fees for you</li>
                            <li>🚀 Instant discount processing</li>
                            <li>💰 €{discountInfo.discount_amount} discount applied</li>
                            <li>🏗️ Platform handled all blockchain fees</li>
                        </ul>
                    </div>
                )}

                <style jsx>{`
                    .payment-modal-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    }
                    
                    .payment-modal {
                        background: white;
                        padding: 30px;
                        border-radius: 15px;
                        max-width: 600px;
                        width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                    }
                    
                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 15px;
                    }
                    
                    .close-btn {
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #666;
                    }
                    
                    .wallet-section {
                        margin: 20px 0;
                        padding: 20px;
                        border: 2px solid #e3f2fd;
                        border-radius: 10px;
                        background: #f8f9fa;
                    }
                    
                    .connect-wallet-btn {
                        background: #ff6b35;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }
                    
                    .connect-wallet-btn:hover {
                        background: #ff5722;
                        transform: translateY(-2px);
                    }
                    
                    .teocoin-discount-btn {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    
                    .discount-applied {
                        background: #e8f5e8;
                        padding: 15px;
                        border-radius: 8px;
                        border: 2px solid #4CAF50;
                    }
                    
                    .gas-free-badge {
                        background: #4CAF50;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        margin-left: 10px;
                    }
                    
                    .layer2-processed {
                        color: #2196F3;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    
                    .layer2-benefits-summary {
                        background: #e3f2fd;
                        padding: 15px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }
                    
                    .layer2-benefits-summary ul {
                        list-style: none;
                        padding: 0;
                        margin: 10px 0 0 0;
                    }
                    
                    .layer2-benefits-summary li {
                        padding: 5px 0;
                        font-weight: 500;
                    }
                `}</style>
            </div>
        </div>
    );
};

// Simplified Card Payment Form Component
const CardPaymentForm = ({ course, finalPrice, discountInfo, onPaymentSuccess, onError, formatPrice }) => {
    const stripe = useStripe();
    const elements = useElements();
    const [processing, setProcessing] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setProcessing(true);

        console.log('🔄 Starting payment process...');
        console.log('💳 Stripe instance:', stripe);
        console.log('🧩 Elements instance:', elements);
        console.log('💰 Final price:', finalPrice);
        console.log('🎁 Discount info:', discountInfo);

        if (!stripe || !elements) {
            console.error('❌ Stripe not loaded properly');
            onError('Stripe not loaded. Please refresh the page.');
            setProcessing(false);
            return;
        }

        const cardElement = elements.getElement(CardElement);
        if (!cardElement) {
            console.error('❌ Card element not found');
            onError('Card form not loaded. Please refresh the page.');
            setProcessing(false);
            return;
        }

        console.log('✅ Stripe and card element ready');

        try {
            // Validate card element before proceeding
            const {error: cardError} = await stripe.createPaymentMethod({
                type: 'card',
                card: cardElement,
            });

            if (cardError) {
                console.error('❌ Card validation error:', cardError);
                if (cardError.code === 'incomplete_zip') {
                    throw new Error('Please enter a complete ZIP/postal code (e.g., 12345)');
                }
                throw new Error(cardError.message);
            }

            console.log('✅ Card validation passed');

            // Create payment intent with discount info
            const { createPaymentIntent } = await import('../services/api/courses');
            const response = await createPaymentIntent(course.id, {
                teocoin_discount: discountInfo?.discount_amount || 0,
                payment_method: 'stripe',
                wallet_address: discountInfo?.student_wallet,
                final_amount: finalPrice,
                discount_info: discountInfo
            });

            if (response.data.success) {
                const { client_secret } = response.data;
                
                console.log('💳 Payment intent created successfully:', response.data);
                console.log('🔐 Client secret received:', client_secret);

                // Confirm payment with Stripe
                console.log('💳 Confirming payment with Stripe...');
                const result = await stripe.confirmCardPayment(client_secret, {
                    payment_method: {
                        card: elements.getElement(CardElement),
                    }
                });

                console.log('💳 Stripe confirmation result:', result);

                if (result.error) {
                    console.error('❌ Stripe payment error:', result.error);
                    if (result.error.code === 'incomplete_zip') {
                        throw new Error('Please enter a complete ZIP/postal code (5 digits, e.g., 12345)');
                    }
                    throw new Error(result.error.message);
                } else {
                    console.log('✅ Payment successful!', result.paymentIntent);
                    
                    // For Layer 2 TeoCoin discounts, student is already enrolled and teacher notified
                    // No additional backend completion needed - the system is designed to be immediate
                    if (discountInfo && discountInfo.discount_amount > 0) {
                        console.log('� Layer 2 TeoCoin discount payment completed!');
                        console.log('💰 Student already enrolled with discount');
                        console.log('📧 Teacher notification already sent');
                        
                        onPaymentSuccess({
                            ...result.paymentIntent,
                            discount_applied: !!discountInfo,
                            layer2_processed: discountInfo?.layer2_processed,
                            immediate_enrollment: true,
                            teacher_notified: true,
                            system_status: 'Layer 2 discount completed - no additional processing needed'
                        });
                    } else {
                        // Regular payment without discount
                        onPaymentSuccess({
                            ...result.paymentIntent,
                            discount_applied: !!discountInfo,
                            layer2_processed: discountInfo?.layer2_processed
                        });
                    }
                }
            } else {
                throw new Error(response.data.error);
            }
        } catch (error) {
            console.error('💳 Payment process error:', error);
            onError(error.message);
        } finally {
            setProcessing(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="card-payment-form">
            <div className="card-element-container">
                <CardElement 
                    options={{
                        style: {
                            base: {
                                fontSize: '16px',
                                color: '#424770',
                                '::placeholder': {
                                    color: '#aab7c4',
                                },
                                fontFamily: 'Arial, sans-serif',
                                fontSmoothing: 'antialiased',
                                padding: '12px',
                            },
                            invalid: {
                                color: '#fa755a',
                                iconColor: '#fa755a'
                            }
                        },
                        hidePostalCode: false, // Ensure postal code field is visible
                        disabled: false,
                    }}
                />
            </div>
            
            <div className="payment-info">
                <p className="test-card-info">
                    🧪 <strong>Test Mode Instructions:</strong><br/>
                    • Card Number: <code>4242 4242 4242 4242</code><br/>
                    • Expiry: Any future date (e.g., 12/28)<br/>
                    • CVC: Any 3 digits (e.g., 123)<br/>
                    • ZIP/Postal Code: <strong>12345</strong> (must be 5 digits)<br/>
                    <em>⚠️ Make sure to fill ALL fields completely!</em>
                </p>
            </div>
            
            <button 
                type="submit" 
                disabled={!stripe || processing}
                className="pay-button"
            >
                {processing ? 'Processing...' : `Pay €${formatPrice(finalPrice)}`}
            </button>
            
            <style jsx>{`
                .card-payment-form {
                    margin-top: 20px;
                }
                
                .card-element-container {
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background: #fff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .payment-info {
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                
                .test-card-info {
                    margin: 0;
                    font-size: 14px;
                    color: #856404;
                    line-height: 1.6;
                }
                
                .test-card-info code {
                    background: #f8f9fa;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-weight: bold;
                    color: #495057;
                }
                
                .pay-button {
                    width: 100%;
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                
                .pay-button:hover:not(:disabled) {
                    background: #0056b3;
                }
                
                .pay-button:disabled {
                    background: #6c757d;
                    cursor: not-allowed;
                }
            `}</style>
        </form>
    );
};

export default PaymentModal;
