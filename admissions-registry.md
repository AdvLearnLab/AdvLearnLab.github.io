---
layout: homepage
title: 研究生招生互助登记
permalink: /admissions-registry.html
---

<div class="registry-page">
  <header class="registry-hero">
    <span class="registry-kicker">Graduate Admissions Registry</span>
    <h1>研究生招生互助登记</h1>
    <p>任何考生或导师均可登记，无需仓库权限。仅登记必要信息，帮助招生与推免双方及时同步接收状态。</p>
    <a class="registry-account-link" href="{{ '/my-admissions.html' | relative_url }}">我的登记</a>
  </header>

  <div class="registry-layout">
    <section class="registry-panel">
      <h2>提交登记</h2>
      <p class="registry-note">任何人均可提交，无需联系管理员。提交时只需登录或免费注册 GitHub 账号，用于确认提交者身份并方便本人后续修改或下架记录。</p>
      <form id="registry-form" class="registry-form-grid">
        <fieldset class="registry-person-fields registry-span-2">
          <legend>考生信息</legend>
          <div class="registry-field"><label for="candidate-name">考生姓名</label><input id="candidate-name" maxlength="30" required autocomplete="name"></div>
          <div class="registry-field"><label for="candidate-school">考生学校</label><input id="candidate-school" maxlength="60" placeholder="例如：安徽大学" required></div>
          <div class="registry-field"><label for="candidate-program">考生学院 / 专业</label><input id="candidate-program" maxlength="80" placeholder="例如：计算机科学与技术学院 / 计算机科学与技术" required></div>
          <div class="registry-field"><label for="candidate-status">考生状态</label><select id="candidate-status" required><option>沟通中</option><option>接受意向</option><option>已确认</option><option>已放弃</option><option>暂时失联</option></select></div>
        </fieldset>
        <fieldset class="registry-person-fields registry-span-2">
          <legend>导师信息</legend>
          <div class="registry-field"><label for="supervisor-name">导师姓名</label><input id="supervisor-name" maxlength="30" required></div>
          <div class="registry-field"><label for="supervisor-school">导师学校</label><input id="supervisor-school" maxlength="60" placeholder="例如：安徽大学" required></div>
          <div class="registry-field"><label for="supervisor-program">导师学院 / 专业</label><input id="supervisor-program" maxlength="80" placeholder="例如：计算机科学与技术学院 / 计算机科学与技术" required></div>
          <div class="registry-field"><label for="supervisor-status">导师状态</label><select id="supervisor-status" required><option>沟通中</option><option>同意接收</option><option>正式确认</option><option>拒绝接收</option><option>暂时失联</option></select></div>
        </fieldset>
        <div class="registry-field registry-span-2"><label for="application-year">申请年份</label><select id="application-year" required><option>2026</option><option>2027</option><option>2028</option><option>2029</option><option>2030</option></select></div>
        <label class="registry-consent registry-span-2"><input id="registry-consent" type="checkbox" required><span>我确认上述信息真实，并已获得公开姓名、单位及沟通状态所需的授权；如状态变化，我会及时更新或申请删除。</span></label>
        <button class="registry-submit registry-span-2" type="submit">任何人均可登记 · 确认提交</button>
      </form>
      <div class="registry-guidelines"><strong>登记原则</strong><br>登记将长期保留，提交者不能删除或通过关闭记录将其下架，但可以编辑本人和导师的状态。“暂时失联”只表示当前无法取得联系，不代表对任何一方作出评价。</div>
    </section>

    <section class="registry-panel">
      <h2>公开登记</h2>
      <p class="registry-note">数据来自公开 GitHub 记录，提交或修改后通常会在数分钟内同步。可按姓名或单位搜索，并按当前状态筛选。</p>
      <div class="registry-toolbar">
        <div class="registry-search"><input id="registry-query" type="search" placeholder="搜索姓名、学校、学院或专业"><select id="registry-year-filter" aria-label="按申请年份筛选"><option value="">全部年份</option><option>2026</option><option>2027</option><option>2028</option><option>2029</option><option>2030</option></select><select id="registry-filter" aria-label="按状态筛选"><option value="">全部状态</option><option>沟通中</option><option>接受意向</option><option>同意接收</option><option>已确认</option><option>正式确认</option><option>已放弃</option><option>拒绝接收</option><option>暂时失联</option></select></div>
        <button id="registry-search-button" class="registry-refresh" type="button">搜索</button>
      </div>
      <div id="registry-list" class="registry-list" aria-live="polite"><div class="registry-loading">正在读取公开登记...</div></div>
    </section>
  </div>
</div>

