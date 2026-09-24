---
layout: homepage
title: 研究生招生互助登记
permalink: /admissions-registry.html
---

<div class="registry-page">
  <header class="registry-hero">
    <span class="registry-kicker">Graduate Admissions Registry</span>
    <h1>研究生招生互助登记</h1>
    <p>面向招生与推免沟通的公开信息板。仅登记必要信息，帮助考生与导师及时同步接收状态。</p>
  </header>

  <div class="registry-layout">
    <section class="registry-panel">
      <h2>提交登记</h2>
      <p class="registry-note">提交后将跳转至 GitHub 创建一条公开记录。需要登录 GitHub，提交前可以再次核对内容。</p>
      <form id="registry-form" class="registry-form-grid">
        <div class="registry-field"><label for="candidate-name">考生姓名</label><input id="candidate-name" maxlength="30" required autocomplete="name"></div>
        <div class="registry-field"><label for="candidate-unit">考生单位</label><input id="candidate-unit" maxlength="80" required></div>
        <div class="registry-field"><label for="supervisor-name">导师姓名</label><input id="supervisor-name" maxlength="30" required></div>
        <div class="registry-field"><label for="supervisor-unit">导师单位</label><input id="supervisor-unit" maxlength="80" required></div>
        <div class="registry-field registry-span-2">
          <label for="registry-status">当前状态</label>
          <select id="registry-status" required>
            <option>沟通中</option><option>导师已同意接收</option><option>正式确认接收</option><option>双方已取消</option><option>失联待核实</option>
          </select>
        </div>
        <label class="registry-consent registry-span-2"><input id="registry-consent" type="checkbox" required><span>我确认上述信息真实，并已获得公开姓名、单位及沟通状态所需的授权；如状态变化，我会及时更新或申请删除。</span></label>
        <button class="registry-submit registry-span-2" type="submit">前往 GitHub 确认提交</button>
      </form>
      <div class="registry-guidelines"><strong>登记原则</strong><br>“失联待核实”只表示暂时无法取得联系，不代表对任何一方作出评价。禁止填写联系方式、身份证号、成绩等额外个人信息；存在争议时，以双方补充确认或删除记录为准。</div>
    </section>

    <section class="registry-panel">
      <h2>公开登记</h2>
      <p class="registry-note">数据来自公开 GitHub 记录，提交或修改后通常会在数分钟内同步。可按姓名或单位搜索，并按当前状态筛选。</p>
      <div class="registry-toolbar">
        <div class="registry-search"><input id="registry-query" type="search" placeholder="搜索姓名或单位"><select id="registry-filter" aria-label="按状态筛选"><option value="">全部状态</option><option>沟通中</option><option>导师已同意接收</option><option>正式确认接收</option><option>双方已取消</option><option>失联待核实</option></select></div>
        <button id="registry-refresh" class="registry-refresh" type="button" title="刷新公开登记">刷新</button>
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
    candidateName: document.querySelector('#candidate-name'), candidateUnit: document.querySelector('#candidate-unit'),
    supervisorName: document.querySelector('#supervisor-name'), supervisorUnit: document.querySelector('#supervisor-unit'),
    status: document.querySelector('#registry-status')
  };
  const list = document.querySelector('#registry-list');
  const query = document.querySelector('#registry-query');
  const filter = document.querySelector('#registry-filter');
  let entries = [];
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
      status: bodyValue(issue.body, '当前状态'), updated: issue.updated_at, url: issue.html_url, number: issue.number
    };
    return [item.candidateName, item.candidateUnit, item.supervisorName, item.supervisorUnit, item.status].every(Boolean) ? item : null;
  }

  function statusClass(status) {
    return { '沟通中': 'status-contact', '导师已同意接收': 'status-agreed', '正式确认接收': 'status-confirmed', '双方已取消': 'status-cancelled', '失联待核实': 'status-unverified' }[status] || 'status-contact';
  }

  function render() {
    const keyword = clean(query.value).toLowerCase();
    const status = filter.value;
    const visible = entries.filter((item) => {
      const haystack = `${item.candidateName} ${item.candidateUnit} ${item.supervisorName} ${item.supervisorUnit}`.toLowerCase();
      return (!keyword || haystack.includes(keyword)) && (!status || item.status === status);
    });
    if (!visible.length) { list.innerHTML = '<div class="registry-empty">暂无符合条件的公开登记。</div>'; return; }
    list.innerHTML = visible.map((item) => `
      <article class="registry-entry">
        <div class="registry-entry-head"><span class="registry-status ${statusClass(item.status)}">${escapeHtml(item.status)}</span><span>#${item.number}</span></div>
        <div class="registry-person"><div><strong>${escapeHtml(item.candidateName)}</strong><span>${escapeHtml(item.candidateUnit)}</span></div><span class="registry-person-arrow">→</span><div><strong>${escapeHtml(item.supervisorName)}</strong><span>${escapeHtml(item.supervisorUnit)}</span></div></div>
        <div class="registry-entry-foot"><span>更新于 ${new Date(item.updated).toLocaleDateString('zh-CN')}</span><a href="${item.url}" target="_blank" rel="noopener">查看 / 补充 / 纠错</a></div>
      </article>`).join('');
  }

  async function loadEntries() {
    list.innerHTML = '<div class="registry-loading">正在读取公开登记...</div>';
    try {
      const dataUrl = 'https://advlearnlab.github.io/assets/data/admissions-registry.json';
      const response = await fetch(`${dataUrl}?v=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Registry data ${response.status}`);
      entries = await response.json();
      render();
    } catch (error) {
      list.innerHTML = '<div class="registry-empty">公开登记暂时读取失败，请稍后刷新。</div>';
      console.error(error);
    }
  }

  document.querySelector('#registry-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const values = Object.fromEntries(Object.entries(fields).map(([key, input]) => [key, clean(input.value)]));
    const title = `[招生登记] ${values.candidateName} / ${values.supervisorName} / ${values.status}`;
    const body = `${MARKER}\n考生姓名：${values.candidateName}\n考生单位：${values.candidateUnit}\n导师姓名：${values.supervisorName}\n导师单位：${values.supervisorUnit}\n当前状态：${values.status}\n\n> 本人确认信息真实并同意按页面登记原则公开。状态变化后请编辑本记录或留言申请更正。`;
    window.open(`https://github.com/${REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`, '_blank', 'noopener');
  });
  query.addEventListener('input', render);
  filter.addEventListener('change', render);
  document.querySelector('#registry-refresh').addEventListener('click', loadEntries);
  loadEntries();
})();
</script>
