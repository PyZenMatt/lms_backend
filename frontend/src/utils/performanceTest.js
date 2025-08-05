// Frontend Performance Testing Script
// Automated tests for React app performance optimizations

import { performance } from 'perf_hooks';

class FrontendPerformanceTester {
  constructor() {
    this.results = [];
    this.baseURL = 'http://localhost:3000';
  }

  // Test page load performance
  async testPageLoad(url) {
    console.log(`🧪 Testing page load: ${url}`);
    const startTime = performance.now();
    
    try {
      const response = await fetch(`${this.baseURL}${url}`);
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      const result = {
        test: 'Page Load',
        url,
        loadTime: Math.round(loadTime),
        status: response.status,
        pass: loadTime < 2000 // Should load in under 2 seconds
      };
      
      this.results.push(result);
      console.log(`${result.pass ? '✅' : '❌'} ${url}: ${result.loadTime}ms`);
      return result;
    } catch (error) {
      console.error(`❌ Failed to load ${url}:`, error);
      return { test: 'Page Load', url, error: error.message, pass: false };
    }
  }

  // Test API response times
  async testAPIPerformance(endpoint, expectedTime = 1000) {
    console.log(`🧪 Testing API: ${endpoint}`);
    const startTime = performance.now();
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      const result = {
        test: 'API Performance',
        endpoint,
        responseTime: Math.round(responseTime),
        status: response.status,
        pass: responseTime < expectedTime
      };
      
      this.results.push(result);
      console.log(`${result.pass ? '✅' : '❌'} ${endpoint}: ${result.responseTime}ms`);
      return result;
    } catch (error) {
      console.error(`❌ API test failed ${endpoint}:`, error);
      return { test: 'API Performance', endpoint, error: error.message, pass: false };
    }
  }

  // Test bundle size
  async testBundleSize() {
    console.log('🧪 Testing bundle sizes...');
    
    try {
      const manifestResponse = await fetch(`${this.baseURL}/assets/manifest.json`);
      const manifest = await manifestResponse.json();
      
      const jsFiles = Object.keys(manifest).filter(key => key.endsWith('.js'));
      const cssFiles = Object.keys(manifest).filter(key => key.endsWith('.css'));
      
      let totalJSSize = 0;
      let totalCSSSize = 0;
      
      // Check JS bundle sizes
      for (const jsFile of jsFiles) {
        try {
          const response = await fetch(`${this.baseURL}/${manifest[jsFile]}`);
          const size = parseInt(response.headers.get('content-length')) || 0;
          totalJSSize += size;
        } catch (error) {
          console.warn(`Could not get size for ${jsFile}`);
        }
      }
      
      // Check CSS bundle sizes
      for (const cssFile of cssFiles) {
        try {
          const response = await fetch(`${this.baseURL}/${manifest[cssFile]}`);
          const size = parseInt(response.headers.get('content-length')) || 0;
          totalCSSSize += size;
        } catch (error) {
          console.warn(`Could not get size for ${cssFile}`);
        }
      }
      
      const result = {
        test: 'Bundle Size',
        totalJSSize: Math.round(totalJSSize / 1024), // KB
        totalCSSSize: Math.round(totalCSSSize / 1024), // KB
        totalSize: Math.round((totalJSSize + totalCSSSize) / 1024), // KB
        pass: (totalJSSize + totalCSSSize) < 1024 * 1024 // Under 1MB
      };
      
      this.results.push(result);
      console.log(`${result.pass ? '✅' : '❌'} Bundle size: ${result.totalSize}KB (JS: ${result.totalJSSize}KB, CSS: ${result.totalCSSSize}KB)`);
      return result;
    } catch (error) {
      console.error('❌ Bundle size test failed:', error);
      return { test: 'Bundle Size', error: error.message, pass: false };
    }
  }

  // Test memory usage simulation
  async testMemoryUsage() {
    console.log('🧪 Testing memory usage...');
    
    if (!window.performance || !window.performance.memory) {
      console.warn('⚠️ Performance.memory not available');
      return { test: 'Memory Usage', error: 'Not supported', pass: false };
    }
    
    const initialMemory = window.performance.memory.usedJSHeapSize;
    
    // Simulate heavy operations
    const heavyArray = new Array(100000).fill(0).map((_, i) => ({ id: i, data: `test-${i}` }));
    
    // Force garbage collection if available
    if (window.gc) {
      window.gc();
    }
    
    const finalMemory = window.performance.memory.usedJSHeapSize;
    const memoryIncrease = finalMemory - initialMemory;
    
    const result = {
      test: 'Memory Usage',
      initialMemory: Math.round(initialMemory / 1024 / 1024), // MB
      finalMemory: Math.round(finalMemory / 1024 / 1024), // MB
      increase: Math.round(memoryIncrease / 1024 / 1024), // MB
      pass: memoryIncrease < 10 * 1024 * 1024 // Under 10MB increase
    };
    
    this.results.push(result);
    console.log(`${result.pass ? '✅' : '❌'} Memory increase: ${result.increase}MB`);
    
    // Clean up
    heavyArray.length = 0;
    
    return result;
  }

  // Test render performance
  async testRenderPerformance() {
    console.log('🧪 Testing render performance...');
    
    const startTime = performance.now();
    
    // Simulate multiple re-renders
    for (let i = 0; i < 100; i++) {
      const div = document.createElement('div');
      div.innerHTML = `<div class="test-component">${i}</div>`;
      document.body.appendChild(div);
      document.body.removeChild(div);
    }
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    const result = {
      test: 'Render Performance',
      renderTime: Math.round(renderTime),
      pass: renderTime < 100 // Should complete in under 100ms
    };
    
    this.results.push(result);
    console.log(`${result.pass ? '✅' : '❌'} Render test: ${result.renderTime}ms`);
    return result;
  }

  // Run all performance tests
  async runAllTests() {
    console.log('🚀 Starting Frontend Performance Tests...\n');
    
    const tests = [
      // Page load tests
      () => this.testPageLoad('/'),
      () => this.testPageLoad('/dashboard'),
      () => this.testPageLoad('/courses'),
      
      // API performance tests
      () => this.testAPIPerformance('/core/api/student/batch-data/', 500),
      () => this.testAPIPerformance('/core/dashboard/teacher/', 800),
      () => this.testAPIPerformance('/courses/courses/', 600),
      () => this.testAPIPerformance('/core/health/', 200),
      
      // Resource tests
      () => this.testBundleSize(),
      () => this.testMemoryUsage(),
      () => this.testRenderPerformance()
    ];
    
    for (const test of tests) {
      try {
        await test();
        await new Promise(resolve => setTimeout(resolve, 100)); // Brief pause between tests
      } catch (error) {
        console.error('Test failed:', error);
      }
    }
    
    this.generateReport();
  }

  // Generate performance report
  generateReport() {
    console.log('\n📊 FRONTEND PERFORMANCE REPORT\n');
    console.log('=' * 50);
    
    const passed = this.results.filter(r => r.pass).length;
    const total = this.results.length;
    const passRate = Math.round((passed / total) * 100);
    
    console.log(`Overall: ${passed}/${total} tests passed (${passRate}%)\n`);
    
    // Group results by test type
    const groupedResults = this.results.reduce((groups, result) => {
      const key = result.test;
      if (!groups[key]) groups[key] = [];
      groups[key].push(result);
      return groups;
    }, {});
    
    Object.entries(groupedResults).forEach(([testType, results]) => {
      console.log(`${testType}:`);
      results.forEach(result => {
        const status = result.pass ? '✅' : '❌';
        if (result.error) {
          console.log(`  ${status} ${result.url || result.endpoint || 'Test'}: ERROR - ${result.error}`);
        } else if (result.loadTime) {
          console.log(`  ${status} ${result.url}: ${result.loadTime}ms`);
        } else if (result.responseTime) {
          console.log(`  ${status} ${result.endpoint}: ${result.responseTime}ms`);
        } else if (result.totalSize) {
          console.log(`  ${status} Bundle: ${result.totalSize}KB`);
        } else if (result.increase !== undefined) {
          console.log(`  ${status} Memory increase: ${result.increase}MB`);
        } else if (result.renderTime) {
          console.log(`  ${status} Render: ${result.renderTime}ms`);
        }
      });
      console.log('');
    });
    
    // Recommendations
    console.log('💡 RECOMMENDATIONS:\n');
    
    const slowPages = this.results.filter(r => r.test === 'Page Load' && r.loadTime > 2000);
    if (slowPages.length > 0) {
      console.log('- Optimize slow loading pages:');
      slowPages.forEach(page => console.log(`  • ${page.url}: ${page.loadTime}ms`));
    }
    
    const slowAPIs = this.results.filter(r => r.test === 'API Performance' && r.responseTime > 1000);
    if (slowAPIs.length > 0) {
      console.log('- Optimize slow API endpoints:');
      slowAPIs.forEach(api => console.log(`  • ${api.endpoint}: ${api.responseTime}ms`));
    }
    
    const largeBundles = this.results.filter(r => r.test === 'Bundle Size' && r.totalSize > 500);
    if (largeBundles.length > 0) {
      console.log('- Consider bundle splitting for large bundles');
    }
    
    if (passRate === 100) {
      console.log('🎉 All performance tests passed! Your optimizations are working great!');
    } else if (passRate >= 80) {
      console.log('👍 Good performance! Consider addressing the failing tests above.');
    } else {
      console.log('⚠️ Performance needs improvement. Focus on the failing tests above.');
    }
  }
}

// Export for use in browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FrontendPerformanceTester;
} else {
  window.FrontendPerformanceTester = FrontendPerformanceTester;
}

// Auto-run if called directly
if (typeof window !== 'undefined' && window.location) {
  // Browser environment - expose globally
  window.runPerformanceTests = () => {
    const tester = new FrontendPerformanceTester();
    return tester.runAllTests();
  };
  
  console.log('Frontend Performance Tester loaded. Run with: runPerformanceTests()');
}
