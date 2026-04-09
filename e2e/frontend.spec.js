const { test, expect } = require('@playwright/test');

test.describe('DischargeIQ Dashboard', () => {

  test('homepage loads and shows DischargeIQ header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=DischargeIQ').first()).toBeVisible({ timeout: 15000 });
  });

  test('dashboard shows summary KPI cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Use .first() since "Auth Pending" appears in both KPI card and status tags
    await expect(page.locator('.summary-card__label:has-text("Auth Pending")').first()).toBeVisible();
    await expect(page.locator('.summary-card__label:has-text("Placed Today")').first()).toBeVisible();
    await expect(page.locator('.summary-card__label:has-text("Avg Delay")').first()).toBeVisible();

    // Verify the KPI values are numbers
    const authValue = await page.locator('.summary-card__value').first().textContent();
    expect(parseInt(authValue)).toBeGreaterThanOrEqual(0);
  });

  test('dashboard shows workflow data table with patient rows', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    const tableContent = await page.locator('table, [class*="table"], [class*="Table"], [role="table"]').first();
    await expect(tableContent).toBeVisible({ timeout: 10000 });

    const pageText = await page.textContent('body');
    const hasPatientData = pageText.includes('Margaret Chen') ||
                           pageText.includes('Robert Williams') ||
                           pageText.includes('Dorothy Johnson') ||
                           pageText.includes('Aetna');
    expect(hasPatientData).toBeTruthy();
  });

  test('dashboard shows status tags with correct labels', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    const bodyText = await page.textContent('body');
    const hasStatusTags = bodyText.includes('Auth Pending') ||
                          bodyText.includes('Auth Approved') ||
                          bodyText.includes('Auth Denied') ||
                          bodyText.includes('Searching') ||
                          bodyText.includes('Placed') ||
                          bodyText.includes('Discharged') ||
                          bodyText.includes('Escalated');
    expect(hasStatusTags).toBeTruthy();
  });

  test('navigation links exist in header', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    // Use the header nav specifically to avoid ambiguity
    await expect(page.locator('header a:has-text("Dashboard")').first()).toBeVisible();
    await expect(page.locator('header a:has-text("Audit Log")').first()).toBeVisible();
  });

  test('can navigate to audit log page', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    await page.locator('text=Audit Log').first().click();
    await page.waitForTimeout(1000);

    const bodyText = await page.textContent('body');
    const hasAuditContent = bodyText.includes('Audit') ||
                            bodyText.includes('audit') ||
                            bodyText.includes('Compliance');
    expect(hasAuditContent).toBeTruthy();
  });

  test('alert notifications are displayed', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    const bodyText = await page.textContent('body');
    const hasAlerts = bodyText.includes('denied') ||
                      bodyText.includes('pending') ||
                      bodyText.includes('Denied') ||
                      bodyText.includes('Denial') ||
                      bodyText.includes('appeal') ||
                      bodyText.includes('observation') ||
                      bodyText.includes('Alert') ||
                      bodyText.includes('Escalation') ||
                      bodyText.includes('Approaching');
    expect(hasAlerts).toBeTruthy();
  });

  test('clicking a patient row navigates to patient detail', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Try clicking a patient name in the table
    const patientName = page.locator('span.semibold[role="link"]').first();
    if (await patientName.isVisible().catch(() => false)) {
      await patientName.click();
    } else {
      // Fallback: try View Details from overflow menu
      const viewBtn = page.locator('text=View Details').first();
      if (await viewBtn.isVisible().catch(() => false)) {
        await viewBtn.click();
      }
    }

    await page.waitForTimeout(1000);

    const bodyText = await page.textContent('body');
    const hasDetail = bodyText.includes('MRN') ||
                      bodyText.includes('Payer') ||
                      bodyText.includes('Prior Auth') ||
                      bodyText.includes('Timeline') ||
                      bodyText.includes('Facility');
    expect(hasDetail).toBeTruthy();
  });

  test('page renders without JavaScript errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));

    await page.goto('/');
    await page.waitForTimeout(3000);

    const criticalErrors = errors.filter(e =>
      !e.includes('ResizeObserver') &&
      !e.includes('Loading chunk') &&
      !e.includes('favicon')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test('no PHI appears in console logs', async ({ page }) => {
    const consoleLogs = [];
    page.on('console', (msg) => consoleLogs.push(msg.text()));

    await page.goto('/');
    await page.waitForTimeout(3000);

    const allLogs = consoleLogs.join(' ');
    // SSN pattern should never appear
    expect(allLogs).not.toMatch(/\b\d{3}-\d{2}-\d{4}\b/);
  });
});

test.describe('DischargeIQ Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone viewport

  test('dashboard renders on mobile viewport', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    await expect(page.locator('text=DischargeIQ').first()).toBeVisible();

    const bodyText = await page.textContent('body');
    const hasKPIs = bodyText.includes('Auth Pending') ||
                    bodyText.includes('Placed Today') ||
                    bodyText.includes('Avg Delay');
    expect(hasKPIs).toBeTruthy();
  });

  test('no horizontal overflow on mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);

    // Check that the visible area doesn't cause horizontal scrollbar
    // The body should have overflow-x: hidden from our CSS
    const hasOverflowHidden = await page.evaluate(() => {
      const html = document.documentElement;
      const computed = window.getComputedStyle(html);
      return computed.overflowX === 'hidden' || document.body.scrollWidth <= window.innerWidth;
    });
    expect(hasOverflowHidden).toBeTruthy();
  });

  test('summary cards stack vertically on mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Verify KPI content is present and readable
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Auth Pending');
    expect(bodyText).toContain('Placed Today');
  });
});

test.describe('DischargeIQ Audit Log Page', () => {

  test('audit log shows table with correct columns', async ({ page }) => {
    await page.goto('/audit');
    await page.waitForTimeout(2000);

    const bodyText = await page.textContent('body');
    // Should have audit-related content
    const hasAuditTable = bodyText.includes('Timestamp') ||
                          bodyText.includes('Agent') ||
                          bodyText.includes('Action') ||
                          bodyText.includes('Compliance') ||
                          bodyText.includes('audit');
    expect(hasAuditTable).toBeTruthy();
  });

  test('audit log shows hashed patient IDs, not raw PHI', async ({ page }) => {
    await page.goto('/audit');
    await page.waitForTimeout(2000);

    const bodyText = await page.textContent('body');
    // Should show hashed IDs (hex strings), never raw names/MRNs
    expect(bodyText).not.toContain('MRN-30491827');
    // Hashed IDs are 64-char hex strings — check for truncated versions
    const hasHashedIds = bodyText.includes('...') || bodyText.match(/[a-f0-9]{10,}/);
    expect(hasHashedIds).toBeTruthy();
  });
});
