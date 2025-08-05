// Utility functions for smooth scrolling to dashboard sections

/**
 * Scrolls to an element by text content in a header
 * @param {string} text - Text to search for in headers
 * @param {string} headerSelector - CSS selector for headers (default: 'h2, h3, h4, h5, h6')
 * @param {Object} options - Scroll options
 */
export const scrollToSectionByText = (text, headerSelector = 'h2, h3, h4, h5, h6', options = {}) => {
  const defaultOptions = {
    behavior: 'smooth',
    block: 'center',
    inline: 'nearest'
  };
  
  const scrollOptions = { ...defaultOptions, ...options };
  
  try {
    // Find header containing the text
    const headers = document.querySelectorAll(headerSelector);
    const targetHeader = Array.from(headers).find(header => 
      header.textContent.includes(text)
    );
    
    if (targetHeader) {
      targetHeader.scrollIntoView(scrollOptions);
      return true;
    }
    
    console.warn(`No header found containing text: "${text}"`);
    return false;
  } catch (error) {
    console.error('Error scrolling to section:', error);
    return false;
  }
};

/**
 * Scrolls to an element by title attribute or data attribute
 * @param {string} titleValue - Value to search for in title attribute
 * @param {Object} options - Scroll options
 */
export const scrollToElementByTitle = (titleValue, options = {}) => {
  const defaultOptions = {
    behavior: 'smooth',
    block: 'center',
    inline: 'nearest'
  };
  
  const scrollOptions = { ...defaultOptions, ...options };
  
  try {
    // Try title attribute first
    let element = document.querySelector(`[title="${titleValue}"]`);
    
    // If not found, try data-title attribute
    if (!element) {
      element = document.querySelector(`[data-title="${titleValue}"]`);
    }
    
    // If found, find the closest container
    if (element) {
      const container = element.closest('.col-md-4, .col-md-6, .col-md-8, .card, .widget') || element;
      container.scrollIntoView(scrollOptions);
      return true;
    }
    
    console.warn(`No element found with title: "${titleValue}"`);
    return false;
  } catch (error) {
    console.error('Error scrolling to element:', error);
    return false;
  }
};

/**
 * Scrolls to the top of the main container
 * @param {Object} options - Scroll options
 */
export const scrollToTop = (options = {}) => {
  const defaultOptions = {
    behavior: 'smooth',
    block: 'start',
    inline: 'nearest'
  };
  
  const scrollOptions = { ...defaultOptions, ...options };
  
  try {
    // Try to find main container
    const container = document.querySelector('.container, .container-fluid, main, #main') || 
                     document.body;
    
    container.scrollIntoView(scrollOptions);
    return true;
  } catch (error) {
    console.error('Error scrolling to top:', error);
    return false;
  }
};

/**
 * Scrolls to a specific selector with fallback options
 * @param {string|string[]} selectors - CSS selector(s) to try
 * @param {Object} options - Scroll options
 */
export const scrollToSelector = (selectors, options = {}) => {
  const defaultOptions = {
    behavior: 'smooth',
    block: 'center',
    inline: 'nearest'
  };
  
  const scrollOptions = { ...defaultOptions, ...options };
  const selectorArray = Array.isArray(selectors) ? selectors : [selectors];
  
  try {
    for (const selector of selectorArray) {
      const element = document.querySelector(selector);
      if (element) {
        element.scrollIntoView(scrollOptions);
        return true;
      }
    }
    
    console.warn('No element found for selectors:', selectorArray);
    return false;
  } catch (error) {
    console.error('Error scrolling to selector:', error);
    return false;
  }
};

/**
 * Navigate to a URL as a fallback when scroll actions fail
 * @param {string} url - URL to navigate to
 */
export const navigateToUrl = (url) => {
  try {
    if (url.startsWith('/')) {
      window.location.href = url;
    } else {
      console.warn('Invalid URL provided for navigation:', url);
    }
  } catch (error) {
    console.error('Error navigating to URL:', error);
  }
};

/**
 * Utility function to combine scroll action with URL fallback
 * @param {Function} scrollAction - Primary scroll action to attempt
 * @param {string} fallbackUrl - URL to navigate to if scroll fails
 */
