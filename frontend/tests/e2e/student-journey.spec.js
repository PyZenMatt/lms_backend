import { test, expect } from '@playwright/test';

/**
 * E2E Test: Complete Student Journey
 * Tests the full user flow from registration to course completion
 * Based on the StudentFlow integration tests but in a real browser environment
 */

test.describe('Student Complete Journey E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('student can complete full registration and course journey', async ({ page }) => {
    test.slow(); // Mark this as a slow test (gets 3x timeout)
    
    // Step 1: Navigate to registration
    await page.click('text=Registrati');
    await expect(page).toHaveURL(/.*signup/);
    
    // Step 2: Fill registration form
    const timestamp = Date.now();
    const testEmail = `student${timestamp}@test.com`;
    
    await page.fill('[name="firstName"]', 'Test');
    await page.fill('[name="lastName"]', 'Student');
    await page.fill('[name="email"]', testEmail);
    await page.fill('[name="password"]', 'TestPassword123!');
    await page.fill('[name="confirmPassword"]', 'TestPassword123!');
    
    // Select student role
    await page.selectOption('[name="role"]', 'student');
    
    // Submit registration
    await page.click('button[type="submit"]');
    
    // Step 3: Verify redirect to login or dashboard
    await expect(page).toHaveURL(/.*(?:signin|dashboard)/);
    
    // If redirected to login, log in
    if (page.url().includes('signin')) {
      await page.fill('[name="email"]', testEmail);
      await page.fill('[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
    }
    
    // Step 4: Verify student dashboard loads
    await expect(page).toHaveURL(/.*dashboard.*student/);
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Benvenuto')).toBeVisible();
    
    // Step 5: Navigate to courses
    await page.click('text=Corsi');
    await expect(page).toHaveURL(/.*corsi/);
    
    // Step 6: View course details
    await page.click('.course-card').first(); // Click first available course
    await expect(page.locator('text=Course Details')).toBeVisible();
    
    // Step 7: Test wallet integration
    await page.click('text=Wallet');
    await expect(page).toHaveURL(/.*rewards/);
    await expect(page.locator('text=Wallet')).toBeVisible();
    
    // Step 8: Test logout
    await page.click('[data-testid="logout-button"], .logout, text=Logout');
    await expect(page).toHaveURL(/.*signin/);
  });

  test('handles authentication errors gracefully', async ({ page }) => {
    // Navigate to login
    await page.goto('/auth/signin-1');
    
    // Try login with invalid credentials
    await page.fill('[name="email"]', 'invalid@test.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Should show error message and stay on login page
    await expect(page.locator('text=Invalid')).toBeVisible();
    await expect(page).toHaveURL(/.*signin/);
  });

  test('course enrollment flow works correctly', async ({ page }) => {
    // Login with test credentials
    await page.goto('/auth/signin-1');
    await page.fill('[name="email"]', 'student@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Navigate to courses
    await page.click('text=Corsi');
    
    // Select a course
    await page.click('.course-card').first();
    
    // Check if enrollment button exists
    const enrollButton = page.locator('text=Enroll, text=Iscriviti');
    if (await enrollButton.isVisible()) {
      await enrollButton.click();
      
      // Verify enrollment success
      await expect(page.locator('text=Enrolled, text=Iscritto')).toBeVisible();
    }
  });

  test('wallet operations and TeoCoin integration', async ({ page }) => {
    // Login as student
    await page.goto('/auth/signin-1');
    await page.fill('[name="email"]', 'student@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Navigate to wallet
    await page.click('text=Wallet');
    
    // Verify wallet components load
    await expect(page.locator('text=Balance')).toBeVisible();
    await expect(page.locator('text=TeoCoin')).toBeVisible();
    
    // Test reward system interface
    const rewardButton = page.locator('text=Claim Reward, text=Test Reward');
    if (await rewardButton.isVisible()) {
      await rewardButton.click();
      // Should show some feedback
      await expect(page.locator('text=Success, text=Claimed')).toBeVisible();
    }
  });

  test('responsive design works on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to app
    await page.goto('/');
    
    // Test mobile navigation
    const mobileMenu = page.locator('.mobile-menu, [data-testid="mobile-menu"]');
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click();
    }
    
    // Verify key elements are accessible on mobile
    await expect(page.locator('text=Dashboard, text=Corsi')).toBeVisible();
  });

  test('navigation and routing work correctly', async ({ page }) => {
    // Test direct URL navigation
    await page.goto('/dashboard/student');
    
    // Should redirect to login if not authenticated
    await expect(page).toHaveURL(/.*signin/);
    
    // Login
    await page.fill('[name="email"]', 'student@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Should now access dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Test navigation between pages
    const navLinks = ['Corsi', 'Wallet', 'Profilo'];
    for (const link of navLinks) {
      await page.click(`text=${link}`);
      await page.waitForLoadState('networkidle');
      // Verify page loads without errors
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
