// Form validation utilities for enhanced user experience

export const validateCourseForm = (formData) => {
  const errors = {};
  
  // Title validation
  if (!formData.title?.trim()) {
    errors.title = 'Il titolo è obbligatorio';
  } else if (formData.title.length < 3) {
    errors.title = 'Il titolo deve contenere almeno 3 caratteri';
  } else if (formData.title.length > 100) {
    errors.title = 'Il titolo non può superare i 100 caratteri';
  }
  
  // Description validation
  if (!formData.description?.trim()) {
    errors.description = 'La descrizione è obbligatoria';
  } else if (formData.description.length < 10) {
    errors.description = 'La descrizione deve contenere almeno 10 caratteri';
  } else if (formData.description.length > 1000) {
    errors.description = 'La descrizione non può superare i 1000 caratteri';
  }
  
  // Price validation
  if (!formData.price) {
    errors.price = 'Il prezzo è obbligatorio';
  } else if (isNaN(formData.price) || formData.price < 0) {
    errors.price = 'Il prezzo deve essere un numero positivo';
  } else if (formData.price > 10000) {
    errors.price = 'Il prezzo non può superare i 10000 TeoCoin';
  }
  
  // Category validation
  if (!formData.category) {
    errors.category = 'Seleziona una categoria';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateLessonForm = (formData) => {
  const errors = {};
  
  // Title validation
  if (!formData.title?.trim()) {
    errors.title = 'Il titolo è obbligatorio';
  } else if (formData.title.length < 3) {
    errors.title = 'Il titolo deve contenere almeno 3 caratteri';
  } else if (formData.title.length > 200) {
    errors.title = 'Il titolo non può superare i 200 caratteri';
  }
  
  // Content validation
  if (!formData.content?.trim()) {
    errors.content = 'Il contenuto è obbligatorio';
  } else if (formData.content.length < 20) {
    errors.content = 'Il contenuto deve contenere almeno 20 caratteri';
  }
  
  // Duration validation
  if (!formData.duration) {
    errors.duration = 'La durata è obbligatoria';
  } else if (isNaN(formData.duration) || formData.duration < 1) {
    errors.duration = 'La durata deve essere almeno 1 minuto';
  } else if (formData.duration > 300) {
    errors.duration = 'La durata non può superare i 300 minuti';
  }
  
  // Video validation for video lessons
  if (formData.lessonType === 'video' && !formData.videoFile) {
    errors.videoFile = 'Il video è obbligatorio per le lezioni video';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateExerciseForm = (formData) => {
  const errors = {};
  
  // Title validation
  if (!formData.title?.trim()) {
    errors.title = 'Il titolo è obbligatorio';
  } else if (formData.title.length < 3) {
    errors.title = 'Il titolo deve contenere almeno 3 caratteri';
  } else if (formData.title.length > 200) {
    errors.title = 'Il titolo non può superare i 200 caratteri';
  }
  
  // Description validation
  if (!formData.description?.trim()) {
    errors.description = 'La descrizione è obbligatoria';
  } else if (formData.description.length < 10) {
    errors.description = 'La descrizione deve contenere almeno 10 caratteri';
  }
  
  // Time estimate validation
  if (!formData.timeEstimate) {
    errors.timeEstimate = 'Il tempo stimato è obbligatorio';
  } else if (isNaN(formData.timeEstimate) || formData.timeEstimate < 1) {
    errors.timeEstimate = 'Il tempo deve essere almeno 1 minuto';
  } else if (formData.timeEstimate > 480) {
    errors.timeEstimate = 'Il tempo non può superare le 8 ore (480 minuti)';
  }
  
  // Materials validation
  if (!formData.materials?.trim()) {
    errors.materials = 'I materiali sono obbligatori';
  } else if (formData.materials.length < 5) {
    errors.materials = 'Descrivi almeno 5 caratteri per i materiali';
  }
  
  // Instructions validation
  if (!formData.instructions?.trim()) {
    errors.instructions = 'Le istruzioni sono obbligatorie';
  } else if (formData.instructions.length < 20) {
    errors.instructions = 'Le istruzioni devono contenere almeno 20 caratteri';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Real-time validation helpers
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Progress calculation for forms
export const calculateProgress = (formData, requiredFields) => {
  const filledFields = requiredFields.filter(field => {
    const value = formData[field];
    return value && (typeof value === 'string' ? value.trim() : true);
  });
  
  return Math.round((filledFields.length / requiredFields.length) * 100);
};

// File validation helpers
export const validateImageFile = (file) => {
  const errors = [];
  
  if (!file.type.startsWith('image/')) {
    errors.push('Il file deve essere un\'immagine');
  }
  
  if (file.size > 5 * 1024 * 1024) {
    errors.push('L\'immagine deve essere inferiore a 5MB');
  }
  
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    errors.push('Formato non supportato. Usa JPG, PNG, GIF o WebP');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

export const validateVideoFile = (file) => {
  const errors = [];
  
  if (!file.type.startsWith('video/')) {
    errors.push('Il file deve essere un video');
  }
  
  if (file.size > 50 * 1024 * 1024) {
    errors.push('Il video deve essere inferiore a 50MB');
  }
  
  const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'];
  if (!allowedTypes.includes(file.type)) {
    errors.push('Formato non supportato. Usa MP4, AVI, MOV o WMV');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};