export const scrollWithFallback = (scrollAction, fallbackUrl = null) => {
  try {
    // Check if we're on the dashboard page
    const isDashboardPage = window.location.pathname.includes('/dashboard');
    
    // If we're already on the dashboard page, try to scroll
    if (isDashboardPage) {
      const success = scrollAction();
      if (!success && fallbackUrl) {
        console.info('Scroll action failed, navigating to fallback URL:', fallbackUrl);
        navigateToUrl(fallbackUrl);
      }
      return success;
    } else {
      // If we're not on the dashboard page, navigate to the fallback URL
      if (fallbackUrl) {
        console.info('Not on dashboard page, navigating to fallback URL:', fallbackUrl);
        navigateToUrl(fallbackUrl);
        return true;
      } else {
        // If no fallback URL is provided, try to navigate to the dashboard
        const userType = getUserTypeFromURL();
        if (userType) {
          navigateToUrl(`/dashboard/${userType}`);
          return true;
        }
        // Last resort - navigate to the main dashboard
        navigateToUrl('/dashboard');
        return true;
      }
    }
  } catch (error) {
    console.error('Error in scroll action:', error);
    if (fallbackUrl) {
      navigateToUrl(fallbackUrl);
    }
    return false;
  }
};

/**
 * Helper function to determine user type from URL
 */
const getUserTypeFromURL = () => {
  const path = window.location.pathname;
  if (path.includes('/student/') || path.includes('/studente/')) {
    return 'student';
  } else if (path.includes('/teacher/') || path.includes('/docente/')) {
    return 'teacher';
  } else if (path.includes('/admin/')) {
    return 'admin';
  }
  return null;
};

// Dashboard-specific scroll functions
export const dashboardScrollActions = {
  // Student Dashboard
  student: {
    overview: () => scrollWithFallback(
      () => scrollToTop(),
      '/dashboard/student'
    ),
    balance: () => scrollWithFallback(
      () => scrollToElementByTitle('Saldo TeoCoin') || scrollToSectionByText('Saldo TeoCoin'),
      '/dashboard/student#balance'
    ),
    courses: () => scrollWithFallback(
      () => scrollToSectionByText('Corsi acquistati') || scrollToSectionByText('I Miei Corsi'),
      '/dashboard/student#courses'
    ),
    transactions: () => scrollWithFallback(
      () => scrollToSectionByText('Ultime Transazioni') || scrollToSectionByText('Transazioni'),
      '/dashboard/student#transactions'
    ),
    exercises: () => scrollWithFallback(
      () => scrollToSectionByText('I miei esercizi') || scrollToSectionByText('Esercizi'),
      '/dashboard/student#exercises'
    )
  },
  
  // Teacher Dashboard
  teacher: {
    overview: () => scrollWithFallback(
      () => scrollToTop(),
      '/dashboard/teacher'
    ),
    balance: () => scrollWithFallback(
      () => scrollToElementByTitle('Saldo TeoCoin') || scrollToSectionByText('Saldo TeoCoin'),
      '/dashboard/teacher#balance'
    ),
    sales: () => scrollWithFallback(
      () => scrollToSectionByText('Vendite') || scrollToSelector(['.dash-sales', '[data-section="sales"]']),
      '/dashboard/teacher#sales'
    ),
    courses: () => scrollWithFallback(
      () => scrollToSectionByText('Corsi creati') || scrollToSectionByText('I Miei Corsi'),
      '/dashboard/teacher#courses'
    ),
    lessons: () => scrollWithFallback(
      () => scrollToSectionByText('Lezioni') || scrollToSelector(['[data-section="lessons"]']),
      '/dashboard/teacher#lessons'
    ),
    transactions: () => scrollWithFallback(
      () => scrollToSectionByText('Ultime Transazioni') || scrollToSectionByText('Transazioni'),
      '/dashboard/teacher#transactions'
    ),
    smartContracts: () => scrollWithFallback(
      () => scrollToSectionByText('Smart Contract') || scrollToSelector(['[data-section="contracts"]']),
      '/dashboard/teacher#contracts'
    )
  },
  
  // Admin Dashboard
  admin: {
    overview: () => scrollWithFallback(
      () => scrollToTop(),
      '/dashboard/admin'
    ),
    balance: () => scrollWithFallback(
      () => scrollToElementByTitle('Saldo TeoCoin') || scrollToSectionByText('Saldo TeoCoin'),
      '/dashboard/admin#balance'
    ),
    pendingTeachers: () => scrollWithFallback(
      () => scrollToSectionByText('Docenti Pending') || scrollToSectionByText('Maestri in attesa'),
      '/dashboard/admin#pending-teachers'
    ),
    pendingCourses: () => scrollWithFallback(
      () => scrollToSectionByText('Corsi Pending') || scrollToSectionByText('Corsi in attesa'),
      '/dashboard/admin#pending-courses'
    ),
    userManagement: () => scrollWithFallback(
      () => scrollToSectionByText('User Management') || scrollToSectionByText('Gestione Utenti'),
      '/dashboard/admin#user-management'
    )
  }
};
