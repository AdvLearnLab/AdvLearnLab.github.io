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
  const legacyCandidateUnit = bodyValue(issue.body, '考生单位');
  const legacySupervisorUnit = bodyValue(issue.body, '导师单位');
  const legacyStatus = bodyValue(issue.body, '当前状态');
  const item = {
    candidateName: bodyValue(issue.body, '考生姓名'),
    candidateSchool: bodyValue(issue.body, '考生学校') || legacyCandidateUnit,
    candidateProgram: bodyValue(issue.body, '考生学院/专业') || '未填写',
    candidateStatus: bodyValue(issue.body, '考生状态') || '未填写',
    supervisorName: bodyValue(issue.body, '导师姓名'),
    supervisorSchool: bodyValue(issue.body, '导师学校') || legacySupervisorUnit,
    supervisorProgram: bodyValue(issue.body, '导师学院/专业') || '未填写',
    supervisorStatus: bodyValue(issue.body, '导师状态') || legacyStatus || '未填写',
    applicationYear: bodyValue(issue.body, '申请年份'),
    updated: issue.updated_at,
    url: issue.html_url,
    number: issue.number
  };
  return [item.candidateName, item.candidateSchool, item.candidateProgram, item.candidateStatus, item.supervisorName, item.supervisorSchool, item.supervisorProgram, item.supervisorStatus, item.applicationYear].every(Boolean) ? [item] : [];
});

await mkdir('assets/data', { recursive: true });
await writeFile('assets/data/admissions-registry.json', `${JSON.stringify(entries, null, 2)}\n`, 'utf8');
console.log(`Wrote ${entries.length} admissions registry entries.`);
