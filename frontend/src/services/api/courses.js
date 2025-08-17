import api from '../core/axiosClient';

// ⚡ PERFORMANCE: Cache for payment-related API calls
const apiCache = new Map();
const CACHE_DURATION = 3 * 60 * 1000; // 3 minutes

const getCachedResponse = (key) => {
  const cached = apiCache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }
  return null;
};

const setCachedResponse = (key, data) => {
  apiCache.set(key, {
    data,
    timestamp: Date.now()
  });
};

export const fetchCourses = async (params = {}) => {
  const searchParams = new URLSearchParams();

  // Aggiungi parametri di filtro se presenti
  if (params.category && params.category !== 'all') {
    searchParams.append('category', params.category);
  }
  if (params.search) {
    searchParams.append('search', params.search);
  }
  if (params.ordering) {
    searchParams.append('ordering', params.ordering);
  }

  const queryString = searchParams.toString();
  const endpoint = queryString ? `courses/?${queryString}` : 'courses/';

  return api.get(endpoint);
};

export const purchaseCourse = async (courseId, walletAddress, transactionData = {}) => {
  return api.post(`courses/${courseId}/purchase/`, {
    wallet_address: walletAddress,
    ...transactionData
  });
};

export const createCourse = async (data) => {
  // Se data è FormData, non impostare Content-Type (axios lo gestirà automaticamente)
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data'
    };
  }
  return api.post('courses/', data, config);
};

// Crea una lezione associata a un corso
export const createLesson = async (data) => {
  // L'endpoint backend corretto è 'lessons/create/'
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data'
    };
  }
  return api.post('lessons/create/', data, config);
};

// Recupera le lezioni di un corso
export const fetchLessonsForCourse = async (courseId) => {
  return api.get(`courses/${courseId}/lessons/`);
};

export const createExercise = async (data) => {
  // L'endpoint backend accetta { title, description, lesson }
  const config = {};
  if (data instanceof FormData) {
    config.headers = {
      'Content-Type': 'multipart/form-data'
    };
  }
  return api.post('exercises/create/', data, config);
};

export const fetchExercisesForLesson = async (lessonId) => {
  return api.get(`lessons/${lessonId}/exercises/`);
};

export const fetchCourseDetail = async (courseId) => {
  const response = await api.get(`courses/${courseId}/`);
  return response.data;
};

export const fetchLessonDetail = async (lessonId) => {
  const response = await api.get(`lessons/${lessonId}/`);
  return response.data;
};

export const fetchExerciseDetail = async (exerciseId) => {
  const response = await api.get(`exercises/${exerciseId}/`);
  return response.data;
};

// ⚡ OPTIMIZED Payment endpoints with caching and performance improvements
export const createPaymentIntent = async (courseId, options = {}) => {
  // No caching for payment intents (security)
  const payload = {
    teocoin_discount: options.teocoin_discount || 0,
    payment_method: options.payment_method || 'stripe',
    wallet_address: options.wallet_address, // Include wallet address for TeoCoin payments
    approval_tx_hash: options.approval_tx_hash // Include approval hash if available
  };
  return api.post(`courses/${courseId}/create-payment-intent/`, payload);
};

export const confirmPayment = async (courseId, paymentIntentId) => {
  // No caching for payment confirmations (security)
  const response = await api.post(`courses/${courseId}/confirm-payment/`, {
    payment_intent_id: paymentIntentId
  });

  // ⚡ PERFORMANCE: Invalidate payment summary cache after successful payment
  if (response.data.success) {
    const cacheKey = `payment_summary_${courseId}`;
    apiCache.delete(cacheKey);
  }

  return response;
};

export const getPaymentSummary = async (courseId) => {
  // ⚡ PERFORMANCE: Try cache first for payment summary
  const cacheKey = `payment_summary_${courseId}`;
  const cached = getCachedResponse(cacheKey);

  if (cached) {
    return cached;
  }

  const response = await api.get(`courses/${courseId}/payment-summary/`);

  // Cache successful responses
  if (response.data.success) {
    setCachedResponse(cacheKey, response);
  }

  return response;
};

export const completeHybridPayment = async (courseId, paymentIntentId) => {
  console.log('🔄 Calling completeHybridPayment API:', { courseId, paymentIntentId });

  // Call the backend completion endpoint that triggers TeoCoin transfer and teacher notification
  const response = await api.put(`courses/${courseId}/hybrid-payment/`, {
    payment_intent_id: paymentIntentId
  });

  console.log('✅ Hybrid payment completion response:', response.data);

  return response;
};

export const updateCourse = async (courseId, formData) => {
  console.log('🔄 Updating course:', courseId, formData);
  return api.put(`courses/${courseId}/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};
