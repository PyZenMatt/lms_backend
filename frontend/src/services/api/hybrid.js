import api from '../core/axiosClient';

export const initiateHybridPayment = async (courseId, teocoinToSpend, walletAddress) => {
  return api.post(`courses/${courseId}/hybrid-payment/`, {
    teocoin_to_spend: teocoinToSpend,
    wallet_address: walletAddress
  });
};

export const confirmHybridPayment = async (courseId, paymentIntentId) => {
  return api.put(`courses/${courseId}/hybrid-payment/`, {
    payment_intent_id: paymentIntentId
  });
};
