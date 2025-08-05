import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import jsconfigPaths from 'vite-jsconfig-paths';
import { splitVendorChunkPlugin } from 'vite';

export default defineConfig({
  server: {
    open: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  define: {
    global: 'window',
    'process.env': {}
  },
  resolve: {
    alias: []
  },
  css: {
    preprocessorOptions: {
      scss: { 
        charset: false,
        quietDeps: true,
        logger: {
          warn: function(message) {
            // Suppress Sass deprecation warnings
            if (message.includes('deprecation') || message.includes('deprecated')) {
              return;
            }
            console.warn(message);
          }
        }
      },
      less: { charset: false }
    },
    charset: false,
    postcss: {
      plugins: [
        {
          postcssPlugin: 'internal:charset-removal',
          AtRule: {
            charset: (atRule) => {
              if (atRule.name === 'charset') {
                atRule.remove();
              }
            }
          }
        }
      ]
    }
  },
  base: '/',
  plugins: [
    react({
      // Enable React refresh for better development experience
      include: "**/*.{jsx,tsx}",
      // Optimize production builds
      babel: {
        plugins: [
          process.env.NODE_ENV === 'production' && [
            'babel-plugin-transform-remove-console',
            { exclude: ['error', 'warn'] }
          ]
        ].filter(Boolean)
      }
    }), 
    jsconfigPaths(),
    splitVendorChunkPlugin()
  ],
  build: {
    // Production build optimizations
    target: 'es2020',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // Disable sourcemaps in production for smaller bundle
    minify: 'terser',
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom'],
          'bootstrap-vendor': ['react-bootstrap', 'bootstrap'],
          'router-vendor': ['react-router-dom'],
          
          // Feature-based chunks
          'dashboard': [
            './src/views/dashboard/StudentDashboard.jsx',
            './src/views/dashboard/TeacherDashboard.jsx'
          ],
          'courses': [
            './src/views/courses/AllCourses.jsx',
            './src/views/courses/StudentCourseDetail.jsx',
            './src/views/courses/StudentLessonDetail.jsx'
          ],
          'components': [
            './src/components/cards/CourseCard.jsx',
            './src/components/ui/StatWidget.jsx',
            './src/components/ui/LazyImage.jsx'
          ]
        },
        // Optimize chunk file names
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop().replace('.jsx', '').replace('.js', '') : 'chunk';
          return `assets/js/[name]-[hash].js`;
        },
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
            return `assets/images/[name]-[hash].${ext}`;
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash].${ext}`;
          }
          if (/\.(css)$/i.test(assetInfo.name)) {
            return `assets/css/[name]-[hash].${ext}`;
          }
          return `assets/[name]-[hash].${ext}`;
        }
      }
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
    
    // Asset optimization
    assetsInlineLimit: 4096, // Inline assets smaller than 4kb
    
    // CSS code splitting
    cssCodeSplit: true
  },
  optimizeDeps: {
    // Pre-bundle dependencies for faster dev startup
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'react-bootstrap',
      'bootstrap'
    ],
    // Exclude problematic dependencies
    exclude: ['@vite/client', '@vite/env']
  },
  
  // Performance optimizations
  esbuild: {
    // Remove console.log and debugger in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : []
  }
});