<script>
(() => {
  const REPO = 'AdvLearnLab/AdvLearnLab.github.io';
  const MARKER = '<!-- admissions-registry -->';
  const fields = {
    candidateName: document.querySelector('#candidate-name'), candidateSchool: document.querySelector('#candidate-school'),
    candidateProgram: document.querySelector('#candidate-program'), candidateStatus: document.querySelector('#candidate-status'),
    supervisorName: document.querySelector('#supervisor-name'), supervisorSchool: document.querySelector('#supervisor-school'),
    supervisorProgram: document.querySelector('#supervisor-program'), supervisorStatus: document.querySelector('#supervisor-status'),
    applicationYear: document.querySelector('#application-year')
  };
  const list = document.querySelector('#registry-list');
  const query = document.querySelector('#registry-query');
  const yearFilter = document.querySelector('#registry-year-filter');
  const filter = document.querySelector('#registry-filter');
  let entries = [];
  let autoChecks = 0;
  let searchRequested = false;
  const clean = (value) => String(value || '').replace(/[\r\n|]/g, ' ').trim();
  const escapeHtml = (value) => clean(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

  function bodyValue(body, key) {
    const match = body.match(new RegExp(`^${key}：\\s*(.+)$`, 'm'));
    return match ? clean(match[1]) : '';
  }

  function parseIssue(issue) {
    if (!issue.body || !issue.body.includes(MARKER) || issue.pull_request) return null;
    const item = {
      candidateName: bodyValue(issue.body, '考生姓名'), candidateUnit: bodyValue(issue.body, '考生单位'),
      supervisorName: bodyValue(issue.body, '导师姓名'), supervisorUnit: bodyValue(issue.body, '导师单位'),
      applicationYear: bodyValue(issue.body, '申请年份'), status: bodyValue(issue.body, '当前状态'), updated: issue.updated_at, url: issue.html_url, number: issue.number
    };
    return [item.candidateName, item.candidateUnit, item.supervisorName, item.supervisorUnit, item.status].every(Boolean) ? item : null;
  }

  function statusClass(status) {
    return { '沟通中': 'status-contact', '导师已同意接收': 'status-agreed', '正式确认接收': 'status-confirmed', '双方已取消': 'status-cancelled', '失联待核实': 'status-unverified' }[status] || 'status-contact';
  }

  function render() {
    const keyword = clean(query.value).toLowerCase();
    const year = yearFilter.value;
    const status = filter.value;
    if (!searchRequested || (!keyword && !year && !status)) {
      list.innerHTML = '<div class="registry-empty">填写姓名、学校、学院、专业、年份或状态，然后点击“搜索”。</div>';
      return;
    }
    const visible = entries.filter((item) => {
      const haystack = `${item.candidateName} ${item.candidateSchool} ${item.candidateProgram} ${item.supervisorName} ${item.supervisorSchool} ${item.supervisorProgram}`.toLowerCase();
      const statusMatch = !status || item.candidateStatus === status || item.supervisorStatus === status;
      return (!keyword || haystack.includes(keyword)) && (!year || item.applicationYear === year) && statusMatch;
    });
    if (!visible.length) { list.innerHTML = '<div class="registry-empty">暂无符合条件的公开登记。</div>'; return; }
    list.innerHTML = visible.map((item) => `
      <article class="registry-entry">
        <div class="registry-entry-head"><span class="registry-year">${escapeHtml(item.applicationYear)} 年</span><span>#${item.number}</span></div>
        <div class="registry-person"><div><strong>${escapeHtml(item.candidateName)}</strong><span>${escapeHtml(item.candidateSchool)} · ${escapeHtml(item.candidateProgram)}</span><em>考生：${escapeHtml(item.candidateStatus)}</em></div><span class="registry-person-arrow">→</span><div><strong>${escapeHtml(item.supervisorName)}</strong><span>${escapeHtml(item.supervisorSchool)} · ${escapeHtml(item.supervisorProgram)}</span><em>导师：${escapeHtml(item.supervisorStatus)}</em></div></div>
        <div class="registry-entry-foot"><span>更新于 ${new Date(item.updated).toLocaleDateString('zh-CN')}</span><a href="${item.url}" target="_blank" rel="noopener">查看 / 补充 / 纠错</a></div>
      </article>`).join('');
  }

  async function loadEntries() {
    list.innerHTML = '<div class="registry-loading">正在读取公开登记...</div>';
    try {
      const dataUrl = 'https://advlearnlab.github.io/assets/data/admissions-registry.json';
      const response = await fetch(dataUrl, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`Registry data ${response.status}`);
      entries = await response.json();
      render();
      if (!entries.length && autoChecks < 3) {
        autoChecks += 1;
        window.setTimeout(loadEntries, 20000);
      }
    } catch (error) {
      list.innerHTML = '<div class="registry-empty">公开登记暂时读取失败，请稍后刷新。</div>';
      console.error(error);
    }
  }

  document.querySelector('#registry-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const values = Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, clean(input.value)]));
    const title = `[招生登记] ${values.applicationYear} / ${values.candidateName} / ${values.supervisorName}`;
    const body = `${MARKER}\n考生姓名：${values.candidateName}\n考生学校：${values.candidateSchool}\n考生学院/专业：${values.candidateProgram}\n考生状态：${values.candidateStatus}\n导师姓名：${values.supervisorName}\n导师学校：${values.supervisorSchool}\n导师学院/专业：${values.supervisorProgram}\n导师状态：${values.supervisorStatus}\n申请年份：${values.applicationYear}\n\n> 本人确认信息真实并同意按页面登记原则公开。登记将长期保留，不接受提交者删除；双方状态及基本信息可以通过编辑本记录进行更新。`;
    window.open(`https://github.com/${REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`, '_blank', 'noopener');
  });
  document.querySelector('#registry-search-button').addEventListener('click', () => {
    searchRequested = true;
    render();
  });
  query.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    searchRequested = true;
    render();
  });
  loadEntries();
})();
</script>
