import {test,expect} from '@playwright/test';
test('operator opens investigation and follows evidence to verification',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Mission Control'})).toBeVisible();
  await page.locator('.ww-engagement-card').filter({hasText:'Local Web Application Assessment'}).click();
  await expect(page.getByRole('heading',{name:'Local Web Application Assessment'})).toBeVisible();
  await page.getByRole('tab',{name:'Investigation'}).click();
  await page.getByRole('button',{name:/Evaluate reflected markup/}).click();
  await expect(page.getByText('GET /search?q=%3Cb%3EWW_MARKER%3C%2Fb%3E').first()).toBeVisible();
  await page.getByRole('tab',{name:'Reasoning Frontier'}).click();
  await expect(page.getByText('Unencoded reflected HTML in /search').first()).toBeVisible();
  await page.getByRole('tab',{name:'Verification'}).click();
  await expect(page.getByText('Verification pending').first()).toBeVisible();
});
test('new engagement saves a draft but does not launch a real assessment',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:/New Engagement/}).first().click();
  await expect(page.getByRole('heading',{name:'Develop a mission'})).toBeVisible();
  await page.getByRole('button',{name:/Continue/}).click();
  await page.getByRole('button',{name:/Continue/}).click();
  await page.getByRole('button',{name:/Continue/}).click();
  await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:/Save concept briefing/}).click();
  await expect(page.getByRole('heading',{name:'New local application review'})).toBeVisible();
  await expect(page.getByText('Draft (not launched)')).toBeVisible();
});

test('recorded run workspace shows real recorded provenance and historical replay',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Recorded Run Evidence'}).click();
  await expect(page.getByRole('heading',{name:'Recorded Run Workspace'})).toBeVisible();
  await expect(page.getByText('Recorded execution history')).toBeVisible();
  await expect(page.getByText('Rejected supplied negative control')).toBeVisible();
  await page.getByRole('button',{name:'Replay recorded events'}).click();
  await expect(page.getByText('Historical replay complete')).toBeVisible();
});

test('live event workspace shows an honest empty recorded ledger without demo findings',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Live Engagement Events'}).click();
  await expect(page.getByRole('heading',{name:'Live Engagement Events'})).toBeVisible();
  await expect(page.getByText('No persisted engagements')).toBeVisible();
  await expect(page.getByText('This workspace reads stored local-agent events.',{exact:false})).toBeVisible();
  await expect(page.getByText('Potential reflected HTML output encoding weakness')).toHaveCount(0);
});
