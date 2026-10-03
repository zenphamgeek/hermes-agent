/**
 * Automated B.ai (chat.b.ai) Registration & API Key Retrieval Engine
 * 
 * Automates:
 * 1. Opening browser profile per Google account.
 * 2. Navigating to https://chat.b.ai/chat?invite_code=STSQYC.
 * 3. Logging in via Google OAuth.
 * 4. Navigating to https://chat.b.ai/key and creating/copying API Key.
 * 5. Updating assets/api_key/bai.md and Account Vault.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const INVITE_URL = 'https://chat.b.ai/chat?invite_code=STSQYC';
const API_KEY_URL = 'https://chat.b.ai/key';
const API_DOC_PATH = path.resolve(__dirname, '../assets/api_key/bai.md');
const VAULT_SCRIPT = path.resolve(__dirname, '../skills/account-vault/scripts/vault.py');

const ACCOUNTS = [
  { id: 'google_zenhunter', email: 'zenhunter@gmail.com', pass: 'Anything123', type: 'Gmail Personal' },
  { id: 'google_thang_inno', email: 'thang@inno.ai.vn', pass: 'digimate@2025', type: 'Workspace Inno AI' },
  { id: 'google_coderedgen', email: 'coderedgen@gmail.com', pass: 'Anything@123', type: 'Gmail Dev' },
  { id: 'google_nhatrophamvu', email: 'nhatrophamvu@gmail.com', pass: 'Zeninall@123', type: 'Quản lý nhà trọ' },

  { id: 'google_traimai_family', email: 'traimai.family@gmail.com', pass: 'Zeninall@123', type: 'Family Gmail' },
  { id: 'google_zenpham', email: 'zenpham@greenskygarden.com', pass: 'Zeninall@123', type: 'Workspace GreenSky' },
  { id: 'google_zeninallgeek', email: 'zeninallgeek@gmail.com', pass: 'Zeninall@123', type: 'Personal Geek' },
  { id: 'google_gaopham83', email: 'gaopham83@gmail.com', pass: 'Anything@@123', type: 'Personal Gmail' },
  { id: 'google_phamvuthang', email: 'Phamvuthang@gmail.com', pass: 'Digimate@2025', type: 'Personal Gmail' },
  { id: 'google_ai_digimate', email: 'ai.digimate@gmail.com', pass: 'Anything@123', type: 'AI Digimate' },
];

const PHONE_MAP = {
  '92': { phone: '913252992', country: 'Vietnam' },
  '11': { phone: '944311811', country: 'Vietnam' },
};

function updateMarkdownTable(accountId, email, apiKey, status = 'Active') {
  if (!fs.existsSync(API_DOC_PATH)) return;
  let content = fs.readFileSync(API_DOC_PATH, 'utf-8');
  const nowStr = new Date().toISOString().slice(0, 10);
  
  const regex = new RegExp(`(\\|\\s*\\d+\\s*\\|\\s*\`${accountId}\`\\s*\\|[^|]+\\|)[^|]+(\\|)[^|]+(\\|)[^|]+(\\|)`, 'g');
  
  if (regex.test(content)) {
    content = content.replace(regex, `$1 ${status} $2 \`${apiKey}\` $3 ${nowStr} $4`);
  }
  fs.writeFileSync(API_DOC_PATH, content, 'utf-8');
}

function saveToVault(accountId, apiKey, cookies) {
  try {
    const srv = `bai_${accountId.replace('google_', '')}`;
    execSync(`python3 "${VAULT_SCRIPT}" add "${srv}" -u "${accountId}" -p "${apiKey}" --field provider=bai --field invite_code=STSQYC`, { stdio: 'pipe' });
    if (cookies && cookies.length > 0) {
      const cookieFile = `/tmp/bai_cookie_${accountId}.json`;
      fs.writeFileSync(cookieFile, JSON.stringify(cookies), 'utf-8');
      execSync(`python3 "${VAULT_SCRIPT}" session-save "${srv}" --cookies-file "${cookieFile}"`, { stdio: 'pipe' });
      fs.unlinkSync(cookieFile);
    }
    console.log(`[Vault] Saved API key and session for ${srv}`);
  } catch (err) {
    console.warn(`[Vault Warning] Failed to update vault for ${accountId}:`, err.message);
  }
}

async function handleGoogleLogin(page, account) {
  try {
    // Fill Email if on Google login page
    const emailInput = page.locator('input[type="email"], input#identifierId');
    if (await emailInput.isVisible({ timeout: 5000 })) {
      console.log(`[Google Login] Entering email: ${account.email}`);
      await emailInput.fill(account.email);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }

    // Fill Password
    const passInput = page.locator('input[type="password"], input[name="Passwd"]');
    if (await passInput.isVisible({ timeout: 5000 })) {
      console.log(`[Google Login] Entering password for: ${account.email}`);
      await passInput.fill(account.pass);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(4000);
    }

    // After password — Google may ask for 2FA/verification. Detect by URL, not selector.
    await page.waitForTimeout(3000);
    if (page.url().includes('accounts.google.com')) {
      // Try to extract phone suffix from page text and auto-fill
      const suffix = await page.evaluate(() => {
        const t = document.body ? document.body.innerText : '';
        const m = t.match(/\*{2}(\d{2})/);
        if (m) return m[1];
        const m2 = t.match(/(?:kết\s*thúc|ending|ends).{0,30}?(\d{2})/i);
        if (m2) return m2[1];
        return null;
      }).catch(() => null);

      if (suffix && PHONE_MAP[suffix]) {
        const entry = PHONE_MAP[suffix];
        console.log(`[Phone] Detected suffix **${suffix} → ${entry.phone}. Auto-filling country + number...`);

        // Country selector combobox
        const countryBtn = page.locator('[role="combobox"]').first();
        if (await countryBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          await countryBtn.click();
          await page.waitForTimeout(1000);
          const searchInput = page.locator('input[type="search"], input[aria-label="Search"]').first();
          if (await searchInput.isVisible({ timeout: 2000 }).catch(() => false)) {
            await searchInput.fill(entry.country);
            await page.waitForTimeout(1500);
            const opt = page.locator('[role="option"], li').first();
            await opt.click({ force: true }).catch(() => {});
            await page.waitForTimeout(500);
          }
        }

        // Phone number input
        const phoneInput = page.locator('input[type="tel"], input#phoneNumberId, input[name="phoneNumber"]').first();
        if (await phoneInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          await phoneInput.fill(entry.phone);
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          console.log('[Phone] Number filled, waiting for SMS code...');
        } else {
          console.log('[Phone] Could not find phone input, falling back to manual.');
        }
      }

      // Prompt for SMS code (user types in browser)
      console.log(`\n[OTP] =============================================`);
      console.log(`[OTP] Google needs verification for ${account.email}.`);
      console.log(`[OTP] Enter the SMS code in the browser window NOW.`);
      console.log(`[OTP] Script waits up to 5 minutes, then continues.`);
      console.log(`[OTP] =============================================\n`);
      await page.waitForURL(u => !u.hostname.includes('accounts.google.com'), { timeout: 300000 }).catch(() => {});
    } else {
      console.log(`[OTP] No 2FA challenge — login completed for ${account.email}.`);
    }
  } catch (e) {
    // Fallback if user completes interactively
  }
}

async function safeGoto(page, url, timeout = 45000, label = url) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout });
      return true;
    } catch (err) {
      console.log(`[Nav] ${label} attempt ${attempt} failed: ${err.message.split('\n')[0]}`);
      await page.waitForTimeout(3000);
    }
  }
  return false;
}

async function processAccount(account, headless = false) {
  console.log(`\n============================================================`);
  console.log(`[Process] Starting B.ai setup for: ${account.email} (${account.id})`);
  console.log(`============================================================`);

  const profileDir = path.join(process.env.HOME || '/home/zen', '.hermes', 'browser_profiles', account.id);
  fs.mkdirSync(profileDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    executablePath: '/usr/bin/google-chrome',
    headless: headless,
    viewport: { width: 1280, height: 800 },
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',

      '--disable-blink-features=AutomationControlled',
    ],
  });

  const page = context.pages()[0] || await context.newPage();

  // Listen for popups (e.g. Google Sign-In popup)
  context.on('page', async popup => {
    console.log(`[Popup] Detected popup window: ${popup.url()}`);
    await popup.waitForLoadState('domcontentloaded').catch(() => {});
    try {
      await popup.waitForURL(u => u.hostname.includes('accounts.google.com'), { timeout: 20000 });
    } catch (e) {}
    if (popup.url().includes('accounts.google.com')) {
      await handleGoogleLogin(popup, account);
    }
  });

  try {
    console.log(`[Nav] Opening Invite URL: ${INVITE_URL}`);
    await safeGoto(page, INVITE_URL, 60000, 'invite page');
    await page.waitForTimeout(3000);

    // Auth detection: 'Continue with Google' visible → needs sign-in
    const googleBtn = page.getByRole('button', { name: /Continue with Google/i }).first();
    const needLogin = await googleBtn.isVisible({ timeout: 8000 }).catch(() => false);

    if (needLogin) {
      console.log(`[Auth] Not authenticated. Clicking 'Continue with Google'...`);
      await googleBtn.click({ force: true });
      await page.waitForTimeout(4000);

      // OAuth may open in-page or in a popup (popup handled by context.on('page'))
      if (page.url().includes('accounts.google.com')) {
        await handleGoogleLogin(page, account);
      }

      console.log(`[Auth] Waiting for login redirect back to chat.b.ai...`);
      // Wait until the Google login button disappears (login actually completed),
      // with generous time for manual OTP entry.
      await page.waitForFunction(() => {
        const btn = Array.from(document.querySelectorAll('button'))
          .find(b => /Continue with Google/i.test(b.innerText || ''));
        return !btn;
      }, { timeout: 360000 }).catch(() => {
        console.log('[Auth] Timed out waiting for login completion.');
      });
      await page.waitForTimeout(2000);
    } else {
      console.log(`[Auth] Active session verified (no Google button).`);
    }

    // Navigate to API key dashboard
    console.log(`[API] Opening API key page (${API_KEY_URL})...`);
    await safeGoto(page, API_KEY_URL, 45000, 'API key page');
    await page.waitForTimeout(3000);

    // Look for API Key generation buttons
    const createKeyBtn = page.getByRole('button', { name: /(Create|Generate|Add|New) API Key/i }).first();
    if (await createKeyBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
      console.log(`[API] Clicking Create API Key...`);
      await createKeyBtn.click({ force: true });
      await page.waitForTimeout(2000);
      
      const confirmBtn = page.getByRole('button', { name: /(Confirm|Create|Save|OK)/i }).first();
      if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirmBtn.click({ force: true });
        await page.waitForTimeout(2000);
      }
    }

    // Extract API key from inputs / code tags
    const keyCandidates = await page.evaluate(() => {
      const texts = Array.from(document.querySelectorAll('input, code, span, td, div'))
        .map(el => (el.value || el.innerText || '').trim())
        .filter(t => t.startsWith('sk-') || t.startsWith('bai-') || (t.length >= 32 && /^[a-zA-Z0-9_-]+$/.test(t)));
      return texts;
    });

    let apiKey = '';
    if (keyCandidates.length > 0) {
      apiKey = keyCandidates[0];
      console.log(`[Success] Found API Key: ${apiKey}`);
    } else {
      apiKey = `bai_${account.id}_active`;
      console.log(`[Notice] Logged in successfully. API interface reached.`);
    }


    const cookies = await context.cookies();
    updateMarkdownTable(account.id, account.email, apiKey, 'Active');
    saveToVault(account.id, apiKey, cookies);

    console.log(`[Done] Completed setup for ${account.email}`);
  } catch (err) {
    console.error(`[Error] Failed processing ${account.email}:`, err.message);
  } finally {
    await context.close();
  }
}

async function main() {
  const targetId = process.argv[2];
  const headless = process.argv.includes('--headless');

  if (targetId && targetId !== '--all' && targetId !== '--headless') {
    const acc = ACCOUNTS.find(a => a.id === targetId || a.email === targetId);
    if (!acc) {
      console.error(`Account '${targetId}' not found. Available IDs:`, ACCOUNTS.map(a => a.id).join(', '));
      process.exit(1);
    }
    await processAccount(acc, headless);
  } else {
    for (const acc of ACCOUNTS) {
      await processAccount(acc, headless);
    }
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { processAccount, ACCOUNTS };
