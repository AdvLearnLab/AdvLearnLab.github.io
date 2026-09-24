---
layout: homepage
title: 我的招生登记
permalink: /my-admissions.html
---

<div class="registry-page">
  <header class="registry-hero">
    <span class="registry-kicker">My Admissions Records</span>
    <h1>我的招生登记</h1>
    <p>使用 GitHub 账号管理自己提交的登记，不在本站保存账号或密码。</p>
    <a class="registry-account-link" href="{{ '/admissions-registry.html' | relative_url }}">返回登记大厅</a>
  </header>

  <div class="registry-account-grid">
    <section class="registry-panel registry-account-panel">
      <span class="registry-step">01</span>
      <h2>注册或登录</h2>
      <p>首次使用请注册 GitHub 账号；已有账号可直接登录。GitHub 是本站登记记录的身份凭据。</p>
      <a class="registry-account-button" href="https://github.com/login" target="_blank" rel="noopener">登录 GitHub</a>
      <a class="registry-account-button registry-account-secondary" href="https://github.com/signup" target="_blank" rel="noopener">注册 GitHub</a>
    </section>

    <section class="registry-panel registry-account-panel">
      <span class="registry-step">02</span>
      <h2>查看我的记录</h2>
      <p>登录后打开“我的记录”，GitHub 会仅列出由当前账号提交的招生登记。</p>
      <a class="registry-account-button" href="https://github.com/AdvLearnLab/AdvLearnLab.github.io/issues?q=is%3Aissue%20author%3A%40me%20in%3Abody%20%22%E8%80%83%E7%94%9F%E5%A7%93%E5%90%8D%EF%BC%9A%22" target="_blank" rel="noopener">查看我的记录</a>
    </section>

    <section class="registry-panel registry-account-panel">
      <span class="registry-step">03</span>
      <h2>修改或下架</h2>
      <p>进入记录后可编辑正文来更新年份或状态。关闭 Issue 即视为删除公开登记，系统会自动将其从列表下架。</p>
      <p class="registry-account-hint">关闭后的 GitHub 历史仍然可见；需要彻底删除时，请在该记录内留言联系仓库管理员。</p>
    </section>
  </div>
</div>
