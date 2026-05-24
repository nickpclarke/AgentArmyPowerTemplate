// @ts-check
import { expect, test } from '@playwright/test';

test.describe('middle-core scenario lab', () => {
  test('renders generated model, graph evidence, and clean failure path', async ({ page }) => {
    await page.goto('/model/demo');

    await expect(page.getByRole('heading', { name: 'Knowledge Drop Scenario Lab' })).toBeVisible();
    await expect(page.getByText('middle-core-runtime-prototype')).toBeVisible();
    await expect(page.locator('#objectCount')).toHaveText('9');
    await expect(page.locator('#stateMachineCount')).toHaveText('9');
    await expect(page.locator('#workflowStepCount')).toHaveText('4');

    await expect(page.locator('#scenarioStatus')).toHaveText('passed');
    await expect(page.locator('#evidenceStatus')).toHaveText('complete');
    await expect(page.locator('.node')).toHaveCount(6);
    await expect(page.locator('.edge')).toHaveCount(5);
    await expect(page.locator('#steps').getByText('validate-source-policy', { exact: true })).toBeVisible();
    await expect(page.locator('#steps').getByText('assemble-ingest-evidence', { exact: true })).toBeVisible();
    await expect(page.locator('#evidenceJson').getByText('evidence-knowledge-drop-001')).toBeVisible();

    await page.getByRole('button', { name: 'Run disabled-handler path' }).click();
    await expect(page.locator('#scenarioStatus')).toHaveText('failed');
    await expect(page.locator('#evidenceStatus')).toHaveText('none');
    await expect(page.locator('.node')).toHaveCount(4);
    await expect(page.locator('.edge')).toHaveCount(2);
    await expect(page.locator('#steps').getByText('has no enabled handler')).toBeVisible();

    await page.getByRole('button', { name: 'Run success path' }).click();
    await expect(page.locator('#scenarioStatus')).toHaveText('passed');
    await expect(page.locator('#evidenceStatus')).toHaveText('complete');
    await expect(page.locator('.node')).toHaveCount(6);
    await expect(page.locator('.edge')).toHaveCount(5);
  });
});
