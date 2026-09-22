---
layout: homepage
title: Students
permalink: /students.html
---

<div class="student-hero">
  <span>Mengnan Zhao Research Group</span>
  <h1>Students & Prospective Students</h1>
  <p>
    欢迎对可信机器学习、计算机视觉、隐私保护和安全方向感兴趣的同学加入。
    如希望进一步了解团队的研究方向、科研氛围与日常学习情况，欢迎联系下方在读学生交流。
  </p>
</div>

<h2 id="current-students">Current Students</h2>

<div class="student-grid">
  <article class="student-card">
    <img class="student-photo" src="{{ '/assets/img/students/xu-tong.jpg' | relative_url }}" alt="许潼">
    <div class="student-card-body">
      <h3>许潼</h3>
      <p class="student-meta">2026级 专硕</p>
      <div class="student-tags" aria-label="Student highlights">
        <span>初试 374</span>
        <span>CET-6</span>
        <span>国奖 × 2</span>
      </div>
      <div class="student-contact" aria-label="许潼微信">
        <span class="student-contact-label">微信咨询</span>
        <span class="student-contact-id">xt18325407136</span>
      </div>
    </div>
  </article>

  <article class="student-card">
    <img class="student-photo" src="{{ '/assets/img/students/xu-chao.jpg' | relative_url }}" alt="许超">
    <div class="student-card-body">
      <h3>许超</h3>
      <p class="student-meta">2026级 学硕</p>
      <div class="student-tags" aria-label="Student highlights">
        <span>初试 370</span>
        <span>CET-6</span>
      </div>
      <div class="student-contact" aria-label="许超微信">
        <span class="student-contact-label">微信咨询</span>
        <span class="student-contact-id">xxysh12581</span>
      </div>
    </div>
  </article>
</div>

<h2 id="prospective-students">Prospective Students</h2>

<div class="student-recruiting">
  <div class="recruiting-panel">
    <h3>我在找什么样的人？<span>读博意向者优先</span><span class="recruiting-tag-attitude">认真</span></h3>
    <article>
      <strong>动手能力</strong>
      <p>科研里真正的门槛不是失败，是连手都不敢伸。</p>
    </article>
    <article>
      <strong>思考方式</strong>
      <p>可以天马行空，但要有本事把缰绳拽回来，用逻辑把脑洞兜住。</p>
    </article>
    <article>
      <strong>表达能力</strong>
      <p>活儿干得漂亮是第一步，还能写清楚、讲明白。</p>
    </article>
    <article>
      <strong>精神面貌</strong>
      <p>我比较欣赏衣着干净、精神利落的同学。它并不能保证科研一定利索，但常常意味着你愿意认真对待自己、他人和手里的事。</p>
    </article>
  </div>

  <div class="recruiting-panel">
    <h3>我能给你什么样的环境？</h3>
    <article>
      <strong>效率优先，不盯坐班。</strong>
      <p>5分钟能搞定的事，别磨成1小时。省下来的55分钟，拿去运动、追剧、发呆、谈恋爱，怎么愉悦自己都行。</p>
    </article>
    <article>
      <strong>身体是科研的底牌。</strong>
      <p>希望你来的时候吃嘛嘛香，走的时候同样吃嘛嘛香。</p>
    </article>
    <article>
      <strong>你往前冲，后面的事我来兜。</strong>
      <p>推荐信我写，资源我帮着你对接，升学我尽力推。</p>
    </article>
  </div>
</div>

<section class="student-application-cta" aria-labelledby="application-heading">
  <div>
    <h3 id="application-heading">简历投来，随时开聊。</h3>
    <p>介绍一下你自己、感兴趣的方向，以及想一起探索的问题。</p>
  </div>
  <button class="application-open" id="application-open" type="button">发送简历</button>
</section>

<p class="application-status" id="application-status" role="status" hidden>简历已发送，感谢你的来信。</p>

<dialog class="application-dialog" id="application-dialog" aria-labelledby="application-dialog-title">
  <form class="application-form" id="application-form" action="https://formsubmit.co/zmn@ahu.edu.cn" method="POST" enctype="multipart/form-data">
    <input type="hidden" name="_subject" value="学生申请｜个人主页简历投递">
    <input type="hidden" name="_template" value="table">
    <input type="hidden" name="_autoresponse" value="你好！你的简历和申请信息已成功提交，我们已经收到。感谢你对团队的关注，如研究方向匹配，将尽快与你联系。请勿重复提交。——赵梦楠，安徽大学">
    <input type="hidden" name="_next" id="application-next" value="">
    <input class="application-honey" type="text" name="_honey" tabindex="-1" autocomplete="off">
    <header class="application-dialog-header">
      <div><span>Prospective Students</span><h2 id="application-dialog-title">发送简历</h2></div>
      <button class="application-close" id="application-close" type="button" aria-label="关闭申请窗口">×</button>
    </header>
    <div class="application-fields">
      <label><span>姓名</span><input type="text" name="姓名" autocomplete="name" required></label>
      <label><span>联系邮箱</span><input type="email" name="email" autocomplete="email" required></label>
      <label><span>微信号</span><input type="text" name="微信号" autocomplete="off" required></label>
      <label><span>英语水平</span><input type="text" name="英语水平" placeholder="如：CET-6 / IELTS 6.5" required></label>
      <label><span>学校</span><input type="text" name="学校" autocomplete="organization" required></label>
      <label><span>研究方向</span><input type="text" name="研究方向" placeholder="如：可信机器学习" required></label>
    </div>
    <label class="application-message">
      <span>想说的话 <small>选填</small></span>
      <textarea name="留言" rows="4" placeholder="可以简单介绍研究经历、兴趣与计划。"></textarea>
    </label>
    <label class="application-upload">
      <span>上传简历</span>
      <strong>选择 PDF 或 Word 文件</strong>
      <small>支持 .pdf、.doc、.docx，文件不超过 10 MB</small>
      <input id="application-file" type="file" name="attachment" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" required>
    </label>
    <p class="application-privacy">提交内容将通过 FormSubmit 转发至 zmn@ahu.edu.cn。</p>
    <footer class="application-actions">
      <button class="application-cancel" id="application-cancel" type="button">取消</button>
      <button class="application-send" type="submit">发送</button>
    </footer>
  </form>
</dialog>

<script>
  (function () {
    const dialog = document.getElementById('application-dialog');
    const form = document.getElementById('application-form');
    const file = document.getElementById('application-file');
    const next = document.getElementById('application-next');
    const status = document.getElementById('application-status');
    if (!dialog || !form) return;
    next.value = window.location.origin + window.location.pathname + '?submitted=1';
    document.getElementById('application-open').addEventListener('click', function () { dialog.showModal(); });
    document.getElementById('application-close').addEventListener('click', function () { dialog.close(); });
    document.getElementById('application-cancel').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (event) { if (event.target === dialog) dialog.close(); });
    file.addEventListener('change', function () {
      file.setCustomValidity(file.files[0] && file.files[0].size > 10 * 1024 * 1024 ? '简历文件不能超过 10 MB。' : '');
    });
    if (new URLSearchParams(window.location.search).get('submitted') === '1') {
      status.hidden = false;
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  })();
</script>
