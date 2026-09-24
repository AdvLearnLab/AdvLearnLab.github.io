import { mkdir, writeFile } from 'node:fs/promises';

const repo = process.env.GITHUB_REPOSITORY;
const token = process.env.GITHUB_TOKEN;
if (!repo || !token) throw new Error('GitHub repository credentials are unavailable.');

const response = await fetch(`https://api.github.com/repos/${repo}/issues?state=all&per_page=100&sort=updated&direction=desc`, {
  headers: {
    Accept: 'application/vnd.github+json',
    Authorization: `Bearer ${token}`,
    'User-Agent': 'admissions-registry-builder',
    'X-GitHub-Api-Version': '2022-11-28'
  }
});
if (!response.ok) throw new Error(`GitHub API returned ${response.status}.`);

const clean = (value) => String(value || '').replace(/[\r\n|]/g, ' ').trim();
const bodyValue = (body, key) => clean(body.match(new RegExp(`^${key}：\\s*(.+)$`, 'm'))?.[1]);
const issues = await response.json();
const entries = issues.flatMap((issue) => {
  if (!issue.body?.includes('<!-- admissions-registry -->') || issue.pull_request) return [];
  const item = {
    candidateName: bodyValue(issue.body, '考生姓名'),
    candidateUnit: bodyValue(issue.body, '考生单位'),
    supervisorName: bodyValue(issue.body, '导师姓名'),
    supervisorUnit: bodyValue(issue.body, '导师单位'),
    status: bodyValue(issue.body, '当前状态'),
    updated: issue.updated_at,
    url: issue.html_url,
    number: issue.number
  };
  return [item.candidateName, item.candidateUnit, item.supervisorName, item.supervisorUnit, item.status].every(Boolean) ? [item] : [];
});

await mkdir('assets/data', { recursive: true });
await writeFile('assets/data/admissions-registry.json', `${JSON.stringify(entries, null, 2)}\n`, 'utf8');
console.log(`Wrote ${entries.length} admissions registry entries.`);
