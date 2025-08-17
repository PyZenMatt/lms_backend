import { test, expect } from '@playwright/test';

/**
 * E2E Test: Teacher Journey
 * Tests teacher-specific workflows like course creation and management
 */

test.describe('Teacher Journey E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login as teacher
    await page.goto('/auth/signin-1');
    await page.fill('[name="email"]', 'teacher@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Verify teacher dashboard loads
    await expect(page).toHaveURL(/.*dashboard.*teacher/);
  });

  test('teacher can access dashboard and view statistics', async ({ page }) => {
    // Verify teacher dashboard elements
    await expect(page.locator('text=Teacher Dashboard')).toBeVisible();
    await expect(page.locator('text=Statistiche, text=Statistics')).toBeVisible();
    
    // Check for course management elements
    await expect(page.locator('text=I Miei Corsi, text=My Courses')).toBeVisible();
  });

  test('teacher can create new course', async ({ page }) => {
    // Navigate to course creation
    await page.click('text=Crea Corso, text=Create Course, text=Nuovo Corso');
    
    // Fill course creation form
    await page.fill('[name="title"]', 'Test Course E2E');
    await page.fill('[name="description"]', 'This is a test course created during E2E testing');
    await page.selectOption('[name="category"]', 'programming');
    await page.fill('[name="price"]', '50');
    
    // Submit course creation
    await page.click('button[type="submit"]');
    
    // Verify course was created
    await expect(page.locator('text=Test Course E2E')).toBeVisible();
  });

  test('teacher can manage existing courses', async ({ page }) => {
    // Navigate to course management
    await page.click('text=Gestisci Corsi, text=Manage Courses');
    
    // Select first course for editing
    await page.click('.course-item .edit-button, [data-testid="edit-course"]').first();
    
    // Verify edit form loads
    await expect(page.locator('text=Modifica Corso, text=Edit Course')).toBeVisible();
    
    // Make a change
    await page.fill('[name="title"]', 'Updated Course Title');
    await page.click('button[type="submit"]');
    
    // Verify update success
    await expect(page.locator('text=Updated Course Title')).toBeVisible();
  });

  test('teacher can view student enrollments and progress', async ({ page }) => {
    // Navigate to students section
    await page.click('text=Studenti, text=Students');
    
    // Verify student list loads
    await expect(page.locator('.student-list, [data-testid="student-list"]')).toBeVisible();
    
    // Click on a student to view details
    await page.click('.student-item, [data-testid="student-item"]').first();
    
    // Verify student details and progress
    await expect(page.locator('text=Progresso, text=Progress')).toBeVisible();
  });

  test('teacher can access blockchain features and rewards', async ({ page }) => {
    // Navigate to blockchain/rewards section
    await page.click('text=Rewards, text=Blockchain');
    
    // Verify teacher can see reward management
    await expect(page.locator('text=Gestisci Reward, text=Manage Rewards')).toBeVisible();
    
    // Test reward creation/management
    const createRewardButton = page.locator('text=Crea Reward, text=Create Reward');
    if (await createRewardButton.isVisible()) {
      await createRewardButton.click();
      await expect(page.locator('text=Nuovo Reward, text=New Reward')).toBeVisible();
    }
  });
});
